"""Unified diffs for the edits the agent makes, so the user always sees exactly what changed."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

MAX_DIFF_LINES = 20_000


@dataclass(frozen=True, slots=True)
class Diff:
    text: str
    added: int
    removed: int


def make_diff(old: str, new: str, path: str, *, context: int = 3, created: bool = False, deleted: bool = False) -> Diff:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    if len(old_lines) > MAX_DIFF_LINES or len(new_lines) > MAX_DIFF_LINES:
        return Diff(f"(diff omitted: {len(old_lines):,} → {len(new_lines):,} lines)", len(new_lines), len(old_lines))
    lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="/dev/null" if created else f"a/{path}",
            tofile="/dev/null" if deleted else f"b/{path}",
            n=context,
            lineterm="",
        )
    )
    added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))
    return Diff("\n".join(lines), added, removed)
