"""Undo through worlds (B4b): whatever changed the workspace during a turn goes back, with or without git, and what
anyone changed since stays (requirement R3)."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import unittest
from typing import ClassVar

from frond.agent.scripted import Step
from frond.events import FileChanged, Notice
from tests.helpers import TurnUndo, WorkspaceCase, scripted_agent

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main"]


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class GitWorkspaceTest(WorkspaceCase):
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

    def objects(self) -> int:
        return sum(len(files) for _, _, files in os.walk(self.root / ".git" / "objects"))

    def test_undo_reverts_what_commands_changed_and_leaves_ignored_paths(self):
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        before_objects = self.objects()
        tools.edit("a.txt", "two", "TWO")  # a tool edit first: undo must return to the turn's starting point
        tools.sh("sed -i 's/one/ONE/' a.txt && rm b.txt && echo new > c.txt && chmod +x run.sh")
        tools.sh("echo built > build/out.log")  # ignored by .gitignore: not tracked, as git status would not
        self.assertEqual((self.root / "a.txt").read_text(), "ONE\nTWO\n")
        changed = {e.path: e.kind for e in self.of_type(FileChanged)}
        self.assertEqual(changed, {"a.txt": "edit", "b.txt": "delete", "c.txt": "create", "run.sh": "edit"})
        self.assertEqual(self.objects(), before_objects)  # worlds never write into the user's .git
        turn.undo()
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\n")
        self.assertEqual((self.root / "b.txt").read_text(), "keep\n")
        self.assertFalse((self.root / "c.txt").exists())
        self.assertFalse(stat.S_IMODE((self.root / "run.sh").stat().st_mode) & 0o111)
        self.assertEqual((self.root / "build/out.log").read_text(), "built\n")
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(status.stdout, "")

    def test_a_background_jobs_new_ignored_output_survives_undo(self):  # F14
        shutil.rmtree(self.root / "build")  # not there when the turn starts
        turn = TurnUndo(self)
        (self.root / "build").mkdir()  # a background job's output, written between steps
        (self.root / "build" / "out").write_text("result\n")
        step = turn.timeline.snapshot()  # a step's snapshot, not a foreground command's
        self.assertIsNone(turn.timeline.lookup(step, "build"))
        turn.undo()
        self.assertEqual((self.root / "build" / "out").read_text(), "result\n")

    def test_a_mode_change_alone_shows_in_the_net_change(self):  # F15
        agent, _ = scripted_agent(self, [Step("Chmod.", "sh('chmod +x run.sh')\nSUBMIT(response='ok')")])
        agent.run_turn("make it executable")
        [change] = agent.turn_diff()
        self.assertEqual(change.path, "run.sh")
        self.assertEqual(change.diff, "(mode 644 → 755)")

    def test_a_turn_that_commits_is_left_to_git(self):
        commit = " ".join(GIT) + " commit -qam second"
        steps = [Step("Commit.", f"sh({f'echo more >> a.txt && {commit}'!r})\nSUBMIT(response='committed')")]
        agent, _ = scripted_agent(self, steps)
        record = agent.run_turn("commit it")
        self.assertTrue(record.head_moved)
        self.assertIn("moved git's HEAD", agent.undo())
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\nmore\n")

    def test_a_link_a_command_retargets_comes_back(self):
        os.symlink("a.txt", self.root / "link")
        subprocess.run([*GIT, "add", "link"], cwd=self.root, check=True)
        subprocess.run([*GIT, "commit", "-qm", "link"], cwd=self.root, check=True)
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        tools.sh("ln -sfn b.txt link && rm a.txt && printf 'x' > a.txt")
        turn.undo()
        self.assertEqual(os.readlink(self.root / "link"), "a.txt")
        self.assertEqual((self.root / "a.txt").read_text(), "one\ntwo\n")

    def test_un_ignoring_a_directory_mid_turn_never_makes_it_look_deleted(self):
        (self.root / "build/keep.bin").write_text("cache\n")
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        tools.sh("printf '' > .gitignore")  # build/ is no longer ignored
        tools.sh("echo again >> b.txt")
        result = turn.undo()
        self.assertEqual((self.root / "build/keep.bin").read_text(), "cache\n")
        self.assertEqual((self.root / ".gitignore").read_text(), "build/\n")
        self.assertNotIn("build/keep.bin", result.restored)


class WorkspaceWithoutGitTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"notes.txt": "a\nb\n", "data/old.csv": "1,2\n"}

    def test_commands_are_undone_without_git(self):
        tools = self.toolbox(mode="yolo")
        turn = TurnUndo(self, tools)
        tools.sh("echo c >> notes.txt && rm -r data && mkdir -p out && echo r > out/report.md")
        self.assertEqual(
            {e.path: e.kind for e in self.of_type(FileChanged)},
            {"notes.txt": "edit", "data/old.csv": "delete", "out/report.md": "create"},
        )
        turn.undo()
        self.assertEqual((self.root / "notes.txt").read_text(), "a\nb\n")
        self.assertEqual((self.root / "data/old.csv").read_text(), "1,2\n")
        self.assertFalse((self.root / "out").exists())

    def test_a_background_jobs_writes_during_the_turn_are_undone(self):
        steps = [
            Step("Start it.", "sh('sleep 0.2; echo late > job.txt', background=True)"),
            Step("Wait.", "import time; time.sleep(0.6)\nSUBMIT(response='done')"),
        ]
        agent, _ = scripted_agent(self, steps)
        record = agent.run_turn("run the job")
        self.assertEqual(record.files, ["job.txt"])
        agent.undo()
        self.assertFalse((self.root / "job.txt").exists())

    def test_an_edit_someone_makes_after_the_turn_survives_undo(self):
        text = "".join(f"line {i}\n" for i in range(1, 21))
        (self.root / "app.py").write_text(text)
        steps = [Step("Edit.", "edit('app.py', 'line 2\\n', 'line 2 by the agent\\n')\nSUBMIT(response='ok')")]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("change line 2")
        later = (self.root / "app.py").read_text().replace("line 19\n", "line 19 by the user\n")
        (self.root / "app.py").write_text(later)
        summary = agent.undo()
        self.assertIn("app.py", summary)
        self.assertEqual((self.root / "app.py").read_text(), text.replace("line 19\n", "line 19 by the user\n"))

    def test_the_same_lines_changed_since_are_kept_and_reported(self):
        steps = [Step("Edit.", "edit('notes.txt', 'a', 'agent')\nSUBMIT(response='ok')")]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("edit")
        (self.root / "notes.txt").write_text("user\nb\n")
        self.assertIn("kept notes.txt", agent.undo())
        self.assertEqual((self.root / "notes.txt").read_text(), "user\nb\n")

    def test_the_turns_net_change_is_reviewable(self):
        steps = [
            Step("Edit.", "edit('notes.txt', 'a', 'A')\nsh('echo x > tmp.txt && rm tmp.txt')\nSUBMIT(response='ok')")
        ]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("edit")
        diff = agent.turn_diff()
        self.assertEqual([(d.path, d.kind, d.scope) for d in diff], [("notes.txt", "edit", "diff")])
        self.assertIn("+A", diff[0].diff)

    def test_every_step_record_names_its_world(self):
        steps = [Step("One.", "write('x.txt', '1')"), Step("Two.", "SUBMIT(response='ok')")]
        agent, _ = scripted_agent(self, steps)
        agent.run_turn("go")
        worlds = [r.world for r in agent.steps.records() if r.kind == "step"]
        self.assertEqual(len(worlds), 2)
        self.assertTrue(all(len(w) == 64 for w in worlds))
        assert agent.timeline is not None
        self.assertIn("x.txt", agent.timeline.store.tree(worlds[0]))


class TooLargeWorkspaceTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"a": "1", "b": "2", "c": "3"}

    def test_snapshots_switch_off_and_undo_says_why(self):
        timeline = self.timeline(max_files=2)
        self.assertEqual(timeline.begin_turn(), ("", ""))
        self.assertFalse(timeline.enabled)
        self.assertIn("more than 2 files", timeline.reason)

    def test_slow_snapshots_turn_off_command_diffs(self):
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        turn.timeline.command_diffs = False
        tools.sh("echo d > d")
        self.assertEqual(self.of_type(FileChanged), [])
        self.assertEqual(turn.undo().restored, ["d"])  # undo still covers it
        self.assertEqual(self.of_type(Notice), [])


if __name__ == "__main__":
    unittest.main()
