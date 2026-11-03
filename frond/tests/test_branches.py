"""FORK (B7, H2): branches start from the world and REPL at FORK, a check scores each, and the winner is kept."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest import mock

from frond.agent.scripted import Step
from frond.cli import export_run
from frond.events import SubAgentFinished, SubAgentStarted
from tests.helpers import WorkspaceCase, scripted_agent

CHECK = "check.py"  # passes when answer.txt holds "b"


class ForkTest(WorkspaceCase):
    files: ClassVar[dict[str, str]] = {
        CHECK: "import sys\nsys.exit(0 if open('answer.txt').read() == 'b' else 1)\n",
        "notes.txt": "start\n",
    }

    def agent(self, steps: list[Step], *, branches: int = 3):
        agent, engine = scripted_agent(self, steps, max_steps=12)
        agent.config.fork = branches
        agent.rlm.max_branches = branches
        agent.pool.root.max_branches = branches
        return agent, engine

    def test_the_branch_whose_check_passes_is_kept(self):
        steps = [
            Step(
                "Try three ways.",
                "v = 7\nFORK(['answer a', 'answer b', 'answer c'], check='python3 check.py', steps=2)",
            ),
            Step("A.", "write('answer.txt', 'a')\nSUBMIT(response='wrote a')"),
            Step("B.", "write('answer.txt', 'b')\nw = 1\nSUBMIT(response=f'wrote b; v was {v}')"),
            Step("C.", "write('answer.txt', 'c')\nSUBMIT(response='wrote c')"),
            Step("Done.", "SUBMIT(response=open('answer.txt').read() + str('w' in globals()))"),
        ]
        agent, engine = self.agent(steps)
        record = agent.run_turn("pick the right answer")
        self.assertEqual(record.response, "bFalse")  # b's world is kept; b's REPL was a copy
        self.assertEqual((self.root / "answer.txt").read_text(), "b")
        self.assertEqual(record.files, ["answer.txt"])
        final_prompt = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("FORK explored 3 options (check: python3 check.py)", final_prompt)
        self.assertIn(
            "option 2 ('answer b'): passed; submitted after 1 step(s). Its report: wrote b; v was 7", final_prompt
        )
        self.assertIn("Kept option 2. The workspace holds its changes (answer.txt)", final_prompt)
        self.assertEqual([e.ok for e in self.of_type(SubAgentFinished)], [False, True, False])
        self.assertEqual(len(self.of_type(SubAgentStarted)), 3)
        scopes = {r.agent for r in agent.steps.records() if r.agent}
        self.assertEqual(len(scopes), 3)  # every branch's steps are in the step log
        out = Path(tempfile.mkdtemp(prefix="frond-export-"))
        self.addCleanup(shutil.rmtree, out, True)
        export_run(agent, out)
        roles = [json.loads(line)["role"] for line in (out / "calls.jsonl").read_text().splitlines()]
        self.assertEqual([r for r in roles if r != "main"], sorted(scopes))  # one call per branch, tagged
        forks = json.loads((out / "metrics.json").read_text())["forks"]
        self.assertEqual([(b["passed"], b["kept"]) for b in forks[0]], [(False, False), (True, True), (False, False)])

    def test_each_branch_starts_from_the_world_at_fork_and_no_pass_keeps_it(self):
        steps = [
            Step("Try.", "FORK(['first', 'second'], check='python3 check.py', steps=1)"),
            Step("First.", "write('answer.txt', 'x')\nedit('notes.txt', 'start', 'first')\nSUBMIT(response='x')"),
            Step("Second.", "import os\nSUBMIT(response=str(os.path.exists('answer.txt')) + open('notes.txt').read())"),
            Step("Done.", "SUBMIT(response='done')"),
        ]
        agent, engine = self.agent(steps, branches=2)
        agent.run_turn("try")
        final_prompt = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("Its report: Falsestart", final_prompt)  # the second branch never saw the first one's changes
        self.assertIn("No branch passed, so the workspace is as it was at FORK", final_prompt)
        self.assertFalse((self.root / "answer.txt").exists())
        self.assertEqual((self.root / "notes.txt").read_text(), "start\n")

    def test_branches_share_the_prompt_prefix_through_the_fork_step(self):
        steps = [
            Step("Look.", "print('looked')"),
            Step("Try.", "FORK(['one', 'two'], steps=1)"),
            Step("One.", "SUBMIT(response='one')"),
            Step("Two.", "SUBMIT(response='two')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = self.agent(steps, branches=2)
        agent.run_turn("go")
        main, one, two = (engine.requests[i].messages for i in (1, 2, 3))
        self.assertEqual([m.text for m in one[: len(main)]], [m.text for m in main[:-1]] + [one[len(main) - 1].text])
        self.assertEqual([m.text for m in one[:-1]], [m.text for m in two[:-1]])  # differ only in their own note
        self.assertIn("You are branch 1 of 2", one[-1].text or "")
        self.assertIn("You are branch 2 of 2", two[-1].text or "")

    def test_a_fork_whose_snapshot_fails_changes_nothing(self):  # review of #25
        steps = [
            Step("Try.", "FORK(['a', 'b'], check='python3 check.py', steps=1)"),
            Step("Done.", "SUBMIT(response='done')"),
        ]
        agent, engine = self.agent(steps, branches=2)
        assert agent.timeline is not None
        with mock.patch.object(agent.timeline, "snapshot", return_value=""):
            agent.run_turn("try")
        final_prompt = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("FORK needs workspace snapshots, which stopped", final_prompt)
        self.assertEqual((self.root / "notes.txt").read_text(), "start\n")
        self.assertTrue((self.root / CHECK).exists())

    def test_with_fork_off_there_is_no_fork(self):
        steps = [Step("Try.", "FORK(['a', 'b'])"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = self.agent(steps, branches=1)
        agent.run_turn("go")
        prompts = ["\n".join(m.text or "" for m in r.messages) for r in engine.requests]
        self.assertIn("NameError", prompts[1])
        self.assertTrue(all("Branching\n" not in p for p in prompts))

    def test_more_options_than_allowed_is_an_error_the_model_sees(self):
        steps = [Step("Try.", "FORK(['a', 'b', 'c'])"), Step("Done.", "SUBMIT(response='ok')")]
        agent, engine = self.agent(steps, branches=2)
        agent.run_turn("go")
        self.assertIn("FORK takes 2 to 2 options; got 3", "\n".join(m.text or "" for m in engine.requests[1].messages))


if __name__ == "__main__":
    unittest.main()
