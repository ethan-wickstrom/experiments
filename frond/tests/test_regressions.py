"""Regression tests for bugs found in review: patch fidelity, undo, symlinks, approvals, compaction, commands,
search limits, sessions and queued turns."""

import contextlib
import io
import itertools
import json
import os
import shutil
import stat
import threading
import time
from pathlib import Path
from typing import ClassVar
from unittest import mock

from dspy.primitives.repl_types import REPLEntry, REPLHistory

from frond import cli
from frond.agent.control import TurnControl
from frond.agent.patch import apply_chunks, parse_patch
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import INDEX_MARK, NOTE_CODE, FoldEntry, FrondRLM, Hooks, LoggedEntry
from frond.agent.scripted import Step
from frond.agent.session import TurnRecord
from frond.agent.tools import ToolError
from frond.events import TurnFinished
from frond.sessions import SessionStore
from frond.tui.app import App, ApprovalRequest
from tests.helpers import TurnUndo, WorkspaceCase, scripted_agent


class PatchFidelityTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"tabs.py": "def f():\n\tx = 1\n\ty = 2\n\treturn x\n"}

    def test_whitespace_fallback_keeps_the_files_own_context_lines(self):
        patch = (
            "*** Begin Patch\n*** Update File: t\n@@\n     x = 1\n-    y = 2\n+    y = 3\n     return x\n*** End Patch"
        )
        [op] = parse_patch(patch)
        out = apply_chunks("def f():\n\tx = 1\n\ty = 2\n\treturn x\n", op.chunks, "t")
        self.assertEqual(out, "def f():\n\tx = 1\n    y = 3\n\treturn x\n")

    def test_crlf_files_stay_crlf(self):
        [op] = parse_patch("*** Begin Patch\n*** Update File: t\n@@\n a\n-b\n+B\n c\n*** End Patch")
        self.assertEqual(apply_chunks("a\r\nb\r\nc\r\n", op.chunks, "t"), "a\r\nB\r\nc\r\n")

    def test_zero_context_unified_insertion_uses_the_line_number(self):
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -2,0 +3 @@\n+inserted\n")
        self.assertEqual(apply_chunks("1\n2\n3\n4\n", op.chunks, "x"), "1\n2\ninserted\n3\n4\n")

    def test_patch_refuses_non_utf8_duplicates_and_clobbering_moves(self):
        (self.root / "latin.py").write_bytes(b"name = 'caf\xe9'\nx = 1\n")
        (self.root / "taken.py").write_text("keep me\n")
        tools = self.toolbox()
        with self.assertRaisesRegex(ToolError, "not valid UTF-8"):
            tools.patch("*** Begin Patch\n*** Update File: latin.py\n@@\n-x = 1\n+x = 2\n*** End Patch")
        self.assertEqual((self.root / "latin.py").read_bytes(), b"name = 'caf\xe9'\nx = 1\n")
        with self.assertRaisesRegex(ToolError, "more than once"):
            tools.patch(
                "*** Begin Patch\n*** Update File: tabs.py\n@@\n-\tx = 1\n+\tx = 9\n"
                "*** Update File: tabs.py\n@@\n-\ty = 2\n+\ty = 9\n*** End Patch"
            )
        with self.assertRaisesRegex(ToolError, "already exists"):
            tools.patch("*** Begin Patch\n*** Update File: tabs.py\n*** Move to: taken.py\n*** End Patch")
        self.assertEqual((self.root / "taken.py").read_text(), "keep me\n")


class UndoOrderingAndSymlinkTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"a/x.py": "orig\n", "target/inside.txt": "t\n"}

    def test_undo_after_moving_a_directory_then_editing_inside_it(self):
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        tools.move("a", "b")
        tools.edit("b/x.py", "orig", "edited")
        result = turn.undo()
        self.assertEqual((self.root / "a/x.py").read_text(), "orig\n")
        self.assertFalse((self.root / "b").exists())
        self.assertEqual(sorted(result.restored), ["a/x.py", "b/x.py"])

    def test_delete_removes_symlinks_not_their_targets_and_undo_restores_them(self):
        os.symlink("target", self.root / "dir_link")
        os.symlink("nowhere", self.root / "dangling")
        tools = self.toolbox()
        turn = TurnUndo(self, tools)
        self.assertIn("symbolic link", tools.delete("dir_link"))
        self.assertIn("symbolic link", tools.delete("dangling"))
        self.assertTrue((self.root / "target/inside.txt").exists())
        self.assertFalse(os.path.lexists(self.root / "dangling"))
        turn.undo()
        self.assertEqual(os.readlink(self.root / "dir_link"), "target")
        self.assertEqual(os.readlink(self.root / "dangling"), "nowhere")


