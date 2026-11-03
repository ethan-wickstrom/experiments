"""Messages sent into a running turn: delivered at the next step boundary, kept verbatim, handed back if unread."""

from __future__ import annotations

import threading
import time

from dspy.primitives.repl_types import REPLEntry, REPLHistory

from frond.agent.adapter import FrondAdapter, last_reply_index
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import STEER_CODE, FrondRLM, Hooks
from frond.agent.scripted import Step
from frond.agent.session import format_history, history_preview
from frond.events import SteerDelivered, SteersReturned
from tests.helpers import WorkspaceCase, scripted_agent


class SteeringTest(WorkspaceCase):
    def test_a_message_sent_mid_turn_reaches_the_next_step(self):
        steps = [
            Step("Working.", "import time\ntime.sleep(0.5)\nprint('one')"),
            Step("Adjusting.", "SUBMIT(response='done')"),
        ]
        agent, engine = scripted_agent(self, steps)
        self.assertFalse(agent.steer("too early"))  # no turn is running
        agent.start_turn("refactor the parser")
        deadline = time.monotonic() + 5
        while not engine.requests and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(agent.steer("keep the public API unchanged"))
        self.assertTrue(agent.wait(10))
        [delivered] = self.of_type(SteerDelivered)
        self.assertEqual((delivered.text, delivered.step), ("keep the public API unchanged", 2))
        record = agent.history[-1]
        self.assertEqual(record.steers, ["keep the public API unchanged"])
        second = "\n".join(m.text or "" for m in engine.requests[1].messages)
        self.assertIn("newer than everything above", second)
        self.assertIn("keep the public API unchanged", second)
        kinds = [(r.kind, r.output) for r in agent.steps.records() if r.kind == "user"]
        self.assertEqual(kinds, [("user", "refactor the parser"), ("user", "keep the public API unchanged")])
        self.assertIn("(while frond worked)\nkeep the public API unchanged", format_history(agent.history))
        preview = history_preview(agent.history, format_history(agent.history), 12_000) or ""
        self.assertIn("[turn 1, while frond worked] keep the public API unchanged", preview)

    def test_a_message_the_turn_never_reads_is_handed_back(self):
        gate = threading.Event()
        steps = [Step("Last step.", "SUBMIT(response='done')")]
        agent, _ = scripted_agent(self, steps)
        inner = agent.emit

        def emit(event):
            inner(event)
            if type(event).__name__ == "StepPlanned":  # the only step is underway: no boundary follows
                agent.steer("one more thing")
                gate.set()

        agent.emit = emit  # ty: ignore[invalid-assignment]
        agent.run_turn("go")
        self.assertTrue(gate.is_set())
        [returned] = self.of_type(SteersReturned)
        self.assertEqual(returned.texts, ("one more thing",))
        self.assertEqual(agent.history[-1].steers, [])
        self.assertFalse(agent.steer("after the turn"))


class SteeringLayoutTest(WorkspaceCase):
    def test_messages_join_the_user_message_before_them(self):
        rlm = FrondRLM(CodingTurn)
        signature = rlm._action_signature_for_current_factory(None, "")
        adapter = FrondAdapter()
        early = REPLHistory(entries=[REPLEntry(reasoning="", code=STEER_CODE, output="also add tests")])
        inputs = {"variables_info": ["v"], "repl_history": early, "iteration": "1/10", "repl_variables": "(none yet)"}
        messages = adapter.format(signature, [], inputs)
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertIn("You have not interacted with the REPL environment yet.", messages[1]["content"])
        self.assertIn("also add tests", messages[1]["content"])
        self.assertIsNone(last_reply_index([], early))
        later = REPLHistory(
            entries=[
                REPLEntry(reasoning="r1", code="print(1)", output="1"),
                REPLEntry(reasoning="", code=STEER_CODE, output="use tabs"),
                REPLEntry(reasoning="r2", code="print(2)", output="2"),
            ]
        )
        messages = adapter.format(signature, [], {**inputs, "repl_history": later})
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user", "assistant", "user"])
        self.assertIn("use tabs", messages[3]["content"])
        self.assertIn("What the user has said during this turn, oldest first", messages[-1]["content"])
        self.assertIn("- use tabs", messages[-1]["content"])
        self.assertTrue(messages[-1]["content"].rstrip().endswith("`[[ ## completed ## ]]`."))
        self.assertEqual(last_reply_index([], later), 3)

    def test_folding_keeps_the_users_words_verbatim(self):
        class TinyBudget(Hooks):
            def history_budget(self) -> int:
                return 2000

        rlm = FrondRLM(CodingTurn, hooks=TinyBudget(), keep_recent=1)
        words = "never edit generated files;\nrun make check before finishing"
        entries = [
            REPLEntry(reasoning="a", code="print(1)", output="x" * 900),
            REPLEntry(reasoning="", code=STEER_CODE, output=words),
            REPLEntry(reasoning="b", code="print(2)", output="y" * 900),
            REPLEntry(reasoning="c", code="print(3)", output="z" * 900),
        ]
        folded = rlm._fold(REPLHistory(entries=entries))
        self.assertIn(
            "the user wrote, during the turn: never edit generated files;\n  run make check", folded.entries[0].output
        )
