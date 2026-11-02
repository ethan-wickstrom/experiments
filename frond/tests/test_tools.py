"""The host tools the agent calls from its REPL, and the approval policy around them."""

import shutil
import threading
import time
import unittest
from typing import ClassVar
from unittest import mock

from frond.agent.control import TurnControl
from frond.agent.policy import risky_reason
from frond.agent.tools import ToolError
from frond.events import CommandFinished, CommandOutput, FileChanged, PlanUpdated
from tests.helpers import WorkspaceCase


class ReadingTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        "src/app.py": "".join(f"line {i}\n" for i in range(1, 501)),
        "src/util.py": "def helper():\n    return 'TODO'\n",
        "README.md": "# Project\nTODO: write docs\n",
        "node_modules/x/index.js": "ignored\n",
    }

    def test_view_numbers_and_windows_lines(self):
        tools = self.toolbox()
        out = tools.view("src/app.py")
        self.assertTrue(out.startswith("  1│ line 1"))
        self.assertIn("100 more lines", out)
        self.assertEqual(tools.view("src/app.py", 499).splitlines(), ["499│ line 499", "500│ line 500"])

    def test_missing_file_suggests_alternatives(self):
        with self.assertRaisesRegex(FileNotFoundError, "Did you mean: src/util.py"):
            self.toolbox().view("util.py")

    def test_ls_skips_noise_and_glob_finds_files(self):
        tools = self.toolbox()
        listing = tools.ls()
        self.assertIn("src/", listing)
        self.assertNotIn("node_modules", listing)
        self.assertEqual(tools.glob("*.py"), ["src/app.py", "src/util.py"])
        self.assertEqual(tools.glob("src/**/*.py", "."), ["src/app.py", "src/util.py"])

    def test_grep_with_ripgrep_and_python_fallback(self):
        tools = self.toolbox()
        for force_python in (False, True):
            if force_python or shutil.which("rg") is None:
                with mock.patch("frond.agent.tools.shutil.which", return_value=None):
                    result = tools.grep("TODO", context=1)
            else:
                result = tools.grep("TODO", context=1)
            items = result["items"]
            self.assertEqual(sorted((m["path"], m["line"]) for m in items), [("README.md", 2), ("src/util.py", 2)])
            util = next(m for m in items if m["path"] == "src/util.py")
            self.assertEqual(util["before"], [[1, "def helper():"]])
        self.assertEqual(tools.grep("todo", ignore_case=True, glob="*.md")["files"], 1)


class WritingTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        "pkg/mod.py": "def f():\n    return 1\n\n\ndef g():\n    return 1\n",
        "crlf.txt": "a\r\nb\r\n",
    }

    def test_write_creates_and_reports_diffs(self):
        tools = self.toolbox()
        self.assertEqual(tools.write("new/dir/file.txt", "hello\n"), "created new/dir/file.txt (1 lines)")
        self.assertEqual((self.root / "new/dir/file.txt").read_text(), "hello\n")
        change = self.of_type(FileChanged)[-1]
        self.assertEqual((change.kind, change.added, change.removed), ("create", 1, 0))

    def test_edit_exact_ambiguous_and_missing(self):
        tools = self.toolbox()
        with self.assertRaisesRegex(ToolError, "occurs 2 times .* lines 2, 6"):
            tools.edit("pkg/mod.py", "    return 1\n", "    return 2\n")
        self.assertIn("at line 2", tools.edit("pkg/mod.py", "def f():\n    return 1", "def f():\n    return 2"))
        with self.assertRaisesRegex(ToolError, "Closest match near line 5"):
            tools.edit("pkg/mod.py", "def g(x):\n    return 1", "nope")
        tools.edit("pkg/mod.py", "return 1", "return 3", replace_all=True)
        self.assertEqual((self.root / "pkg/mod.py").read_text().count("return 3"), 1)

    def test_edit_tolerates_trailing_whitespace_and_keeps_crlf(self):
        tools = self.toolbox()
        tools.edit("pkg/mod.py", "def g():   \n    return 1  \n", "def g():\n    return 9\n")
        self.assertIn("return 9", (self.root / "pkg/mod.py").read_text())
        tools.edit("crlf.txt", "a\nb", "a\nB")
        self.assertEqual((self.root / "crlf.txt").read_bytes(), b"a\r\nB\r\n")

    def test_edit_with_empty_old_creates_a_file(self):
        self.toolbox().edit("fresh.py", "", "x = 1\n")
        self.assertEqual((self.root / "fresh.py").read_text(), "x = 1\n")

    def test_patch_is_all_or_nothing(self):
        tools = self.toolbox()
        bad = (
            "*** Begin Patch\n*** Add File: added.txt\n+new\n*** Update File: pkg/mod.py\n@@\n-missing\n+x\n"
            "*** End Patch"
        )
        with self.assertRaises(ToolError):
            tools.patch(bad)
        self.assertFalse((self.root / "added.txt").exists())
        good = (
            "*** Begin Patch\n*** Add File: added.txt\n+new\n*** Update File: pkg/mod.py\n@@ def g():\n"
            "-    return 1\n+    return 7\n*** End Patch"
        )
        summary = tools.patch(good)
        self.assertIn("created added.txt", summary)
        self.assertTrue((self.root / "pkg/mod.py").read_text().endswith("return 7\n"))

    def test_delete_and_move(self):
        tools = self.toolbox()
        tools.move("pkg/mod.py", "lib/mod.py")
        self.assertTrue((self.root / "lib/mod.py").exists())
        with self.assertRaisesRegex(ToolError, "recursive=True"):
            tools.delete("lib")
        tools.delete("lib", recursive=True)
        self.assertFalse((self.root / "lib").exists())

    def test_read_only_toolbox_refuses_writes(self):
        tools = self.toolbox(read_only=True)
        names = [getattr(f, "__name__", "") for f in tools.functions()]
        self.assertNotIn("write", names)
        with self.assertRaises(PermissionError):
            tools.write("x.txt", "nope")

    def test_plan_parses_statuses(self):
        self.toolbox().plan(["[x] one", "[>] two", "three"])
        items = self.of_type(PlanUpdated)[-1].items
        self.assertEqual([(i.text, i.status) for i in items], [("one", "done"), ("two", "active"), ("three", "todo")])


