"""Freshness (B5, H3): reads become observations, stale ones are shown to the model, and a change the model never
saw cannot be overwritten; with freshness off, stale actions are only counted."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

from frond.agent.freshness import Observations
from frond.agent.metrics import RunMetrics
from frond.agent.scripted import Step
from frond.agent.tools import Toolbox, ToolError
from tests.helpers import WorkspaceCase, scripted_agent


class ObservationsTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"a.py": "x = 1\n"}

    def test_a_read_stays_fresh_until_the_file_changes(self):
        seen = Observations(self.root)
        seen.step = 2
        seen.saw("a.py", (self.root / "a.py").read_bytes())
        self.assertIsNone(seen.changed("a.py"))
        self.assertEqual(seen.note(), "(none)")
        (self.root / "a.py").write_text("x = 2\n")
        stale = seen.changed("a.py")
        assert stale is not None
        self.assertEqual(stale.step, 2)
        self.assertIn("a.py (read at step 2", seen.note())
        (self.root / "a.py").unlink()
        self.assertIsNotNone(seen.changed("a.py"))
        self.assertIsNone(seen.changed("never-read.py"))


class GuardTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"a.py": "one\ntwo\nthree\n"}

    def tools(self, *, freshness: bool) -> tuple[Toolbox, RunMetrics]:
        tools = self.toolbox(mode="yolo")
        tools.observations = Observations(self.root)
        tools.metrics = metrics = RunMetrics()
        tools.freshness = freshness
        return tools, metrics

    def test_a_whole_file_write_over_a_stale_read_is_refused_until_it_is_read_again(self):
        tools, metrics = self.tools(freshness=True)
        tools.view("a.py")
        (self.root / "a.py").write_text("one\ntwo\nthree\nadded by the user\n")
        with self.assertRaisesRegex(ToolError, "changed since you read it"):
            tools.write("a.py", "rewritten\n")
        self.assertIn("added by the user", (self.root / "a.py").read_text())
        with self.assertRaisesRegex(ToolError, "changed since you read it"):
            tools.delete("a.py")
        self.assertEqual(metrics.stale_actions, 2)
        tools.read("a.py")
        tools.write("a.py", "rewritten\n")  # read again: allowed
        self.assertEqual((self.root / "a.py").read_text(), "rewritten\n")

    def test_a_stale_edit_applies_where_it_still_matches_and_says_so(self):
        tools, metrics = self.tools(freshness=True)
        tools.view("a.py")
        (self.root / "a.py").write_text("zero\none\ntwo\nthree\n")
        result = tools.edit("a.py", "two", "TWO")
        self.assertIn("had changed since you read it at step 0", result)
        self.assertEqual((self.root / "a.py").read_text(), "zero\none\nTWO\nthree\n")
        self.assertIsNotNone(tools.observations and tools.observations.changed("a.py"))  # still stale
        self.assertEqual(metrics.stale_actions, 1)

    def test_the_models_own_edits_keep_its_picture_fresh(self):
        tools, metrics = self.tools(freshness=True)
        tools.view("a.py")
        tools.edit("a.py", "two", "TWO")
        tools.write("a.py", "replaced\n")
        assert tools.observations is not None
        self.assertIsNone(tools.observations.changed("a.py"))
        self.assertEqual(metrics.stale_actions, 0)

    def test_a_patch_deleting_a_stale_file_writes_nothing(self):
        (self.root / "b.py").write_text("b\n")
        tools, _ = self.tools(freshness=True)
        tools.view("a.py")
        (self.root / "a.py").write_text("changed\n")
        patch = "*** Begin Patch\n*** Update File: b.py\n@@\n-b\n+B\n*** Delete File: a.py\n*** End Patch"
        with self.assertRaises(ToolError):
            tools.patch(patch)
        self.assertEqual((self.root / "b.py").read_text(), "b\n")  # validated before anything was written

    def test_off_counts_stale_actions_and_changes_nothing_else(self):
        tools, metrics = self.tools(freshness=False)
        tools.view("a.py")
        (self.root / "a.py").write_text("one\ntwo\nthree\nmore\n")
        self.assertNotIn("Note", tools.edit("a.py", "two", "TWO"))
        tools.write("a.py", "overwritten\n")
        self.assertEqual((self.root / "a.py").read_text(), "overwritten\n")
        self.assertEqual(metrics.stale_actions, 2)


class ReviewFindingsTest(WorkspaceCase):
    """Devin's findings on PR #13 (ledger F16-F21)."""

    files: ClassVar[dict[str, str]] = {"src/app.py": "x = 1\n", "src/util.py": "y = 2\n", "settings.py": "a = 1\n"}

    def tools(self, *, freshness: bool = True) -> tuple[Toolbox, RunMetrics]:
        tools = self.toolbox(mode="yolo")
        tools.observations = Observations(self.root)
        tools.metrics = metrics = RunMetrics()
        tools.freshness = freshness
        return tools, metrics

    def test_deleting_a_directory_checks_every_read_inside_it(self):  # F16
        tools, metrics = self.tools()
        tools.view("src/app.py")
        (self.root / "src" / "app.py").write_text("x = 1  # formatted\n")
        with self.assertRaisesRegex(ToolError, "files in src changed since you read them: src/app.py"):
            tools.delete("src", recursive=True)
        self.assertTrue((self.root / "src" / "app.py").exists())
        self.assertEqual(metrics.stale_actions, 1)
        tools.view("src/app.py")
        tools.delete("src", recursive=True)
        self.assertFalse((self.root / "src").exists())
        self.assertEqual(tools.observations.stale() if tools.observations else None, [])  # its own delete: not stale

    def test_a_symlink_and_its_target_share_one_read(self):  # F17
        (self.root / "config.py").symlink_to("src/app.py")
        tools, _ = self.tools()
        tools.view("config.py")
        (self.root / "src" / "app.py").write_text("x = 1\nchanged = True\n")
        with self.assertRaisesRegex(ToolError, "changed since you read it"):
            tools.write("src/app.py", "x = 3\n")
        self.assertIn("changed = True", (self.root / "src" / "app.py").read_text())

    def test_a_symlink_retargeted_since_the_read_is_stale(self):  # review of #24
        (self.root / "first.txt").write_text("first\n")
        (self.root / "second.txt").write_text("second, never read\n")
        (self.root / "config").symlink_to("first.txt")
        tools, _ = self.tools()
        tools.view("config")
        (self.root / "config").unlink()
        (self.root / "config").symlink_to("second.txt")
        with self.assertRaisesRegex(ToolError, "changed since you read it"):
            tools.write("config", "overwrite\n")
        self.assertEqual((self.root / "second.txt").read_text(), "second, never read\n")
        assert tools.observations is not None
        self.assertIn("config", [o.path for o in tools.observations.stale()])
        tools.view("config")  # read again through the new link: fresh
        tools.write("config", "overwrite\n")

    def test_a_stale_read_moves_with_its_file(self):  # review of #24
        tools, _ = self.tools()
        tools.view("settings.py")
        (self.root / "settings.py").write_text("a = 2  # formatted\n")
        tools.move("settings.py", "conf/settings.py")
        assert tools.observations is not None
        self.assertEqual([o.path for o in tools.observations.stale()], ["conf/settings.py"])

    def test_a_child_already_gone_does_not_block_its_directory(self):  # review of #24
        tools, metrics = self.tools()
        tools.view("src/app.py")
        (self.root / "src" / "app.py").unlink()  # as sh("rm src/app.py") would
        tools.delete("src", recursive=True)
        self.assertFalse((self.root / "src").exists())
        self.assertEqual(metrics.stale_actions, 1)  # still a stale action, counted

    def test_moving_a_link_leaves_its_targets_read_alone(self):  # review of #24
        tools, metrics = self.tools()
        tools.view("src/app.py")
        (self.root / "alias").symlink_to("src/app.py")
        tools.move("alias", "other/alias")
        tools.write("src/app.py", "x = 2\n")  # unchanged since read: no refusal, nothing stale
        self.assertEqual(metrics.stale_actions, 0)

    def test_the_models_own_delete_or_move_leaves_its_picture_true(self):  # F18
        tools, metrics = self.tools()
        tools.view("settings.py")
        tools.delete("settings.py")
        self.assertIn("created settings.py", tools.write("settings.py", "a = 2\n"))
        tools.view("src/util.py")
        tools.move("src/util.py", "lib/util.py")
        tools.write("lib/util.py", "y = 3\n")  # the read moved with the file, so this is not a blind overwrite
        tools.write("src/util.py", "y = 4\n")  # gone by its own move: nothing to lose
        self.assertEqual(metrics.stale_actions, 0)

    def test_a_file_deleted_behind_the_models_back_can_be_written_again(self):  # F18, by a shell command
        tools, metrics = self.tools()
        tools.view("settings.py")
        (self.root / "settings.py").unlink()  # as sh("rm settings.py") would
        result = tools.write("settings.py", "a = 9\n")
        self.assertIn("it was deleted after you read it at step 0", result)
        self.assertEqual(metrics.stale_actions, 1)
        self.assertIsNone(tools.observations.changed("settings.py") if tools.observations else 0)  # now known

    def test_a_stale_edit_that_no_longer_matches_is_still_counted(self):  # F19
        tools, metrics = self.tools()
        tools.view("src/app.py")
        (self.root / "src" / "app.py").write_text("z = 1\n")
        with self.assertRaises(ToolError):
            tools.edit("src/app.py", "x = 1", "x = 2")
        self.assertEqual(metrics.stale_actions, 1)

    def test_a_file_under_home_is_checked_where_it_is(self):  # F21
        home = Path(tempfile.mkdtemp(prefix="frond-home-"))
        self.addCleanup(shutil.rmtree, home, True)
        (home / "notes.txt").write_text("remember\n")
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            tools, metrics = self.tools()
            tools.view("~/notes.txt")
            self.assertEqual(tools.observations.stale() if tools.observations else None, [])
            tools.write("~/notes.txt", "remember more\n")
        self.assertEqual(metrics.stale_actions, 0)
        self.assertEqual((home / "notes.txt").read_text(), "remember more\n")


class PromptTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"app.py": "x = 1\n"}

    def run_steps(self, *, freshness: bool) -> list[str]:
        steps = [
            Step("Look and format.", "view('app.py')\nsh(\"sed -i 's/1/2/' app.py\")"),
            Step("Look again.", "view('app.py')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps)
        agent.config.freshness = freshness
        agent.rlm.freshness = freshness
        agent.toolbox.freshness = freshness
        agent.run_turn("go")
        return ["\n".join(m.text or "" for m in r.messages) for r in engine.requests if r.messages]

    def test_a_read_gone_stale_is_named_in_the_next_prompt_and_cleared_by_a_new_read(self):
        prompts = self.run_steps(freshness=True)
        self.assertIn("[[ ## stale_reads ## ]]\n(none)", prompts[0])
        self.assertIn("app.py (read at step 1; it has changed since)", prompts[1])
        self.assertIn("[[ ## stale_reads ## ]]\n(none)", prompts[2])

    def test_with_freshness_off_the_prompt_has_no_such_field(self):
        prompts = self.run_steps(freshness=False)
        self.assertTrue(all("stale_reads" not in p for p in prompts))


if __name__ == "__main__":
    unittest.main()
