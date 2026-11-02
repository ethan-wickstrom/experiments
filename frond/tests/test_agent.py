"""The REPL interpreter and complete agent turns against a scripted model."""

import threading
import time
import unittest
from pathlib import Path
from typing import ClassVar

from dspy.primitives.code_interpreter import CodeExecutionError, FinalOutput

from frond.agent.control import TurnCancelled, TurnControl
from frond.agent.repl import ReplPool, ReplSession
from frond.agent.scripted import Step
from frond.agent.session import format_history
from frond.events import (
    CodeDelta,
    ExecFinished,
    FileChanged,
    ReasoningDelta,
    ResponseDelta,
    StepStarted,
    SubAgentFinished,
    SubQueryProgress,
    TurnFinished,
    UsageUpdated,
)
from tests.helpers import WorkspaceCase, scripted_agent


class ReplTest(unittest.TestCase):
    def setUp(self) -> None:
        self.control = TurnControl()
        self.output: list[str] = []
        self.session = ReplSession(Path.cwd(), control=self.control, on_output=self.output.append, timeout=3)
        self.addCleanup(self.session.shutdown)

        def add(a: int, b: int = 10) -> int:
            """Add two numbers."""
            return a + b

        self.session.tools["add"] = add
        self.session.output_fields = [{"name": "response", "type": "str"}]

    def test_state_persists_and_tools_take_positional_args(self):
        self.assertEqual(self.session.execute("x = add(1)\nprint('x', x)\nx * 2"), "x 11\n22\n")
        self.assertEqual(self.session.execute("print(x + add(1, 2))"), "14\n")

    def test_errors_keep_printed_output_and_syntax_errors_raise(self):
        with self.assertRaises(CodeExecutionError) as ctx:
            self.session.execute("print('before')\n1/0")
        self.assertIn("before", str(ctx.exception))
        self.assertIn("ZeroDivisionError", str(ctx.exception))
        with self.assertRaises(SyntaxError):
            self.session.execute("def broken(:")

    def test_submit_and_policy(self):
        self.assertEqual(self.session.execute("SUBMIT(response='ok')"), FinalOutput({"response": "ok"}))
        with self.assertRaisesRegex(CodeExecutionError, "sh\\(...\\)"):
            self.session.execute("import os; os.system('true')")
        with self.assertRaisesRegex(CodeExecutionError, "write\\(\\)"):
            self.session.execute("open('blocked.txt', 'w')")
        self.assertFalse(Path("blocked.txt").exists())

    def test_timeout_interrupts_but_keeps_state(self):
        with self.assertRaisesRegex(CodeExecutionError, "variables kept"):
            self.session.execute("kept = 1\nwhile True: pass")
        self.assertEqual(self.session.execute("print(kept)"), "1\n")

    def test_cancel_interrupts_and_streams_output(self):
        threading.Timer(0.4, self.control.cancel).start()
        with self.assertRaises(TurnCancelled):
            self.session.execute("import time\nfor i in range(50):\n    print(i)\n    time.sleep(0.05)")
        self.assertTrue(self.output)
        self.control.reset()
        self.assertEqual(self.session.execute("print('alive')"), "alive\n")

    def test_pool_leases_root_then_hands_out_fresh_workers(self):
        pool = ReplPool(Path.cwd(), self.control)
        self.addCleanup(pool.close)
        lease = pool()
        nested = pool()
        self.assertIsNot(nested, pool.root)
        self.assertIsInstance(nested, ReplSession)
        nested.shutdown()
        lease.shutdown()
        self.assertIs(type(pool()).__name__, "ReplLease")


class AgentTurnTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {"app.py": "def greet(name):\n    return 'hello ' + name\n"}

    def test_full_turn_streams_edits_and_answers(self):
        steps = [
            Step("Read it first.", "print(view('app.py'))"),
            Step(
                "Fix and verify.",
                "edit('app.py', \"'hello '\", \"'Hello, '\")\n"
                "print(sh('python3 -c \"import app; print(app.greet(1 and \\'x\\'))\"'))",
            ),
            Step("Done.", 'SUBMIT(response="""Capitalised the greeting in `app.py:2`.""")'),
        ]
        agent, _ = scripted_agent(self, steps)
        record = agent.run_turn("make the greeting nicer")
        self.assertEqual(record.status, "done")
        self.assertEqual(record.response, "Capitalised the greeting in `app.py:2`.")
        self.assertEqual(record.files, ["app.py"])
        self.assertIn("Hello, ", (self.root / "app.py").read_text())
        self.assertEqual([e.step for e in self.of_type(StepStarted)], [1, 2, 3])
        self.assertEqual("".join(e.text for e in self.of_type(ResponseDelta)), record.response)
        self.assertEqual("".join(e.text for e in self.of_type(ReasoningDelta) if e.step == 1), "Read it first.")
        self.assertTrue(any("view('app.py')" in e.text for e in self.of_type(CodeDelta)) or self.of_type(CodeDelta))
        self.assertEqual(self.of_type(FileChanged)[0].added, 1)
        usage = self.of_type(UsageUpdated)[-1]
        self.assertGreater(usage.prompt_tokens, 1000)
        self.assertEqual(usage.context_window, 100_000)
        self.assertIsInstance(self.of_type(TurnFinished)[-1], TurnFinished)

    def test_errors_are_shown_to_the_model_which_recovers(self):
        steps = [
            Step("Oops.", "print(undefined_name)"),
            Step("Recover.", "SUBMIT(response='recovered')"),
        ]
        agent, engine = scripted_agent(self, steps)
        record = agent.run_turn("go")
        self.assertEqual(record.response, "recovered")
        first = self.of_type(ExecFinished)[0]
        self.assertIn("NameError", first.error or "")
        second_prompt = engine.requests[1].messages[0].text or ""
        self.assertIn("NameError: name 'undefined_name' is not defined", second_prompt)

    def test_cancel_during_streaming(self):
        steps = [Step("A long thought. " * 40, "print('never runs')")]
        agent, _ = scripted_agent(self, steps, delay=0.01)
        agent.start_turn("go")
        time.sleep(0.3)
        agent.cancel()
        self.assertTrue(agent.wait(5))
        self.assertEqual(agent.history[-1].status, "cancelled")
        self.assertFalse(any(e.step == 1 for e in self.of_type(ExecFinished)))

    def test_step_limit_falls_back_to_extract(self):
        agent, _ = scripted_agent(self, [Step("Look around.", "print(1)")] * 3, max_steps=2)
        record = agent.run_turn("go")
        self.assertEqual(record.status, "limit")
        self.assertIn("ran out of steps", record.response)

    def test_subqueries_and_subagents(self):
        steps = [
            Step("Fan out.", "print(llm_query_batched(['a', 'b']))\nprint(subagent('find greet'))"),
            # the sub-agent consumes the next two steps (its own REPL loop)
            Step("Sub-agent looks.", "print(grep('greet'))"),
            Step("Sub-agent reports.", "SUBMIT(report='greet is defined in app.py:1')"),
            Step("Wrap up.", "SUBMIT(response='done')"),
        ]
        agent, _ = scripted_agent(self, steps, sub_answer=lambda prompt: "sub!")
        record = agent.run_turn("go")
        self.assertEqual(record.response, "done")
        progress = self.of_type(SubQueryProgress)
        self.assertEqual((progress[-1].total, progress[-1].done), (2, 2))
        finished = self.of_type(SubAgentFinished)
        self.assertEqual(finished[0].result, "greet is defined in app.py:1")
        self.assertIn("greet is defined in app.py:1", self.of_type(ExecFinished)[0].output)

    def test_history_carries_across_turns_and_repl_persists(self):
        steps = [
            Step("Remember.", "note = 'kept'\nSUBMIT(response='first answer')"),
            Step("Recall.", "SUBMIT(response=note + ' / ' + str(len(history) > 0))"),
        ]
        agent, engine = scripted_agent(self, steps)
        agent.run_turn("first")
        record = agent.run_turn("second")
        self.assertEqual(record.response, "kept / True")
        prompt = engine.requests[-1].messages[0].text or ""
        self.assertIn("first answer", prompt)
        self.assertIn("### turn 1 · user", format_history(agent.history))


if __name__ == "__main__":
    unittest.main()
