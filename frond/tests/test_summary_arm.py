"""The summary context policy (B10, H4): past the budget, early steps become an LLM summary, with no index and no
way back to them; the fold keeps the index and the history tools. The policy holds for every loop of the arm, and
both policies keep the user's own words verbatim (D38)."""

from __future__ import annotations

import unittest

from dspy.primitives.repl_types import REPLEntry, REPLHistory

from frond.agent.adapter import STEER_CODE, UserEntry
from frond.agent.prompts import CodingTurn
from frond.agent.rlm import INDEX_MARK, NOTE_CODE, SUMMARY_HEAD, FoldEntry, FrondRLM, Hooks, LoggedEntry
from frond.agent.scripted import Step
from frond.events import SubAgentFinished
from tests.helpers import WorkspaceCase, scripted_agent

SUMMARY = "The agent printed four blocks of x."
PROBE = "str('history_search' in globals())"  # can this loop search the step log?


def summariser(prompt: str) -> str:
    if "[[ ## transcript ## ]]" in prompt:
        return f"[[ ## summary ## ]]\n{SUMMARY}\n\n[[ ## completed ## ]]\n"
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
        self.assertIn(f"{SUMMARY_HEAD}{SUMMARY}", last)
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


class EveryLoopTest(WorkspaceCase):
    """Sub-agents and FORK branches follow the arm's policy too (Devin, PR #17), or the summary arm could recover
    the steps it summarised by delegating."""

    def probes(self, context: str) -> list[str]:
        steps = [
            Step("Delegate.", "print(subagent('look around'))"),
            Step("The sub-agent probes.", f"SUBMIT(report={PROBE})"),
            Step("Branch.", "FORK(['one', 'two'], steps=1)"),
            Step("Branch one probes.", f"SUBMIT(response={PROBE})"),
            Step("Branch two.", "SUBMIT(response='two')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, _ = scripted_agent(self, steps, max_steps=8, context=context, fork=2)
        agent.run_turn("go")
        return [e.result for e in self.of_type(SubAgentFinished)][:2]  # the sub-agent's, then branch one's

    def test_under_the_summary_policy_no_loop_can_search_the_step_log(self):
        self.assertEqual(self.probes("summary"), ["False", "False"])

    def test_under_the_fold_every_loop_can(self):
        self.assertEqual(self.probes("fold"), ["True", "True"])

    def test_a_branch_past_the_budget_is_summarised_by_the_model(self):
        steps = [
            Step("Branch.", "FORK(['long', 'short'], steps=6)"),
            *[Step(f"Print block {i}.", "print('x' * 3000)") for i in range(5)],
            Step("Long done.", "SUBMIT(response='long')"),
            Step("Short.", "SUBMIT(response='short')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = scripted_agent(self, steps, sub_answer=summariser, max_steps=8, context="summary", fork=2)
        agent.window = 4_000  # the main line stays under the budget; the long branch passes it
        agent.run_turn("go")
        texts = ["\n".join(m.text or "" for m in r.messages or []) for r in engine.requests]
        summaries = [i for i, text in enumerate(texts) if "## transcript ##" in text]
        self.assertTrue(summaries)
        self.assertEqual({agent.metrics.branch_calls.get(i) for i in summaries}, {"branch1"})  # priced as its own
        later = [texts[i] for i, scope in agent.metrics.branch_calls.items() if scope == "branch1" and i > summaries[0]]
        self.assertTrue(any(f"{SUMMARY_HEAD}{SUMMARY}" in t for t in later))  # the model's summary, not a trace
        self.assertEqual(agent.metrics.summaries, len(summaries))
        self.assertEqual(agent.metrics.compactions, len(summaries))


class Summariser(Hooks):
    def __init__(self, summary: str | None) -> None:
        self.summary = summary
        self.transcripts: list[str] = []

    def history_budget(self) -> int:
        return 1500

    def summarize(self, transcript: str) -> str | None:
        self.transcripts.append(transcript)
        return self.summary


def entries() -> list[REPLEntry]:
    return [
        FoldEntry(reasoning="(summarised)", code=NOTE_CODE, output=f"{SUMMARY_HEAD}The agent fixed parse() first."),
        LoggedEntry(reasoning="look", code="print(1)", output="x" * 900, seq=4, step=3),
        UserEntry(reasoning="", code=STEER_CODE, output="do not touch generated files"),
        LoggedEntry(reasoning="edit", code="print(2)", output="y" * 900, seq=6, step=4),
        LoggedEntry(reasoning="test", code="print(3)", output="z" * 900, seq=7, step=5),
        LoggedEntry(reasoning="check", code="print(4)", output="w" * 900, seq=8, step=6),
    ]


class SummaryCompactionTest(unittest.TestCase):
    def compact(self, summary: str | None, history: list[REPLEntry]) -> tuple[REPLHistory, Summariser]:
        hooks = Summariser(summary)
        rlm = FrondRLM(CodingTurn, hooks=hooks, keep_recent=2, context="summary")
        return rlm._fold(REPLHistory(entries=history)), hooks

    def test_the_users_words_stay_verbatim_ahead_of_the_summary(self):
        compacted, hooks = self.compact("Then it edited and tested.", entries())
        user, note, *recent = compacted.entries
        self.assertIsInstance(user, UserEntry)
        self.assertEqual(user.output, "do not touch generated files")
        self.assertEqual(note.output, f"{SUMMARY_HEAD}Then it edited and tested.")
        self.assertEqual(len(recent), 2)
        [transcript] = hooks.transcripts
        self.assertIn("Summary of even earlier steps:\nThe agent fixed parse() first.", transcript)
        self.assertIn("The user wrote, during the turn:\ndo not touch generated files", transcript)

    def test_a_failed_summary_keeps_the_users_words_and_the_earlier_summary(self):
        compacted, _ = self.compact(None, entries())
        user, note, *_ = compacted.entries
        self.assertEqual(user.output, "do not touch generated files")
        self.assertTrue(note.output.startswith(f"{SUMMARY_HEAD}The agent fixed parse() first.\n\n"))
        self.assertIn("seq 4", note.output)  # and a clipped trace of the steps since
        self.assertNotIn("seq 7", note.output)  # the recent steps stay whole

    def test_with_only_notes_and_the_users_words_left_nothing_is_compacted_again(self):
        history: list[REPLEntry] = [
            UserEntry(reasoning="", code=STEER_CODE, output="u" * 2000),
            FoldEntry(reasoning="(summarised)", code=NOTE_CODE, output=f"{SUMMARY_HEAD}Earlier work."),
            LoggedEntry(reasoning="a", code="print(1)", output="a" * 50, seq=9, step=7),
            LoggedEntry(reasoning="b", code="print(2)", output="b" * 50, seq=10, step=8),
        ]
        compacted, hooks = self.compact("never asked", history)
        self.assertEqual(list(compacted.entries), history)
        self.assertEqual(hooks.transcripts, [])


if __name__ == "__main__":
    unittest.main()
