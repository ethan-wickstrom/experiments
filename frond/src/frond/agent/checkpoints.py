"""Per-turn checkpoints of the files the agent changes, so ``/undo`` can put them back exactly.

Every change the agent makes goes through its tools, so the tools record what they are about to change: a
file's original bytes the first time a turn touches it (or that it did not exist yet), a directory move, or a
deleted symbolic link. The records form an ordered journal that undo replays backwards, so a sequence such as
"move a/ to b/, then edit b/x.py" unwinds correctly. Changes made by shell commands are not tracked.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

MAX_DIR_SNAPSHOT_BYTES = 50_000_000


@dataclass(frozen=True, slots=True)
class Entry:
    kind: Literal["file", "move", "link"]
    path: Path  # the file, the move's source, or the link
    original: bytes | None = None  # "file": content before the turn touched it (None: it did not exist)
    other: Path | None = None  # "move": destination
    target: str | None = None  # "link": where the deleted link pointed


@dataclass
class Checkpoint:
    turn: int
    journal: list[Entry] = field(default_factory=list)
    seen: set[Path] = field(default_factory=set)
    created_dirs: list[Path] = field(default_factory=list)  # directories that did not exist before the turn
    lost: list[str] = field(default_factory=list)  # changes too large to snapshot

    def __bool__(self) -> bool:
        return bool(self.journal or self.lost)


@dataclass(frozen=True, slots=True)
class Restored:
    path: Path
    before: bytes | None  # content just before the undo (None: absent)
    after: bytes | None  # content after the undo (None: removed)
    moved_from: Path | None = None  # set when the undo moved ``path`` back from here


class Checkpoints:
    def __init__(self) -> None:
        self._stack: list[Checkpoint] = []
        self._current: Checkpoint | None = None
        self._lock = threading.Lock()

    def begin(self, turn: int) -> None:
        with self._lock:
            self._current = Checkpoint(turn)
            self._stack.append(self._current)

    def record(self, path: Path) -> None:
        """Remember ``path``'s content before its first change in the current turn."""
        with self._lock:
            cp = self._current
            if cp is None or path in cp.seen:
                return
            cp.seen.add(path)
            try:
                original = path.read_bytes() if path.is_file() else None
            except OSError:
                original = None
            cp.journal.append(Entry("file", path, original))
            if original is None:
                parent = path.parent
                while not parent.exists() and parent not in cp.created_dirs:
                    cp.created_dirs.append(parent)
                    parent = parent.parent

    def record_tree(self, root: Path) -> None:
        """Remember every file under ``root`` before the directory is deleted."""
        files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
        if sum(p.stat().st_size for p in files) > MAX_DIR_SNAPSHOT_BYTES:
            with self._lock:
                if self._current is not None:
                    self._current.lost.append(f"{root} (too large to snapshot)")
            return
        for p in files:
            self.record(p)

    def record_move(self, src: Path, dst: Path) -> None:
        with self._lock:
            if self._current is not None:
                self._current.journal.append(Entry("move", src, other=dst))

    def record_link(self, link: Path, target: str) -> None:
        with self._lock:
            if self._current is not None:
                self._current.journal.append(Entry("link", link, target=target))

    def can_undo(self) -> bool:
        with self._lock:
            return any(self._stack)

    def undo(self) -> tuple[Checkpoint, list[Restored]] | None:
        """Restore the most recent turn that changed anything. Returns what was restored."""
        with self._lock:
            while self._stack and not self._stack[-1]:
                self._stack.pop()
            if not self._stack:
                return None
            cp = self._stack.pop()
            if cp is self._current:
                self._current = None
        before: dict[Path, bytes | None] = {}
        moves: list[Restored] = []
        for entry in reversed(cp.journal):
            if entry.kind == "move":
                assert entry.other is not None
                if entry.other.exists() and not entry.path.exists():
                    entry.path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(entry.other), str(entry.path))
                    moves.append(Restored(entry.path, None, None, moved_from=entry.other))
            elif entry.kind == "link":
                if not entry.path.exists() and not entry.path.is_symlink() and entry.target is not None:
                    entry.path.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(entry.target, entry.path)
            else:
                path = entry.path
                if path not in before:
                    try:
                        before[path] = path.read_bytes() if path.is_file() else None
                    except OSError:
                        before[path] = None
                if entry.original is None:
                    if path.is_file():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(entry.original)
        # Remove directories the turn created, deepest first, but only if they are empty again.
        for d in sorted(cp.created_dirs, key=lambda p: len(p.parts), reverse=True):
            with contextlib.suppress(OSError):
                d.rmdir()
        restored = list(moves)
        carried = [m.moved_from for m in moves if m.moved_from is not None]
        for path, old in before.items():
            try:
                now = path.read_bytes() if path.is_file() else None
            except OSError:
                now = None
            if now is None and any(path == d or d in path.parents for d in carried):
                continue  # it went back with its directory; the move is reported instead
            if now != old:
                restored.append(Restored(path, old, now))
        return cp, restored