class _StubAgent:
    """Just enough of the agent for the app to stop a turn."""

    def start_turn(self, request: str, attachments: dict[str, str] | None = None) -> None: ...
    def steer(self, text: str) -> bool:
        return False

    def cancel(self) -> None: ...
    def undo(self) -> str:
        return ""

    def turn_diff(self, index: int | None = None) -> list:
        return []

    def reset_repl(self) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


class ApprovalQueueTest(WorkspaceCase):
    def test_concurrent_requests_are_answered_in_turn_and_stop_declines_the_rest(self):
        app = App(self.ws, model="m", sub_model="m")
        answers: dict[str, str] = {}

        def ask(name: str) -> None:
            answers[name] = app.approver(name, f"detail {name}")

        threads = [threading.Thread(target=ask, args=(n,)) for n in ("first", "second", "third")]
        for t in threads:
            t.start()
        deadline = time.monotonic() + 5
        while (app.approval is None or len(app.pending_approvals) < 2) and time.monotonic() < deadline:
            app.pump()
            time.sleep(0.01)
        self.assertIsInstance(app.approval, ApprovalRequest)
        first_title = app.approval.title if app.approval else ""
        from frond.tui.keys import Key

        app.on_input(Key("y"))
        self.assertIsNotNone(app.approval)  # the next request is shown, not lost
        app.running = True
        app.attach(_StubAgent())
        app.stop()
        for t in threads:
            t.join(5)
        self.assertEqual(answers[first_title], "yes")
        self.assertEqual(sorted(v for k, v in answers.items() if k != first_title), ["no", "no"])


class FoldingKeepsTheIndexTest(WorkspaceCase):
    def test_an_earlier_index_survives_a_second_fold(self):
        class TinyBudget(Hooks):
            def history_budget(self) -> int:
                return 3000

        rlm = FrondRLM(CodingTurn, hooks=TinyBudget(), keep_recent=2)
        earlier = f"{INDEX_MARK}\n- step 1 · seq 2 · IMPORTANT: edited src/app.py:42 → ok"
        entries: list[REPLEntry] = [FoldEntry(reasoning="(folded)", code=NOTE_CODE, output=earlier)]
        entries += [
            LoggedEntry(reasoning=f"step {i}", code=f"print({i})", output="x" * 900, seq=i + 3, step=i + 2)
            for i in range(6)
        ]
        folded = rlm._fold(REPLHistory(entries=entries))
        note = folded.entries[0]
        self.assertEqual(note.code, NOTE_CODE)
        self.assertIn("IMPORTANT: edited src/app.py:42", note.output)
        self.assertIn("- step 2 · seq 3 · step 0 → xxxx", note.output)
        self.assertEqual(len(folded.entries), 3)


class PatchEndOfFileTest(WorkspaceCase):
    def test_the_no_newline_marker_adds_or_removes_the_final_newline(self):
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n\\ No newline at end of file\n+new\n")
        self.assertEqual(apply_chunks("old", op.chunks, "x"), "new\n")
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new\n\\ No newline at end of file\n")
        self.assertEqual(apply_chunks("old\n", op.chunks, "x"), "new")
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n a\n-b\n\\ No newline at end of file\n+B\n")
        self.assertEqual(apply_chunks("a\r\nb", op.chunks, "x"), "a\r\nB\r\n")
        [op] = parse_patch("--- /dev/null\n+++ b/x\n@@ -0,0 +1 @@\n+solo\n\\ No newline at end of file\n")
        self.assertEqual(op.content, "solo")

    def test_removing_every_line_leaves_an_empty_file(self):
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1 +0,0 @@\n-old\n\\ No newline at end of file\n")
        self.assertEqual(apply_chunks("old", op.chunks, "x"), "")
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1,2 +0,0 @@\n-a\n-b\n\\ No newline at end of file\n")
        self.assertEqual(apply_chunks("a\r\nb", op.chunks, "x"), "")
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1 +0,0 @@\n-old\n")
        self.assertEqual(apply_chunks("old\n", op.chunks, "x"), "")

    def test_lines_added_to_an_empty_file(self):
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -0,0 +1 @@\n+new\n")
        self.assertEqual(apply_chunks("", op.chunks, "x"), "new\n")
        [op] = parse_patch("*** Begin Patch\n*** Update File: x\n@@\n+new\n*** End Patch")
        self.assertEqual(apply_chunks("", op.chunks, "x"), "new\n")

    def test_without_a_marker_the_file_keeps_its_own_ending(self):
        [op] = parse_patch("--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n a\n-b\n+B\n")
        self.assertEqual(apply_chunks("a\nb", op.chunks, "x"), "a\nB")
        self.assertEqual(apply_chunks("a\r\nb", op.chunks, "x"), "a\r\nB")


class UndoFidelityTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        "assets/a.txt": "a\n",
        "scripts/build.sh": "#!/bin/sh\necho hi\n",
        "src/m.py": "x = 1\n",
    }

    def undoable(self, **kwargs):
        tools = self.toolbox(**kwargs)
        return tools, TurnUndo(self, tools)

    def test_undo_of_a_recursive_delete_brings_back_links_empty_folders_and_modes(self):
        (self.root / "assets/empty").mkdir()
        os.symlink("a.txt", self.root / "assets/latest")
        (self.root / "scripts/build.sh").chmod(0o755)
        tools, turn = self.undoable(mode="yolo")
        tools.delete("assets", recursive=True)
        tools.delete("scripts/build.sh")
        turn.undo()
        self.assertTrue((self.root / "assets/empty").is_dir())
        self.assertEqual(os.readlink(self.root / "assets/latest"), "a.txt")
        self.assertEqual((self.root / "assets/a.txt").read_text(), "a\n")
        self.assertEqual(stat.S_IMODE((self.root / "scripts/build.sh").stat().st_mode), 0o755)

    def test_a_deleted_tree_without_regular_files_can_be_undone(self):
        (self.root / "hollow/inner").mkdir(parents=True)
        tools, turn = self.undoable(mode="yolo")
        tools.delete("hollow", recursive=True)
        self.assertEqual(turn.undo().restored, ["hollow/inner"])
        self.assertTrue((self.root / "hollow/inner").is_dir())

    def test_undoing_a_directory_move_removes_the_folders_it_created(self):
        tools, turn = self.undoable()
        tools.move("src", "generated/deep/src")
        turn.undo()
        self.assertEqual((self.root / "src/m.py").read_text(), "x = 1\n")
        self.assertFalse((self.root / "generated").exists())

    def test_patches_and_moves_journal_the_symlink_not_its_target(self):
        os.symlink("src/m.py", self.root / "link.py")
        os.symlink("src/m.py", self.root / "other.py")
        tools, turn = self.undoable()
        tools.patch("*** Begin Patch\n*** Delete File: link.py\n*** End Patch")
        tools.move("other.py", "renamed.py")
        turn.undo()
        self.assertEqual(os.readlink(self.root / "link.py"), "src/m.py")
        self.assertEqual(os.readlink(self.root / "other.py"), "src/m.py")
        self.assertFalse(os.path.lexists(self.root / "renamed.py"))
        self.assertEqual((self.root / "src/m.py").read_text(), "x = 1\n")

    def test_undoing_a_move_removes_the_moved_link_even_where_it_dangles(self):
        os.symlink("src/m.py", self.root / "shortcut")  # relative: it points nowhere once moved into sub/
        tools, turn = self.undoable()
        tools.move("shortcut", "sub/shortcut")
        self.assertTrue(os.path.lexists(self.root / "sub/shortcut"))
        self.assertFalse((self.root / "sub/shortcut").exists())
        turn.undo()
        self.assertEqual(os.readlink(self.root / "shortcut"), "src/m.py")
        self.assertFalse(os.path.lexists(self.root / "sub"))

    def test_recursive_delete_asks_first(self):
        asked: list[str] = []
        tools = self.toolbox(approver=lambda title, detail: asked.append(detail) or "no")
        with self.assertRaisesRegex(PermissionError, "declined"):
            tools.delete("assets", recursive=True)
        self.assertEqual(asked, ["assets/ (1 entry)"])
        self.assertTrue((self.root / "assets/a.txt").exists())
        self.toolbox(approver=lambda title, detail: "yes").delete("assets", recursive=True)
        self.assertFalse((self.root / "assets").exists())


