"""/undo covers what shell commands change in a git workspace, through private snapshots that leave .git alone."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

from frond.agent.checkpoints import Checkpoints
from frond.agent.snapshots import GitSnapshots
from frond.events import FileChanged, Notice
from tests.helpers import WorkspaceCase

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main"]


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class CommandUndoTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        "a.txt": "one\ntwo\n",
        "b.txt": "keep\n",
        "run.sh": "echo hi\n",
        ".gitignore": "build/\n",
    }

    def setUp(self) -> None:
        super().setUp()
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "base"]):
            subprocess.run([*GIT, *args], cwd=self.root, check=True, capture_output=True)
        (self.root / "build").mkdir()
        self.scratch = Path(tempfile.mkdtemp(prefix="frond-snap-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def tracked_toolbox(self):
        tools = self.toolbox()
        tools.checkpoints = checkpoints = Checkpoints()
        tools.snapshots = GitSnapshots(self.root, self.scratch)
        checkpoints.begin(1)
        return tools, checkpoints

    def objects(self) -> int:
        return sum(len(files) for _, _, files in os.walk(self.root / ".git" / "objects"))

    def test_undo_reverts_what_commands_changed(self):
        tools, checkpoints = self.tracked_toolbox()
        before_objects = self.objects()
        tools.edit("a.txt", "two", "TWO")  # a tool edit first: undo must return to the turn's starting point
        tools.sh("sed -i 's/one/ONE/' a.txt && rm b.txt && echo new > c.txt && chmod +x run.sh")
        tools.sh("echo built > build/out.log")  # ignored by .gitignore: not tracked
        self.assertEqual((self.root / "a.txt").read_text(), "ONE\nTWO\n")
        changed = {e.path: e.kind for e in self.of_type(FileChanged)}
        self.assertEqual(changed, {"a.txt": "edit", "b.txt": "delete", "c.txt": "create", "run.sh": "edit"})
        self.assertEqual(self.objects(), before_objects)  # snapshots wrote nothing into the user's .git
        checkpoints.undo()
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\n")
        self.assertEqual((self.root / "b.txt").read_text(), "keep\n")
        self.assertFalse((self.root / "c.txt").exists())
        self.assertFalse(stat.S_IMODE((self.root / "run.sh").stat().st_mode) & 0o111)
        self.assertEqual((self.root / "build/out.log").read_text(), "built\n")
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(status.stdout, "")

    def test_commands_that_move_head_are_left_alone(self):
        tools, checkpoints = self.tracked_toolbox()
        tools.sh(f"echo more >> a.txt && {' '.join(GIT)} commit -qam second")
        self.assertTrue(any("moved HEAD" in n.text for n in self.of_type(Notice)))
        self.assertIsNone(checkpoints.undo())  # nothing journaled: undoing files would contradict the new commit
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\nmore\n")

    def test_a_link_a_command_retargets_comes_back(self):
        os.symlink("a.txt", self.root / "link")
        subprocess.run([*GIT, "add", "link"], cwd=self.root, check=True)
        subprocess.run([*GIT, "commit", "-qm", "link"], cwd=self.root, check=True)
        tools, checkpoints = self.tracked_toolbox()
        tools.sh("ln -sfn b.txt link && rm a.txt && printf 'x' > a.txt")
        checkpoints.undo()
        self.assertEqual(os.readlink(self.root / "link"), "a.txt")
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\n")


class NotAGitWorkspaceTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"x.txt": "x\n"}

    def test_snapshots_switch_themselves_off(self):
        snapshots = GitSnapshots(self.root, Path(tempfile.mkdtemp(prefix="frond-snap-")))
        self.assertFalse(snapshots.enabled)
        self.assertIsNone(snapshots.take())


if __name__ == "__main__":
    unittest.main()
