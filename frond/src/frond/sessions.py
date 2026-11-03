"""Saving conversations per workspace so ``frond --continue`` can pick one up again.

A session file holds the conversation (the user's messages, frond's replies, and what each turn changed),
not the REPL's memory: variables do not survive a restart, but the agent knows what happened before.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

from frond.agent.session import TurnRecord
from frond.world import Store


def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "frond"


class SessionStore:
    def __init__(self, workspace_root: Path, base: Path | None = None) -> None:
        digest = hashlib.sha256(str(workspace_root).encode()).hexdigest()[:16]
        self.root = workspace_root
        self.directory = (base or data_home()) / "sessions" / f"{workspace_root.name}-{digest}"

    def new_path(self) -> Path:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        return self.directory / f"{stamp}-{os.getpid()}.json"

    @staticmethod
    def steps_path(session_file: Path) -> Path:
        """Where the session's step log lives: every message, step and answer, one JSON line each."""
        return session_file.with_name(session_file.stem + ".steps.jsonl")

    def world_roots(self, *, max_age_days: float = 30.0) -> set[str]:
        """The worlds this workspace's recent sessions name: their turns' and their steps' (ledger G21). Sessions
        untouched for longer than ``max_age_days`` no longer hold theirs, so their undo history may be collected."""
        cutoff = time.time() - max_age_days * 86400
        roots: set[str] = set()
        if not self.directory.is_dir():
            return roots
        for path in self.directory.iterdir():
            try:
                if path.stat().st_mtime < cutoff:
                    continue
                if path.name.endswith(".steps.jsonl"):
                    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                        with contextlib.suppress(ValueError, AttributeError):
                            roots.add(json.loads(line).get("world") or "")
                elif path.suffix == ".json":
                    for turn in json.loads(path.read_text(encoding="utf-8")).get("turns", []):
                        roots.update((turn.get("world_before") or "", turn.get("world_after") or ""))
            except (OSError, ValueError):
                continue
        roots.discard("")
        return roots

    def collect(self, store: Store, *, bound: int = 2 * 1024**3, grace: float = 3600.0) -> int:
        """Past ``bound`` bytes, delete the store's objects that no recent session reaches and that have not been
        used for ``grace`` seconds (objects a running session is still writing are newer); bytes freed."""
        if store.size() <= bound:
            return 0
        return store.sweep(store.reachable(self.world_roots()), older_than=time.time() - grace)

    def latest(self) -> Path | None:
        if not self.directory.is_dir():
            return None
        files = sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime)
        return files[-1] if files else None

    def load(self, path: Path) -> list[TurnRecord]:
        data = json.loads(path.read_text(encoding="utf-8"))
        fields = {f.name for f in dataclasses.fields(TurnRecord)}
        return [TurnRecord(**{k: v for k, v in turn.items() if k in fields}) for turn in data.get("turns", [])]

    def save(self, path: Path, records: list[TurnRecord], model: str) -> None:
        payload = {
            "workspace": str(self.root),
            "model": model,
            "saved": dt.datetime.now().isoformat(timespec="seconds"),
            "turns": [dataclasses.asdict(r) for r in records],
        }
        # Conversations can contain code and secrets, so the folder and every file are private from the start.
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.fchmod(fd, 0o600)  # a leftover .tmp from an older save keeps its mode otherwise
            f.write(json.dumps(payload, indent=1))
        os.replace(tmp, path)