class SilentCommandTest(WorkspaceCase):
    def test_a_command_that_closes_its_output_still_reports_its_exit(self):
        r = self.toolbox().sh("exec 1>&- 2>&-; sleep 0.3; exit 3")
        self.assertEqual((r["exit_code"], r["status"]), (3, "failed"))

    def test_timeout_and_stop_still_apply_after_the_output_closes(self):
        started = time.monotonic()
        r = self.toolbox().sh("exec 1>&- 2>&-; sleep 30", timeout=1)
        self.assertEqual(r["status"], "timeout")
        self.assertLess(time.monotonic() - started, 4)
        control = TurnControl()
        tools = self.toolbox(control=control)
        threading.Timer(0.3, control.cancel).start()
        started = time.monotonic()
        r = tools.sh("exec 1>&- 2>&-; sleep 30")
        self.assertEqual(r["status"], "cancelled")
        self.assertLess(time.monotonic() - started, 4)


class _EndlessRipgrep:
    """A ripgrep that would print matches forever: grep must stop reading at its limit."""

    def __init__(self, *args, **kwargs):
        lines = (
            json.dumps(
                {"type": "match", "data": {"path": {"text": "big.txt"}, "lines": {"text": "x\n"}, "line_number": n}}
            ).encode()
            + b"\n"
            for n in itertools.count(1)
        )
        self.stdout = mock.MagicMock()
        self.stdout.__iter__.return_value = lines
        self.returncode: int | None = None

    def poll(self):
        return self.returncode

    def kill(self):
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


class GrepLimitTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"big.txt": "x\n"}

    def test_grep_stops_reading_at_the_result_limit(self):
        with (
            mock.patch("frond.agent.tools.shutil.which", return_value="/usr/bin/rg"),
            mock.patch("frond.agent.tools.subprocess.Popen", _EndlessRipgrep),
        ):
            result = self.toolbox().grep("x", max_results=5)
        self.assertEqual(len(result["items"]), 5)
        self.assertTrue(result["truncated"])

    def test_ripgrep_errors_still_surface(self):
        if shutil.which("rg") is None:
            self.skipTest("ripgrep is not installed")
        with self.assertRaises(ToolError):
            self.toolbox().grep("(unclosed")


class ReplayScriptTest(WorkspaceCase):
    def test_a_plain_json_list_of_steps_replays(self):
        script = self.root / "steps.json"
        script.write_text(json.dumps([{"reasoning": "Answer.", "code": "SUBMIT(response='listed')"}]))
        out = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "xdg"), "XDG_CACHE_HOME": str(self.root)}),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            code = cli.main(["-p", "--script", str(script), "-C", str(self.root), "hello"])
        self.assertEqual((code, out.getvalue().strip()), (0, "listed"))


class AttachmentAndSessionFileTest(WorkspaceCase):
    def test_mentions_read_no_more_than_the_attachment_cap(self):
        (self.root / "big.log").write_bytes(b"x" * 1_000_000)
        app = App(self.ws, model="m", sub_model="m")
        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("read the whole file")):
            found = app.mentions("look at @big.log")
        self.assertIn("truncated; file is 1,000,000 bytes", found["big.log"])
        self.assertLess(len(found["big.log"]), 201_000)

    def test_session_files_are_private_from_the_first_byte(self):
        store = SessionStore(self.root, base=self.root / "xdg")
        modes: list[int] = []
        real_replace = os.replace

        def spy(src, dst):
            modes.append(stat.S_IMODE(os.stat(src).st_mode))
            real_replace(src, dst)

        previous = os.umask(0o022)
        try:
            with mock.patch("frond.sessions.os.replace", side_effect=spy):
                store.save(store.new_path(), [TurnRecord(1, "hi")], "m")
        finally:
            os.umask(previous)
        self.assertEqual(modes, [0o600])
        self.assertEqual(stat.S_IMODE(store.directory.stat().st_mode), 0o700)


class QueuedTurnTest(WorkspaceCase):
    def test_the_next_turn_can_start_as_soon_as_the_last_one_reports_finished(self):
        steps = [Step("one", "SUBMIT(response='1')"), Step("two", "SUBMIT(response='2')")]
        agent, _ = scripted_agent(self, steps)
        finished = threading.Event()
        inner = agent._emit

        def emit(event):
            inner(event)
            if isinstance(event, TurnFinished) and not finished.is_set():
                finished.set()
                time.sleep(0.3)  # the turn's thread is still alive while the UI reacts to TurnFinished

        agent._emit = emit
        agent.start_turn("first")
        self.assertTrue(finished.wait(10))
        agent.start_turn("second")  # raised "a turn is already running" before the fix
        self.assertTrue(agent.wait(10))
        self.assertEqual([e.response for e in self.of_type(TurnFinished)], ["1", "2"])
