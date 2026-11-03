"""The conversation's lossless record: every user message, every REPL step and every answer, in order.

A long turn folds its early steps out of the prompt to stay within the context window, and the prompt shows only
the tail of earlier turns. Neither step loses anything: the record keeps each step's reasoning, code and full
output under a sequence number, and the agent reads it back with ``history_search`` and ``history_step``. This
follows Scroll ("Context as an Environment", arXiv 2608.21690), where an append-only event log the model queries
from its REPL beat summarised history by a wide margin (73.1% vs 19.9% on BEAM-10M), and replaces summaries,
which drop the user's constraints (arXiv 2610.31778), mix the summariser's guesses in with facts (arXiv
2610.20927), and can launder instructions planted in tool output into apparent user turns (arXiv 2610.29869).

Search is BM25 over identifiers and words. The record is appended to a JSONL file beside the session file, so
``--continue`` brings it back.
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal

Kind = Literal["user", "step", "answer"]
MAX_STORED_OUTPUT = 200_000
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")
_K1, _B = 1.2, 0.75


def tokens(text: str) -> list[str]:
    out: list[str] = []
    for word in _TOKEN.findall(text):
        lower = word.lower()
        out.append(lower)
        parts = [p for p in re.split(r"_+|(?<=[a-z])(?=[A-Z])", word) if p]
        if len(parts) > 1:  # snake_case and camelCase also match their parts
            out.extend(p.lower() for p in parts)
    return out


def headline(text: str, limit: int = 140) -> str:
    """The first non-empty line, shortened: how a step is named in indexes and search results."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line if len(line) <= limit else line[: limit - 1] + "…"
    return ""


@dataclass(frozen=True, slots=True)
class Record:
    seq: int
    kind: Kind
    turn: int
    step: int = 0  # the step within its turn (0 for messages and answers)
    scope: str = ""  # "" for the main agent, "sub3" for a sub-agent's steps
    reasoning: str = ""
    code: str = ""
    output: str = ""  # the REPL output, the user's message, or the answer
    error: bool = False

    @property
    def headline(self) -> str:
        return headline(self.reasoning or self.output)

    def text(self) -> str:
        return "\n".join(part for part in (self.reasoning, self.code, self.output) if part)

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        if not self.scope:
            data.pop("scope")
        if not data["error"]:
            data.pop("error")
        return data


class StepLog:
    def __init__(self, path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._records: list[Record] = []
        self._postings: dict[str, dict[int, int]] = {}  # term -> {index: count}
        self._lengths: list[int] = []
        self.path: Path | None = None
        if path is not None:
            self.attach(path)

    # ── writing ──────────────────────────────────────────────────────────────

    def attach(self, path: Path) -> None:
        """Keep the record in ``path`` from now on, first loading whatever an earlier session left there."""
        with self._lock:
            pending = self._records  # normally empty: the file is attached before the first turn
            self._records, self._postings, self._lengths = [], {}, []
            self.path = path
            if path.exists():
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    try:
                        self._index(Record(**json.loads(line)))
                    except (ValueError, TypeError):
                        continue  # a line cut short by a crash
            for record in pending:
                self._write(self._index(record))

    def add(
        self,
        kind: Kind,
        *,
        turn: int,
        step: int = 0,
        scope: str = "",
        reasoning: str = "",
        code: str = "",
        output: str = "",
        error: bool = False,
    ) -> int:
        if len(output) > MAX_STORED_OUTPUT:
            output = output[:MAX_STORED_OUTPUT] + f"\n… [{len(output) - MAX_STORED_OUTPUT:,} more chars not kept]"
        with self._lock:
            seq = len(self._records) + 1
            record = self._index(Record(seq, kind, turn, step, scope, reasoning, code, output, error))
            self._write(record)
            return record.seq

    def _index(self, record: Record) -> Record:
        if record.seq != len(self._records) + 1:  # keep seq == position + 1, even after a damaged line
            record = replace(record, seq=len(self._records) + 1)
        position = len(self._records)
        self._records.append(record)
        counts = Counter(tokens(record.text()))
        self._lengths.append(sum(counts.values()))
        for term, count in counts.items():
            self._postings.setdefault(term, {})[position] = count
        return record

    def _write(self, record: Record) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    # ── reading ──────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._records)

    @property
    def last_seq(self) -> int:
        return len(self._records)

    def get(self, seq: int) -> Record | None:
        with self._lock:
            return self._records[seq - 1] if 1 <= seq <= len(self._records) else None

    def records(self, *, turn: int | None = None) -> list[Record]:
        with self._lock:
            return [r for r in self._records if turn is None or r.turn == turn]

    def search(self, query: str, k: int = 8) -> list[dict[str, Any]]:
        terms = list(dict.fromkeys(tokens(query)))
        with self._lock:
            n = len(self._records)
            if not n or not terms:
                return []
            average = sum(self._lengths) / n or 1.0
            scores: dict[int, float] = {}
            for term in terms:
                postings = self._postings.get(term, {})
                if not postings:
                    continue
                idf = math.log(1 + (n - len(postings) + 0.5) / (len(postings) + 0.5))
                for position, count in postings.items():
                    norm = count + _K1 * (1 - _B + _B * self._lengths[position] / average)
                    scores[position] = scores.get(position, 0.0) + idf * count * (_K1 + 1) / norm
            best = sorted(scores, key=lambda p: (-scores[p], -p))[: max(1, k)]
            return [self._hit(self._records[p], terms, scores[p]) for p in best]

    @staticmethod
    def _hit(record: Record, terms: list[str], score: float) -> dict[str, Any]:
        wanted = set(terms)
        # what happened (the output) before what was said about it: ties go to the earlier line
        text = "\n".join((record.output, record.reasoning, record.code))
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        match = max(lines, key=lambda line: len(wanted & set(tokens(line))), default="")
        hit = {"seq": record.seq, "kind": record.kind, "turn": record.turn}
        if record.step:
            hit["step"] = record.step
        if record.scope:
            hit["scope"] = record.scope
        hit["headline"] = record.headline
        hit["match"] = match if len(match) <= 200 else match[:199] + "…"
        hit["score"] = round(score, 2)
        return hit
