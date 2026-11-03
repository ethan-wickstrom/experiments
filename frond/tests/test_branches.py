"""FORK (B7, H2): branches start from the world and REPL at FORK, a check scores each, and the winner is kept."""

from __future__ import annotations

import json
import shutil
import subprocess
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

    def test_git_state_is_reset_between_branches_and_the_kept_ones_stays(self):  # Devin, #15 (F26)
        git = "git -c user.name=t -c user.email=t@example.com"
        subprocess.run(f"git init -q && {git} add -A && {git} commit -qm start", shell=True, cwd=self.root, check=True)
        steps = [
            Step("Branch.", "FORK(['commit a', 'commit b'], check='python3 check.py', steps=2)"),
            Step(
                "A.",
                f"write('answer.txt', 'a')\nsh({git!r} + ' add -A && ' + {git!r} + ' commit -qm a')\n"
                "SUBMIT(response='a')",
            ),
            Step(
                "B.",
                "seen = sh('git log --format=%s').output.split()\nwrite('answer.txt', 'b')\n"
                f"sh({git!r} + ' add -A && ' + {git!r} + ' commit -qm b')\nSUBMIT(response=' '.join(seen))",
            ),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = self.agent(steps)
        agent.run_turn("go")
        last = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("Its report: start", last)  # B started from the commit at FORK, not A's
        log = subprocess.run(["git", "log", "--format=%s"], cwd=self.root, capture_output=True, text=True).stdout
        self.assertEqual(log.split(), ["b", "start"])  # the kept branch's commit, on the branch it was made on
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(status.stdout, "")  # index and tree agree

    def test_files_too_large_for_the_store_are_restored_between_branches(self):  # Devin, #15 (F27)
        (self.root / "data.bin").write_bytes(b"0" * 4000)
        steps = [
            Step("Branch.", "FORK(['a', 'b', 'c'], check='python3 check.py', steps=1)"),
            Step("A.", "write('answer.txt', 'a')\nsh('printf changed > data.bin')\nSUBMIT(response='a')"),
            Step(
                "B.",
                "write('answer.txt', 'b')\nn = len(open('data.bin').read())\n"
                "sh('head -c 5000 /dev/zero > big.bin')\nSUBMIT(response=f'saw {n}')",
            ),
            Step("C.", "write('answer.txt', 'c')\nsh('rm big.bin; printf c > data.bin')\nSUBMIT(response='c')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, engine = self.agent(steps)
        assert agent.timeline is not None
        agent.timeline.work.max_blob = 1000  # so these files are "large": kept by signature only
        record = agent.run_turn("go")
        self.assertEqual(record.response, "ok")
        last = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("Its report: saw 4000", last)  # B saw data.bin as it was at FORK, after A changed it
        self.assertEqual((self.root / "data.bin").read_bytes(), b"0" * 4000)
        self.assertEqual((self.root / "big.bin").stat().st_size, 5000)  # B's large file, though C ran after it
        self.assertEqual((self.root / "answer.txt").read_text(), "b")
        self.assertEqual(agent.timeline.work.kept_large, {})  # the copies are gone

    def test_the_main_lines_jobs_are_paused_while_branches_run(self):  # Devin, #15 (F28)
        steps = [
            Step("Start a job.", "print(sh('while true; do echo x >> ticks.log; sleep 0.05; done', background=True))"),
            Step("Branch.", "import time\ntime.sleep(0.3)\nFORK(['a', 'b'], steps=1)"),
            Step(
                "A.",
                "import os, time\nn = os.path.getsize('ticks.log')\ntime.sleep(0.5)\n"
                "SUBMIT(response=str(os.path.getsize('ticks.log') - n))",
            ),
            Step("B.", "SUBMIT(response='b')"),
            Step(
                "Done.",
                "import os, time\nn = os.path.getsize('ticks.log')\ntime.sleep(0.5)\n"
                "SUBMIT(response=str(os.path.getsize('ticks.log') > n))",
            ),
        ]
        agent, engine = self.agent(steps)
        record = agent.run_turn("go")
        self.assertEqual(record.response, "True")  # resumed after FORK
        last = "\n".join(m.text or "" for m in engine.requests[-1].messages)
        self.assertIn("Its report: 0", last)  # no writes while option a ran
        self.assertIn("1 background job(s) of yours were paused while the branches ran, and resumed", last)

    def test_a_branch_can_start_jobs_and_is_told_it_cannot_fork(self):  # Devin, #15 (F29, F31)
        steps = [
            Step("Branch.", "FORK(['one', 'two'], steps=2)"),
            Step("One starts a job.", "print(sh('sleep 5', background=True))"),
            Step("One forks.", "FORK(['deeper', 'wider'], steps=1)"),
            Step("Two.", "SUBMIT(response='two')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        agent, _ = self.agent(steps)
        record = agent.run_turn("go")
        self.assertEqual(record.response, "ok")
        outputs = [r.output for r in agent.steps.records() if r.agent and r.kind == "step"]
        self.assertRegex(outputs[0], r"job \d+ \(pid \d+\) running")  # its log directory exists (F29)
        self.assertIn("FORK is not available inside a branch", outputs[1])  # the host's refusal, no NameError (F31)

    def test_a_branchs_sub_model_calls_are_billed_to_the_branch(self):  # Devin, #15 (F30)
        from frond.agent.scripted import ScriptedEngine, scripted_lm
        from frond.agent.session import Agent

        steps = [
            Step("Branch.", "FORK(['one', 'two'], steps=1)"),
            Step("One asks.", "print(llm_query('hi'))"),
            Step("Two.", "SUBMIT(response='two')"),
            Step("Done.", "SUBMIT(response='ok')"),
        ]
        main = scripted_lm(ScriptedEngine(steps))
        sub = scripted_lm(ScriptedEngine([], sub_answer=lambda prompt: "hello"))
        reference, _ = scripted_agent(self, [], max_steps=12)
        agent = Agent(reference.config, self.ws, self.events.append, lm=main, sub_lm=sub)
        self.addCleanup(agent.close)
        agent.config.fork = agent.rlm.max_branches = agent.pool.root.max_branches = 2
        agent.run_turn("go")
        self.assertEqual(len(sub.history), 1)
        self.assertEqual(set(agent.metrics.sub_branch_calls), {0})
        self.assertTrue(agent.metrics.sub_branch_calls[0].startswith("branch"))

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
