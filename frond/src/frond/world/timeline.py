"""A session's workspace over time: a world after every step, a net change per turn, and undo as a revert (D22).

frond snapshots the workspace when a turn starts and after each of its steps; only files whose stat changed are read
again (``Worktree.snapshot``). Whatever changed the directory in between, frond's file tools, a shell command, a
background job or a formatter, shows up in the difference. So no tool keeps an undo journal, and undo works in any
directory, with or without git. Undo is a revert (``merge.revert``): the turn's changes go back, and changes made
since by anyone else stay, merged line by line where both touched the same file.

In a git work tree, untracked paths git ignores are left out, as ``git status`` leaves them out, so a build's
``target/`` is never hashed. Within a turn that set only takes in paths that did not exist before, so editing
``.gitignore`` never makes an existing directory look deleted or created. A turn that moved HEAD (a commit, a
checkout) is not undone file by file, which would contradict the commit; git undoes it.
"""

from __future__ import annotations

import contextlib
import subprocess
import threading
import time
from pathlib import Path

from frond.world.merge import Revert, revert
from frond.world.store import Change, Entry, Store, TooLarge, Worktree

MAX_BLOB = 16 * 1024 * 1024  # larger files are tracked by a stat signature: undo reports them, cannot restore them
MAX_FILES = 200_000  # a workspace past this is not snapshotted at all: undo is off, and says why
SLOW_SECONDS = 2.0  # a snapshot slower than this turns off per-command diffs, which take two snapshots a command


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            ["git", "-c", "core.fsmonitor=false", *args],
            cwd=root,
            capture_output=True,
            timeout=30,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def in_git(root: Path) -> bool:
    result = _git(root, "rev-parse", "--is-inside-work-tree")
    return result is not None and result.returncode == 0 and result.stdout.strip() == b"true"


def git_ignored(root: Path) -> frozenset[str]:
    """Untracked paths git ignores under ``root``, relative to it (``dir/`` for a whole directory)."""
    result = _git(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory")
    if result is None or result.returncode != 0:
        return frozenset()
    return frozenset(p.decode(errors="surrogateescape") for p in result.stdout.split(b"\0") if p)


def git_head(root: Path) -> str:
    """The checked-out commit and branch ("" outside git)."""
    result = _git(root, "rev-parse", "-q", "HEAD", "--symbolic-full-name", "HEAD")
    return result.stdout.decode(errors="replace") if result is not None and result.returncode == 0 else ""


class Timeline:
    def __init__(self, root: Path, store_dir: Path, *, max_blob: int = MAX_BLOB, max_files: int = MAX_FILES) -> None:
        self.root = root
        self.store = Store(store_dir)
        self.work = Worktree(self.store, root, max_blob=max_blob, max_files=max_files)
        self.git = in_git(root)
        self.enabled = True
        self.reason = ""  # why snapshots are off
        self.command_diffs = True  # off once a snapshot is slow: they would slow every command
        self.last_seconds = 0.0
        self.last: str | None = None  # the latest snapshot
        self._lock = threading.RLock()

    def warm(self) -> None:
        """Take a first snapshot in the background, so the first turn does not wait for every file to be read."""

        def first() -> None:
            with contextlib.suppress(OSError):  # best effort: the session may close, and its store go, meanwhile
                self.snapshot()

        threading.Thread(target=first, name="frond-world-warmup", daemon=True).start()

    def snapshot(self, *, new_ignored: bool = False) -> str:
        """The workspace now, as a tree id. ``new_ignored``: first leave out paths git began ignoring that did not
        exist at the previous snapshot (a build's output directory, say)."""
        with self._lock:
            if not self.enabled:
                return ""
            started = time.monotonic()
            if new_ignored and self.git:
                fresh = git_ignored(self.root) - self.work.ignored
                if self.last is not None:
                    fresh = frozenset(p for p in fresh if self.lookup(self.last, p.rstrip("/")) is None)
                self.work.ignored |= fresh
            try:
                self.last = self.work.snapshot()
            except TooLarge as exc:
                self.enabled, self.reason, self.last = False, str(exc), None
                return ""
            self.last_seconds = time.monotonic() - started
            if self.last_seconds > SLOW_SECONDS:
                self.command_diffs = False
            return self.last

    def begin_turn(self) -> tuple[str, str]:
        """The world a turn starts from ("" when snapshots are off), and git's HEAD then. The ignored set restarts
        from git's current one."""
        with self._lock:
            if not self.enabled:
                return "", ""
            self.work.ignored = git_ignored(self.root) if self.git else frozenset()
            return self.snapshot(), self.head()

    def head(self) -> str:
        return git_head(self.root) if self.git else ""

    def lookup(self, tree: str, path: str) -> Entry | None:
        entry: Entry | None = Entry("tree", tree)
        for part in path.split("/"):
            if entry is None or entry.kind != "tree":
                return None
            entry = self.store.tree(entry.oid).get(part)
        return entry

    def diff(self, before: str, after: str) -> list[Change]:
        return self.store.diff(before, after)

    def content(self, entry: Entry | None) -> bytes | None:
        """A file's bytes (a link's target), or None for absent paths, directories and files too large to keep."""
        return self.work.read("", entry)

    def revert(self, before: str, after: str) -> Revert:
        """Undo the change from world ``before`` to world ``after`` in the directory as it is now."""
        with self._lock:
            result = revert(self.work, before, after)
            self.last = self.work.snapshot()
            return result
