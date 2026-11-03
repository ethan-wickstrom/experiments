"""Worlds: content-addressed, versioned workspace state (decision D22). See design.md, "Architecture: worlds"."""

from frond.world.merge import Merged, Revert, merge3, revert
from frond.world.store import EXCLUDED, Change, Entry, Store, Worktree

__all__ = ["EXCLUDED", "Change", "Entry", "Merged", "Revert", "Store", "Worktree", "merge3", "revert"]
