#!/usr/bin/env python3
"""Stop hook: a turn ends only when the work is committed, pushed and on origin/main (decisions D18, D19).

State that lives only in a session's VM is lost when the VM is reclaimed, and a new session starts from a fresh
clone of the default branch. When the tree is dirty or HEAD is not on origin/main, this blocks the stop once and
says what is missing. ``stop_hook_active`` marks the stop that follows such a block: it is let through, so a check
that cannot be satisfied (no network, say) never traps the session in a loop.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def git(root: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30, check=False)


def problems(root: str) -> list[str]:
    found: list[str] = []
    status = git(root, "status", "--porcelain").stdout.strip()
    if status:
        lines = status.splitlines()
        more = f"\n… and {len(lines) - 12} more" if len(lines) > 12 else ""
        found.append("uncommitted changes:\n" + "\n".join(lines[:12]) + more)
    git(root, "fetch", "-q", "origin", "main")  # best effort: offline, the last known origin/main is used
    if git(root, "rev-parse", "--verify", "-q", "origin/main").returncode == 0:
        if git(root, "merge-base", "--is-ancestor", "HEAD", "origin/main").returncode != 0:
            head = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
            found.append(f"HEAD {head} is not on origin/main: push the branch, open a PR and merge it (merge commit)")
    return found


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    if data.get("stop_hook_active"):
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return 0
    found = problems(root)
    if found:
        reason = (
            "Before this turn ends (CLAUDE.md, Rules): "
            + "; ".join(found)
            + ". Update frond/docs/ledger.md and frond/docs/now.md in the same change."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
