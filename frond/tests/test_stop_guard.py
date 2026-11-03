"""The Stop hook ends a turn only when the work is committed and on origin/main, and fails closed (D19)."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "stop_guard.py"
_spec = importlib.util.spec_from_file_location("stop_guard", HOOK)
assert _spec is not None and _spec.loader is not None
stop_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stop_guard)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


class StopGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="frond-guard-"))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.work = self.base / "work"
        self.work.mkdir()
        git(self.work, "init", "-q")
        (self.work / "a.txt").write_text("a\n")
        git(self.work, "add", "a.txt")
        git(self.work, "commit", "-q", "-m", "one")

    def test_no_origin_main_blocks(self):
        found = stop_guard.problems(str(self.work))
        self.assertEqual(len(found), 1)
        self.assertIn("origin/main cannot be resolved", found[0])

    def test_merged_and_clean_passes_and_dirty_or_unmerged_blocks(self):
        git(self.base, "init", "-q", "--bare", "origin.git")
        git(self.work, "remote", "add", "origin", str(self.base / "origin.git"))
        git(self.work, "push", "-q", "origin", "main")
        self.assertEqual(stop_guard.problems(str(self.work)), [])
        (self.work / "a.txt").write_text("changed\n")
        self.assertIn("uncommitted changes", stop_guard.problems(str(self.work))[0])
        git(self.work, "commit", "-q", "-am", "two")
        self.assertIn("is not on origin/main", stop_guard.problems(str(self.work))[0])


if __name__ == "__main__":
    unittest.main()
