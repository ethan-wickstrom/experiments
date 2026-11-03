"""Git's own state around FORK (ledger F26): what worlds leave out, since they exclude ``.git``.

A branch that commits, checks out or stages changes moves HEAD, refs and the index, and the resets between branches
restore only the working tree. So FORK captures git's state when it starts, puts it back before each branch, and at
the end puts back the kept branch's (or the start's). Objects are not touched: they are added, never changed, so a
commit a branch made stays reachable only if its branch is kept, and is otherwise left for git's garbage collection.

In a linked worktree HEAD, the index and operations in progress are the worktree's own, but branch refs are shared
with the repository's common directory (``commondir``), so both are captured (F62). Symbolic links under them are
neither followed nor written through.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Under the worktree's own git directory: where HEAD points, what is staged, and operations in progress.
PRIVATE = (
    "HEAD",
    "ORIG_HEAD",
    "FETCH_HEAD",
    "MERGE_HEAD",
    "MERGE_MSG",
    "MERGE_MODE",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "index",
    "rebase-merge",
    "rebase-apply",
    "sequencer",
    "refs",  # a linked worktree's own refs (refs/bisect, refs/worktree); every ref in a plain repository
)
SHARED = ("packed-refs", "refs")  # under the common directory: branches and tags
KEEP_DIRS = frozenset({"refs", "refs/heads", "refs/tags"})  # git expects these to exist


@dataclass(frozen=True)
class GitState:
    """The bytes of every state file, by directory ("private", "common") and path relative to it."""

    files: dict[tuple[str, str], bytes] = field(default_factory=dict)


@dataclass(frozen=True)
class GitDirs:
    private: Path
    common: Path  # the same as private outside a linked worktree


def git_dir(root: Path | None) -> GitDirs | None:
    """The git directories of a work tree rooted at ``root``: ``.git``, or where a ``.git`` file (a linked worktree
    or a submodule) points, and the common directory its ``commondir`` names."""
    if root is None:
        return None
    dot = root / ".git"
    private: Path | None = None
    if dot.is_dir() and not dot.is_symlink():
        private = dot
    elif dot.is_file():
        text = dot.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("gitdir:"):
            target = Path(text[len("gitdir:") :].strip())
            target = target if target.is_absolute() else (root / target)
            private = target.resolve() if target.is_dir() else None
    if private is None:
        return None
    common = private
    pointer = private / "commondir"
    if pointer.is_file():
        named = Path(pointer.read_text(encoding="utf-8", errors="replace").strip())
        candidate = (named if named.is_absolute() else private / named).resolve()
        if candidate.is_dir():
            common = candidate
    return GitDirs(private, common)


def _roots(dirs: GitDirs) -> list[tuple[str, Path, tuple[str, ...]]]:
    if dirs.common == dirs.private:
        return [("private", dirs.private, (*PRIVATE, "packed-refs"))]
    return [("private", dirs.private, PRIVATE), ("common", dirs.common, SHARED)]


def capture(dirs: GitDirs) -> GitState:
    files: dict[tuple[str, str], bytes] = {}
    for label, directory, names in _roots(dirs):
        for name in names:
            path = directory / name
            if path.is_symlink():
                continue
            if path.is_file():
                files[label, name] = path.read_bytes()
            elif path.is_dir():
                for parent, _, leaves in os.walk(path):  # does not follow links to directories
                    for leaf in leaves:
                        full = Path(parent) / leaf
                        if not full.is_symlink() and full.is_file():
                            files[label, full.relative_to(directory).as_posix()] = full.read_bytes()
    return GitState(files)


def restore(dirs: GitDirs, state: GitState) -> None:
    """Make git's state files exactly ``state``: remove the ones it does not have, with directories they leave
    empty (which would block writing a ref of the same name, F65), then write each that differs."""
    for label, directory, names in _roots(dirs):
        for name in names:
            path = directory / name
            if path.is_symlink() or (path.is_file() and (label, name) not in state.files):
                path.unlink()
            elif path.is_dir():
                for parent, subdirs, leaves in os.walk(path, topdown=False):
                    for leaf in leaves:
                        full = Path(parent) / leaf
                        if full.is_symlink() or (label, full.relative_to(directory).as_posix()) not in state.files:
                            full.unlink()
                    for sub in subdirs:
                        full = Path(parent) / sub
                        rel = full.relative_to(directory).as_posix()
                        if full.is_symlink():
                            full.unlink()
                        elif rel not in KEEP_DIRS and not any(full.iterdir()):
                            full.rmdir()
                if name not in KEEP_DIRS and not any(path.iterdir()):
                    path.rmdir()
        for (where, rel), data in state.files.items():
            if where != label:
                continue
            path = directory / rel
            if path.is_file() and not path.is_symlink() and path.read_bytes() == data:
                continue
            for parent in reversed(path.relative_to(directory).parents[:-1]):  # no link on the way: never write out
                if (directory / parent).is_symlink():
                    (directory / parent).unlink()
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)  # emptied above: a directory where the ref file belongs
            tmp = path.with_name(f".{path.name}.frond-tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
