"""Per-turn checkpoints of the files the agent changes, so ``/undo`` can put them back exactly.

Every change the agent makes goes through its tools, so the tools record a file's original bytes the first
time a turn touches it (or that it did not exist). Undo restores those bytes, deletes files the turn created,
and reverses directory moves. Changes made by shell commands (formatters, codemods) are not tracked.
"""

from __future__ import annotations

import contextlib
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path

MAX_DIR_SNAPSHOT_BYTES = 50_000_000


@dataclass
class Checkpoint:
    turn: int
    files: dict[Path, bytes | None] = field(default_factory=dict)  # original bytes; None = did not exist
    moves: list[tuple[Path, Path]] = field(default_factory=list)  # (src, dst) directory moves, in order
    created_dirs: list[Path] = field(default_factory=list)  # directories that did not exist before the turn
    lost: list[str] = field(default_factory=list)  # changes too large to snapshot

    def __bool__(self) -> bool:
        return bool(self.files or self.moves or self.lost)


@dataclass(frozen=True, slots=True)
class Restored:
    path: Path
    before: bytes | None  # content just before the undo (None: absent)
    after: bytes | None  # content after the undo (None: removed)


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
            if cp is None or path in cp.files:
                return
            try:
                cp.files[path] = path.read_bytes() if path.is_file() else None
            except OSError:
                cp.files[path] = None
            if cp.files[path] is None:
                parent = path.parent
                while not parent.exists() and parent not in cp.created_dirs:
                    cp.created_dirs.append(parent)
                    parent = parent.parent

    def record_tree(self, root: Path) -> None:
        """Remember every file under ``root`` before the directory is deleted."""
        files = [p for p in root.rglob("*") if p.is_file()]
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
                self._current.moves.append((src, dst))

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
        restored: list[Restored] = []
        for src, dst in reversed(cp.moves):
            if dst.exists() and not src.exists():
                src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dst), str(src))
        for path, original in cp.files.items():
            try:
                before = path.read_bytes() if path.is_file() else None
            except OSError:
                before = None
            if original is None:
                if path.is_file():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
            if before != original:
                restored.append(Restored(path, before, original))
        # Remove directories the turn created, deepest first, but only if they are empty again.
        for d in sorted(cp.created_dirs, key=lambda p: len(p.parts), reverse=True):
            with contextlib.suppress(OSError):
                d.rmdir()
        return cp, restored
