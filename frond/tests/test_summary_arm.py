"""The summary context policy (B10, H4): past the budget, early steps become an LLM summary, with no index and no
way back to them; the fold keeps the index and the history tools."""

from __future__ import annotations

import unittest

from frond.agent.rlm import INDEX_MARK
from frond.agent.scripted import Step
from tests.helpers import WorkspaceCase, scripted_agent


def summariser(prompt: str) -> str:
    if "[[ ## transcript ## ]]" in prompt:
        return "[[ ## summary ## ]]\nThe agent printed four blocks of x.\n\n[[ ## completed ## ]]\n"
    return "OK"


def long_turn() -> list[Step]:
    return [Step(f"Print block {i}.", "print('x' * 3000)") for i in range(6)] + [Step("Done.", "SUBMIT(response='ok')")]


class SummaryArmTest(WorkspaceCase):
    def run_turn(self, context: str):
        agent, engine = scripted_agent(self, long_turn(), sub_answer=summariser, max_steps=10, context=context)
        agent.window = 4_000  # a budget of about 6,500 characters: the turn passes it
        agent.run_turn("print blocks")
        prompts = ["\n".join(m.text or "" for m in r.messages) for r in engine.requests if r.messages]
        system = engine.requests[0].system or ""
        system = system if isinstance(system, str) else "".join(getattr(p, "text", "") for p in system)
        return agent, prompts, system

    def test_summary_replaces_early_steps_with_no_way_back(self):
        agent, prompts, system = self.run_turn("summary")
        last = prompts[-1]
        self.assertIn("Summary of the earlier steps of this turn:\nThe agent printed four blocks of x.", last)
        self.assertNotIn(INDEX_MARK, last)
        self.assertNotIn("history_search", system)
        self.assertGreaterEqual(agent.metrics.summaries, 1)
        self.assertGreaterEqual(agent.metrics.compactions, 1)

    def test_the_fold_keeps_an_index_and_the_history_tools(self):
        agent, prompts, system = self.run_turn("fold")
        self.assertIn(INDEX_MARK, prompts[-1])
        self.assertIn("history_search", system)
        self.assertEqual(agent.metrics.summaries, 0)
        self.assertGreaterEqual(agent.metrics.compactions, 1)


if __name__ == "__main__":
    unittest.main()
