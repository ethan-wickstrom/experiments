#!/usr/bin/env python3
"""Record guesses before the world answers, then score them.

The record is `bets.jsonl`, one event per line, append only: a `bet` line states a claim, a probability and what
real event decides it; a later `verdict` line records what happened. Nothing is edited, so the order of the lines
(and of the commits that added them) shows each guess was made before its answer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

RECORD = Path(__file__).with_name("bets.jsonl")


def load(path: Path, new: dict | None = None) -> tuple[dict[str, dict], dict[str, dict]]:
    """Read the record, with `new` checked as if it were its next line."""
    bets: dict[str, dict] = {}
    verdicts: dict[str, dict] = {}
    # Split on "\n" only: a pasted claim may hold other characters that str.splitlines treats as line ends.
    lines = path.read_text().split("\n") if path.exists() else []
    items = [(i, json.loads(line)) for i, line in enumerate(lines, 1) if line.strip()]
    if new is not None:
        items.append((len(lines) + 1, new))
    for n, e in items:
        if e["kind"] == "bet":
            if e["id"] in bets:
                raise ValueError(f"line {n}: bet {e['id']} is already recorded")
            if not 0 < e["p"] < 1:
                raise ValueError(f"line {n}: p must be strictly between 0 and 1")
            bets[e["id"]] = e
        elif e["kind"] == "verdict":
            if e["id"] not in bets:
                raise ValueError(f"line {n}: verdict for unknown bet {e['id']}")
            if e["id"] in verdicts:
                raise ValueError(f"line {n}: bet {e['id']} already has a verdict")
            verdicts[e["id"]] = e
        else:
            raise ValueError(f"line {n}: unknown kind {e['kind']!r}")
    return bets, verdicts


def append(path: Path, event: dict) -> None:
    prefix = "\n" if path.exists() and path.stat().st_size > 0 and not path.read_text().endswith("\n") else ""
    with path.open("a") as f:
        f.write(prefix + json.dumps(event, ensure_ascii=False) + "\n")


def score(bets: dict[str, dict], verdicts: dict[str, dict], today: str) -> str:
    done = [(bets[i]["p"], 1.0 if v["happened"] else 0.0) for i, v in verdicts.items()]
    out = [f"{len(bets)} bets, {len(done)} with a verdict."]
    if done:
        brier = sum((p - y) ** 2 for p, y in done) / len(done)
        out.append(f"Brier score {brier:.3f} (0 is perfect; always saying 50% scores 0.250).")
        out.append("said     n  happened")
        for k in range(5):  # five bins by percentage points; each probability falls in exactly one
            ys = [y for p, y in done if min(int(round(p * 100, 6)) // 20, 4) == k]
            if ys:
                out.append(f"{k * 20}%-{k * 20 + 20}%".ljust(8) + f"{len(ys):>2}  {sum(ys) / len(ys):.0%}")
    late = sorted((b["due"], i) for i, b in bets.items() if i not in verdicts and b["due"] < today)
    out += [f"overdue: {i} (due {due})" for due, i in late]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", type=Path, default=RECORD)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bet", help="record a guess")
    b.add_argument("id")
    b.add_argument("p", type=float, help="probability the claim is true")
    b.add_argument("due", help="YYYY-MM-DD by which the world will have answered")
    b.add_argument("claim")
    b.add_argument("--decided-by", required=True, help="the real event that settles it")
    v = sub.add_parser("verdict", help="record what happened")
    v.add_argument("id")
    v.add_argument("happened", choices=["yes", "no"])
    v.add_argument("--evidence", required=True)
    sub.add_parser("score", help="how good the guesses have been")
    a = ap.parse_args(argv)
    today = dt.date.today().isoformat()
    if a.cmd == "bet":
        due = dt.date.fromisoformat(a.due).isoformat()
        event = {"kind": "bet", "id": a.id, "made": today, "p": a.p, "due": due, "claim": a.claim, "decided_by": a.decided_by}
    elif a.cmd == "verdict":
        event = {"kind": "verdict", "id": a.id, "on": today, "happened": a.happened == "yes", "evidence": a.evidence}
    else:
        print(score(*load(a.record), today))
        return 0
    try:
        load(a.record, event)
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1
    append(a.record, event)
    return 0


if __name__ == "__main__":
    sys.exit(main())
