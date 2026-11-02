"""Regression tests for bugs found in review: patch fidelity, undo ordering, symlinks, approvals, compaction."""

import os
import threading
import time
from typing import ClassVar

from dspy.primitives.repl_types import REPLEntry, REPLHistory

from frond.agent.checkpoints import Checkpoints
from frond.agent.patch import apply_chunks, parse_patch
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import NOTE_CODE, FrondRLM, Hooks
from frond.agent.tools import ToolError
from frond.tui.app import App, ApprovalRequest
from tests.helpers import WorkspaceCase


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
        tools.checkpoints = checkpoints = Checkpoints()
        checkpoints.begin(1)
        tools.move("a", "b")
        tools.edit("b/x.py", "orig", "edited")
        result = checkpoints.undo()
        assert result is not None
        self.assertEqual((self.root / "a/x.py").read_text(), "orig\n")
        self.assertFalse((self.root / "b").exists())
        self.assertEqual([r.moved_from.name for r in result[1] if r.moved_from], ["b"])

    def test_delete_removes_symlinks_not_their_targets_and_undo_restores_them(self):
        os.symlink("target", self.root / "dir_link")
        os.symlink("nowhere", self.root / "dangling")
        tools = self.toolbox()
        tools.checkpoints = checkpoints = Checkpoints()
        checkpoints.begin(1)
        self.assertIn("symbolic link", tools.delete("dir_link"))
        self.assertIn("symbolic link", tools.delete("dangling"))
        self.assertTrue((self.root / "target/inside.txt").exists())
        self.assertFalse(os.path.lexists(self.root / "dangling"))
        checkpoints.undo()
        self.assertEqual(os.readlink(self.root / "dir_link"), "target")
        self.assertEqual(os.readlink(self.root / "dangling"), "nowhere")


class _StubAgent:
    """Just enough of the agent for the app to stop a turn."""

    def start_turn(self, request: str, attachments: dict[str, str] | None = None) -> None: ...
    def cancel(self) -> None: ...
    def undo(self) -> str:
        return ""

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


class CompactionKeepsSummariesTest(WorkspaceCase):
    def test_earlier_summary_survives_a_second_compaction(self):
        class TinyBudget(Hooks):
            def history_budget(self) -> int:
                return 3000

        rlm = FrondRLM(CodingTurn, hooks=TinyBudget(), keep_recent=2)
        summary = "IMPORTANT FACT: edited src/app.py:42. " * 60  # ~2.3k chars, longer than any clip
        entries = [REPLEntry(reasoning="(compacted)", code=NOTE_CODE, output=summary)]
        entries += [REPLEntry(reasoning=f"step {i}", code=f"print({i})", output="x" * 900) for i in range(6)]
        compacted = rlm._compact(REPLHistory(entries=entries))
        note = compacted.entries[0]
        self.assertEqual(note.code, NOTE_CODE)
        self.assertIn(summary.strip(), note.output)