class ShellTest(WorkspaceCase):
    def test_foreground_command_streams_and_reports(self):
        tools = self.toolbox()
        r = tools.sh("echo hello; echo oops >&2; exit 3")
        self.assertEqual((r["exit_code"], r["status"], r["ok"]), (3, "failed", False))
        self.assertIn("hello", r["output"])
        self.assertIn("oops", r["output"])
        self.assertIn("hello", "".join(e.text for e in self.of_type(CommandOutput)))
        self.assertEqual(self.of_type(CommandFinished)[-1].status, "failed")

    def test_timeout_kills_the_process_group(self):
        tools = self.toolbox()
        started = time.monotonic()
        r = tools.sh("sleep 30 & sleep 30; echo never", timeout=1)
        self.assertEqual(r["status"], "timeout")
        self.assertLess(time.monotonic() - started, 6)

    def test_cancel_stops_a_running_command(self):
        control = TurnControl()
        tools = self.toolbox(control=control)
        threading.Timer(0.3, control.cancel).start()
        started = time.monotonic()
        r = tools.sh("sleep 20")
        self.assertEqual(r["status"], "cancelled")
        self.assertLess(time.monotonic() - started, 5)

    def test_background_jobs(self):
        tools = self.toolbox()
        job = tools.sh("echo ready; sleep 30", background=True)
        self.assertTrue(job["running"])
        self.assertIn("ready", job["output"])
        self.assertEqual(tools.jobs()[0]["job"], job["job"])
        self.assertIn("stopped", tools.job_kill(job["job"]))
        self.assertFalse(tools.jobs()[0]["running"])

    def test_risky_commands_need_approval(self):
        self.assertEqual(risky_reason("rm -rf build"), "recursive or forced delete")
        self.assertEqual(risky_reason("git push --force origin main"), "force push")
        self.assertIsNone(risky_reason("rm notes.txt"))
        self.assertIsNone(risky_reason("uv run pytest -q"))
        asked: list[str] = []
        tools = self.toolbox(approver=lambda title, detail: asked.append(detail) or "no")
        with self.assertRaisesRegex(PermissionError, "declined"):
            tools.sh("rm -rf build")
        self.assertEqual(asked, ["rm -rf build"])
        always = self.toolbox(approver=lambda title, detail: "always")
        always.sh("rm -rf build")
        self.assertEqual(always.sh("rm -rf build")["status"], "ok")
        with self.assertRaisesRegex(PermissionError, "not available here"):
            self.toolbox().sh("rm -rf build")
        self.assertEqual(self.toolbox(mode="yolo").sh("rm -rf build")["status"], "ok")
        with self.assertRaises(PermissionError):
            self.toolbox(mode="readonly").sh("ls")


if __name__ == "__main__":
    unittest.main()
