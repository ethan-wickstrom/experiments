"""The TUI driven headlessly: typing, sending, queueing, stopping, popups, commands, rendering at any size."""

import time
from typing import ClassVar

from frond.agent.scripted import Step
from frond.tui.app import App
from frond.tui.headless import Harness, to_html
from frond.tui.keys import Mouse
from frond.tui.text import str_width
from tests.helpers import WorkspaceCase, scripted_agent


class AppTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        "src/app.py": "def main():\n    return 1\n",
        "src/api.py": "ROUTES = []\n",
        "README.md": "# hi\n",
    }

    def make(self, steps: list[Step], *, delay: float = 0.0, width: int = 100, height: int = 30) -> Harness:
        app = App(self.ws, model="test/model", sub_model="test/model")
        agent, self.engine = scripted_agent(self, steps, delay=delay, approver=app.approver)
        agent._emit = app.emit  # route events to the app (the helper collected them in a list)
        agent.jobs.set_emit(agent.emit)
        app.attach(agent)
        self.app = app
        return Harness(app, width, height)

    def test_send_renders_reasoning_code_diff_and_answer(self):
        h = self.make(
            [
                Step("Let me change it.", "edit('src/app.py', 'return 1', 'return 2')"),
                Step("Done.", 'SUBMIT(response="""Changed `src/app.py` to return **2**.""")'),
            ]
        )
        h.type("change @src/app.py please\n")
        self.assertTrue(h.wait())
        screen = h.text()
        self.assertIn("▌ change @src/app.py please", screen)
        self.assertIn("⧉ src/app.py", screen)
        self.assertIn("Let me change it.", screen)
        self.assertIn("✎ src/app.py", screen)
        self.assertIn("+ ", screen)
        self.assertIn("◆ Changed src/app.py to return 2.", screen)
        self.assertIn("✓ done · 2 steps", screen)
        self.assertIn("⏎ send", screen)
        self.assertIn("return 2", (self.root / "src/app.py").read_text())

    def test_queue_and_stop(self):
        h = self.make(
            [
                Step("Slow work.", "import time\nfor i in range(100):\n    print(i)\n    time.sleep(0.05)"),
                Step("Second turn.", "SUBMIT(response='second done')"),
            ],
            delay=0.002,
        )
        h.type("first\n")
        self.assertTrue(h.wait(lambda: "■ stop" in h.text(), 10))
        h.type("second")
        h.key("tab")  # enter would steer the running turn; tab queues for after it
        self.assertEqual(self.app.queue, ["second"])
        self.assertIn("↳ queued", h.text())
        h.wait(lambda: any(getattr(b, "state", "") == "running" for b in self.app.blocks), 10)
        h.key("escape")
        self.assertTrue(h.wait(timeout=20))
        screen = h.text()
        self.assertIn("■ stopped", screen)
        self.assertIn("second done", screen)
        self.assertEqual(self.app.queue, [])

    def test_enter_steers_the_running_turn(self):
        h = self.make(
            [
                Step("Slow work.", "import time\ntime.sleep(0.6)\nprint('step one done')"),
                Step("Adjusting.", "SUBMIT(response='steered')"),
            ],
            delay=0.002,
        )
        h.type("first\n")
        self.assertTrue(h.wait(lambda: any(getattr(b, "state", "") == "running" for b in self.app.blocks), 10))
        self.assertIn("⏎ steer", h.text() if self.app.editor.text else (h.type("x"), h.text())[1])
        self.app.editor.clear()
        h.type("use tabs, not spaces\n")
        self.assertEqual(self.app.queue, [])
        self.assertIn("↪ sent to the running turn", h.text())
        self.assertTrue(h.wait(timeout=20))
        self.assertIn("↪ read before step 2", h.text())
        second = "\n".join(m.text or "" for m in self.engine.requests[1].messages)
        self.assertIn("sent while you were working", second)
        self.assertIn("use tabs, not spaces", second)

    def test_up_arrow_recalls_last_queued_message(self):
        h = self.make([Step("Slow.", "import time\ntime.sleep(2)\nSUBMIT(response='x')")], delay=0.002)
        h.type("first\n")
        h.wait(lambda: self.app.running, 5)
        h.type("oops typo")
        h.key("tab")
        self.assertEqual(self.app.queue, ["oops typo"])
        h.key("up")
        self.assertEqual(self.app.editor.text, "oops typo")
        self.assertEqual(self.app.queue, [])
        h.key("escape")
        h.wait(timeout=10)

    def test_mention_popup_completes_paths(self):
        h = self.make([])
        h.type("look at @src/ap")
        self.assertIsNotNone(self.app.popup)
        screen = h.text()
        self.assertIn("src/app.py", screen)
        self.assertIn("src/api.py", screen)
        h.key("down")
        h.key("tab")
        self.assertRegex(self.app.editor.text, r"^look at @src/ap[ip]\.py $")
        self.assertIsNone(self.app.popup)

    def test_slash_commands(self):
        h = self.make([])
        h.type("/he")
        self.assertIn("/help", h.text())
        h.key("enter")
        self.assertIn("ctrl+o", h.text())
        h.type("/details\n")
        self.assertTrue(self.app.details)
        h.key("o", ctrl=True)
        self.assertFalse(self.app.details)
        h.type("/model\n")
        self.assertIn("model test/model", h.text())
        h.type("/new\n")
        self.assertEqual(len(self.app.blocks), 1)

    def test_multiline_input_and_editing_keys(self):
        h = self.make([])
        h.type("line one")
        h.key("j", ctrl=True)
        h.type("line two\\")
        h.key("enter")  # a trailing backslash turns enter into a newline
        h.type("three")
        self.assertEqual(self.app.editor.text, "line one\nline two\nthree")
        h.key("w", ctrl=True)
        self.assertEqual(self.app.editor.text, "line one\nline two\n")
        h.key("c", ctrl=True)
        self.assertEqual(self.app.editor.text, "")
        h.send(b"\x1b[200~pasted\ttext\x1b[201~")
        self.assertEqual(self.app.editor.text, "pasted    text")

    def test_approval_prompt_round_trip(self):
        h = self.make(
            [
                Step("Clean up.", "print(sh('rm -rf build_dir'))"),
                Step("Report.", "SUBMIT(response='ok')"),
            ]
        )
        h.type("clean\n")
        self.assertTrue(h.wait(lambda: self.app.approval is not None, 10))
        self.assertIn("approval needed", h.text())
        h.key("y")
        self.assertTrue(h.wait())
        self.assertIn("$ rm -rf build_dir", h.text())

    def test_mouse_wheel_scroll_and_stop_button(self):
        h = self.make([Step("Slow.", "import time\ntime.sleep(5)")], delay=0.0, height=20)
        for i in range(30):
            self.app.command("help") if i % 10 == 0 else None
        h.frame()
        h.app.on_input(Mouse("wheel_up", 5, 5))
        self.assertGreater(self.app.scroll, 0)
        h.key("escape")
        self.assertEqual(self.app.scroll, 0)
        h.type("go\n")
        h.wait(lambda: self.app.running and "■ stop" in h.text(), 5)
        h.frame()
        button = next(hit for hit in self.app.hits if hit.kind == "button")
        started = time.monotonic()
        h.app.on_input(Mouse("press", button.x0 + 1, button.y0))
        self.assertTrue(h.wait(timeout=10))
        self.assertLess(time.monotonic() - started, 8)
        self.assertIn("■ stopped", h.text())

    def test_render_at_many_sizes_never_overflows(self):
        h = self.make(
            [
                Step(
                    "Edit a file and run something.",
                    "edit('src/app.py', 'return 1', 'return 1  # 界 wide chars')\n"
                    "print(sh('printf \"%s\\\\n\" one two three'))",
                ),
                Step(
                    "Done.",
                    'SUBMIT(response="""A **long** answer with `code` and a list:\n\n- item one\n- item two""")',
                ),
            ]
        )
        h.type("go\n")
        h.wait()
        for width, height in [(40, 12), (60, 20), (80, 24), (120, 40), (200, 50)]:
            h.width, h.height = width, height
            frame = h.frame()
            for row in frame.chars:
                self.assertLessEqual(str_width("".join(row)), width)
            self.assertIsNotNone(frame.cursor)
        self.assertIn("<pre>", to_html(h.frame(), self.app.theme))

    def test_undo_command_shows_reverted_diff(self):
        h = self.make([Step("Edit.", "edit('src/app.py', 'return 1', 'return 5')\nSUBMIT(response='ok')")])
        h.type("edit it\n")
        self.assertTrue(h.wait())
        self.assertIn("return 5", (self.root / "src/app.py").read_text())
        h.type("/undo\n")
        h.pump()
        screen = h.text()
        self.assertIn("↶ Reverted the file changes of turn 1: src/app.py", screen)
        self.assertIn("✎ src/app.py", screen)
        self.assertIn("return 1", (self.root / "src/app.py").read_text())

    def test_diff_command_shows_the_turns_net_change(self):
        h = self.make([Step("Edit.", "edit('src/app.py', 'return 1', 'return 5')\nSUBMIT(response='ok')")])
        h.type("edit it\n")
        self.assertTrue(h.wait())
        h.type("/diff\n")
        h.pump()
        screen = h.text()
        self.assertIn("Δ The last turn's net change: 1 path", screen)
        self.assertIn("✎ src/app.py", screen)
