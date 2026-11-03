"""Git's own state around FORK (ledger F26): what worlds leave out, since they exclude ``.git``.

A branch that commits, checks out or stages changes moves HEAD, refs and the index, and the resets between branches
restore only the working tree. So FORK captures git's state when it starts, puts it back before each branch, and at
the end puts back the kept branch's (or the start's). Objects are not touched: they are added, never changed, so a
commit a branch made stays reachable only if its branch is kept, and is otherwise left for git's garbage collection.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Files and directories directly under .git that hold where HEAD points, what is staged, and operations in progress.
STATE = (
    "HEAD",
    "ORIG_HEAD",
    "FETCH_HEAD",
    "MERGE_HEAD",
    "MERGE_MSG",
    "MERGE_MODE",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "index",
    "packed-refs",
    "refs",
    "rebase-merge",
    "rebase-apply",
    "sequencer",
)


@dataclass(frozen=True)
class GitState:
    """The bytes of every state file, by path relative to the git directory."""

    files: dict[str, bytes] = field(default_factory=dict)


def git_dir(root: Path | None) -> Path | None:
    """The git directory of a work tree rooted at ``root``: ``.git``, or where a ``.git`` file (a linked worktree or
    a submodule) points."""
    if root is None:
        return None
    dot = root / ".git"
    if dot.is_dir():
        return dot
    if dot.is_file():
        text = dot.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("gitdir:"):
            target = Path(text[len("gitdir:") :].strip())
            target = target if target.is_absolute() else (root / target)
            return target.resolve() if target.is_dir() else None
    return None


def capture(directory: Path) -> GitState:
    files: dict[str, bytes] = {}
    for name in STATE:
        path = directory / name
        if path.is_file():
            files[name] = path.read_bytes()
        elif path.is_dir():
            for parent, _, names in os.walk(path):
                for leaf in names:
                    full = Path(parent) / leaf
                    files[full.relative_to(directory).as_posix()] = full.read_bytes()
    return GitState(files)


def restore(directory: Path, state: GitState) -> None:
    """Make git's state files exactly ``state``: write each, and remove the ones it does not have."""
    for name in STATE:
        path = directory / name
        if path.is_dir():
            for parent, _, names in os.walk(path, topdown=False):
                for leaf in names:
                    full = Path(parent) / leaf
                    if full.relative_to(directory).as_posix() not in state.files:
                        full.unlink()
            if name != "refs" and not any(path.rglob("*")) and not any(k.startswith(f"{name}/") for k in state.files):
                shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and name not in state.files:
            path.unlink()
    for rel, data in state.files.items():
        path = directory / rel
        if path.is_file() and path.read_bytes() == data:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.frond-tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
