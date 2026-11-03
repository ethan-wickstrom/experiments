"""What a shell command changed in a git workspace, so ``/undo`` can put it back and the user can see it.

frond's own tools journal their edits before making them, but a formatter, a code generator or ``sed -i`` run
through ``sh()`` changes files behind their back. Around each such command this module snapshots the workspace as
a git tree, then diffs the two trees. Every changed path's earlier bytes and mode go into the turn's undo journal,
and a diff is shown for it. Changes to files git ignores (build output, caches) are not tracked.

The user's repository is never written to. Snapshots go through a private index (seeded from the real one, so
only files whose stat data changed are hashed again) and a private object directory, with the repository's own
objects as an alternate, so no objects or refs appear in ``.git``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

SLOW_SNAPSHOT_SECONDS = 2.0  # past this, snapshots are switched off for the session: they would slow every command


@dataclass(frozen=True, slots=True)
class Change:
    path: Path
    status: str  # "A" added, "M" modified (content or mode), "D" deleted, "T" type changed
    before: bytes | None  # content before the command (a symlink's target for links); None when added
    mode: str  # the git mode before: "100644", "100755", "120000" (symlink); "" when added
    new_mode: str  # the git mode after; "" when deleted


class GitSnapshots:
    def __init__(self, root: Path, scratch: Path) -> None:
        self.root = root
        self.enabled = False
        self.reason = ""
        self._lock = threading.Lock()
        try:
            top = self._git("rev-parse", "--show-toplevel", env=os.environ.copy()).decode().strip()
            git_dir = self._git("rev-parse", "--absolute-git-dir", env=os.environ.copy()).decode().strip()
            objects = self._git("rev-parse", "--git-path", "objects", env=os.environ.copy()).decode().strip()
        except (OSError, subprocess.CalledProcessError):
            self.reason = "not a git repository"
            return
        self.top = Path(top)
        self.pathspec = os.path.relpath(root, self.top)
        scratch.mkdir(parents=True, exist_ok=True)
        self.index = scratch / "index"
        self.objects = scratch / "objects"
        self.objects.mkdir(exist_ok=True)
        real_index = Path(git_dir) / "index"
        if real_index.exists():
            shutil.copyfile(real_index, self.index)  # its stat cache spares re-hashing unchanged files
        objects_dir = Path(objects) if os.path.isabs(objects) else self.top / objects
        self.env = {
            **os.environ,
            "GIT_INDEX_FILE": str(self.index),
            "GIT_OBJECT_DIRECTORY": str(self.objects),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(objects_dir),
            "GIT_OPTIONAL_LOCKS": "0",
        }
        self.enabled = True

    def _git(self, *args: str, env: dict[str, str], cwd: Path | None = None) -> bytes:
        return subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", *args],
            cwd=cwd or self.root,
            env=env,
            capture_output=True,
            check=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        ).stdout

    def take(self) -> str | None:
        """The workspace's current state as a tree id (None when snapshots are off)."""
        if not self.enabled:
            return None
        with self._lock:
            started = time.monotonic()
            try:
                self._git("add", "-A", "--", self.pathspec, env=self.env, cwd=self.top)
                tree = self._git("write-tree", env=self.env, cwd=self.top).decode().strip()
            except (OSError, subprocess.SubprocessError) as exc:
                self.enabled, self.reason = False, f"git snapshot failed: {exc}"
                return None
            if time.monotonic() - started > SLOW_SNAPSHOT_SECONDS:
                self.enabled = False
                self.reason = f"snapshots took over {SLOW_SNAPSHOT_SECONDS:.0f}s in this repository"
            return tree

    def changes(self, before: str, after: str) -> list[Change]:
        """Paths whose content, mode or type differ between two snapshots, with what they held before."""
        if before == after:
            return []
        with self._lock:
            raw = self._git("diff-tree", "-r", "-z", "--no-renames", "--raw", before, after, env=self.env, cwd=self.top)
            out: list[Change] = []
            fields = raw.split(b"\0")
            i = 0
            while i + 1 < len(fields):
                meta, name = fields[i].decode(), fields[i + 1].decode(errors="surrogateescape")
                i += 2
                if not meta.startswith(":"):
                    continue
                old_mode, new_mode, old_blob, _new_blob, status = meta[1:].split(" ")
                path = self.top / name
                new_mode = "" if new_mode == "000000" else new_mode
                if status.startswith("A"):
                    out.append(Change(path, "A", None, "", new_mode))
                    continue
                content = self._git("cat-file", "blob", old_blob, env=self.env, cwd=self.top)
                out.append(Change(path, status[0], content, old_mode, new_mode))
            return out

    def head(self) -> str:
        """The checked-out commit (and branch), to notice commands that move it."""
        if not self.enabled:
            return ""
        try:
            return self._git("rev-parse", "-q", "HEAD", "--symbolic-full-name", "HEAD", env=self.env).decode()
        except (OSError, subprocess.SubprocessError):
            return ""
