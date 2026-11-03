"""Git's own state around FORK (F26): captured, restored, in plain repositories and linked worktrees."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from frond.world import gitstate

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


def git(cwd: Path, *args: str) -> str:
    return subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class GitStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="frond-git-"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "a.txt").write_text("a\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "start")

    def test_a_linked_worktrees_shared_branch_ref_is_restored(self):  # Devin, #33 (F62)
        tree = self.dir / "tree"
        git(self.repo, "worktree", "add", "-q", "-b", "work", str(tree))
        dirs = gitstate.git_dir(tree)
        assert dirs is not None
        self.assertNotEqual(dirs.private, dirs.common)
        start = git(tree, "rev-parse", "HEAD")
        state = gitstate.capture(dirs)
        (tree / "b.txt").write_text("b\n")
        git(tree, "add", "-A")
        git(tree, "commit", "-qm", "discarded")
        gitstate.restore(dirs, state)
        self.assertEqual(git(tree, "rev-parse", "HEAD"), start)
        self.assertEqual(git(self.repo, "rev-parse", "work"), start)  # the shared ref, seen from the main tree too

    def test_a_ref_replaced_by_a_nested_one_comes_back(self):  # Codex and Devin, #33 (F65)
        dirs = gitstate.git_dir(self.repo)
        assert dirs is not None
        git(self.repo, "branch", "topic")
        state = gitstate.capture(dirs)
        git(self.repo, "branch", "-D", "topic")
        git(self.repo, "branch", "topic/child")
        gitstate.restore(dirs, state)
        self.assertEqual(sorted(git(self.repo, "branch", "--format=%(refname:short)").split()), ["main", "topic"])

    def test_links_under_git_are_neither_read_nor_written_through(self):
        dirs = gitstate.git_dir(self.repo)
        assert dirs is not None
        outside = self.dir / "outside"
        outside.mkdir()
        (outside / "secret").write_text("s")
        (self.repo / ".git" / "refs" / "heads" / "link").symlink_to(outside / "secret")
        state = gitstate.capture(dirs)
        self.assertNotIn(("private", "refs/heads/link"), state.files)
        gitstate.restore(dirs, state)
        self.assertEqual((outside / "secret").read_text(), "s")
        self.assertFalse((self.repo / ".git" / "refs" / "heads" / "link").is_symlink())


if __name__ == "__main__":
    unittest.main()
