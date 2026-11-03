"""The research bench: statistics, specs, the matrix runner's plan, and the analysis of Harbor jobs (ledger B3)."""

from __future__ import annotations

import itertools
import json
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from statistics import fmean
from unittest import mock

from bench import analyze, matrix, spec
from bench.stats import betting_cs, bootstrap_interval, difference_cs, holm, midranks, wilcoxon


def brute_force_wilcoxon(diffs: list[float]) -> tuple[float, float]:
    """P(W+ >= observed) and P(W+ <= observed) by enumerating every sign assignment (the definition)."""
    d = [x for x in diffs if x != 0]
    ranks = midranks([abs(x) for x in d])
    observed = sum(r for r, x in zip(ranks, d, strict=True) if x > 0)
    signs = itertools.product((0, 1), repeat=len(d))
    sums = [sum(r for r, positive in zip(ranks, s, strict=True) if positive) for s in signs]
    return (
        sum(s >= observed - 1e-9 for s in sums) / len(sums),
        sum(s <= observed + 1e-9 for s in sums) / len(sums),
    )


class WilcoxonTest(unittest.TestCase):
    def test_a_textbook_case(self):
        statistic, p, n = wilcoxon([1, 2, 3, 4, 5])
        self.assertEqual((statistic, n), (15.0, 5))
        self.assertAlmostEqual(p, 2 / 32)
        self.assertAlmostEqual(wilcoxon([1, 2, 3, 4, 5], "greater")[1], 1 / 32)

    def test_ties_and_zeros_match_enumeration(self):
        rng = random.Random(3)
        for _ in range(30):
            diffs = [rng.choice([-1, -2 / 3, -1 / 3, 0, 1 / 3, 2 / 3, 1]) for _ in range(rng.randint(1, 12))]
            greater, less = brute_force_wilcoxon([round(x, 9) for x in diffs])
            self.assertAlmostEqual(wilcoxon(diffs, "greater")[1], greater)
            self.assertAlmostEqual(wilcoxon(diffs, "less")[1], less)

    def test_float_noise_does_not_break_ties(self):
        self.assertEqual(wilcoxon([2 / 3 - 1 / 3, 1 - 2 / 3]), wilcoxon([1 / 3, 1 / 3]))

    def test_all_zero_differences_give_no_evidence(self):
        self.assertEqual(wilcoxon([0, 0, 0]), (0.0, 1.0, 0))


class IntervalTest(unittest.TestCase):
    def test_holm_steps_down(self):
        adjusted = holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adjusted["a"], 0.03)
        self.assertAlmostEqual(adjusted["c"], 0.06)
        self.assertAlmostEqual(adjusted["b"], 0.06)

    def test_bootstrap_of_a_constant_is_that_constant(self):
        self.assertEqual(bootstrap_interval([0.4] * 20, fmean), (0.4, 0.4))
        low, high = bootstrap_interval([0.0, 1.0] * 30, fmean, seed=1)
        self.assertTrue(0.3 < low < 0.5 < high < 0.7, (low, high))


class ConfidenceSequenceTest(unittest.TestCase):
    def test_the_true_mean_stays_inside_at_every_step_in_most_runs(self):
        rng = random.Random(7)
        alpha, runs, misses = 0.2, 60, 0
        for _ in range(runs):
            xs = [1.0 if rng.random() < 0.3 else 0.0 for _ in range(66)]
            if any(not lo <= 0.3 <= hi for lo, hi in betting_cs(xs, alpha=alpha, grid=200)):
                misses += 1
        self.assertLessEqual(misses / runs, alpha)

    def test_intervals_nest_and_shrink(self):
        rng = random.Random(1)
        sequence = betting_cs([rng.random() for _ in range(66)], alpha=0.05, grid=200)
        for (lo1, hi1), (lo2, hi2) in itertools.pairwise(sequence):
            self.assertTrue(lo1 <= lo2 and hi2 <= hi1)
        self.assertLess(sequence[-1][1] - sequence[-1][0], 0.5 * (sequence[0][1] - sequence[0][0]))

    def test_a_clear_difference_is_decided(self):
        final = difference_cs([1.0] * 30 + [0.0] * 6, alpha=0.05, grid=200)[-1]
        self.assertGreater(final[0], 0.2)

    def test_observations_outside_the_unit_interval_are_refused(self):
        with self.assertRaises(ValueError):
            betting_cs([1.5])


class BenchCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="frond-bench-"))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write_spec(self, body: str) -> Path:
        path = self.dir / "spec.toml"
        path.write_text(body)
        return path


SPEC = """
id = "T1"
title = "treatment beats control"
dataset = "terminal-bench/terminal-bench@4.0.0"
tasks = [{tasks}]
exclude = ["broken"]
trials = 2
batch = 4
seed = 11
concurrency = 2

[[arms]]
name = "control"
agent = "frond_harbor:Frond"
model = "anthropic/claude-opus-5-5"
options = {{ layout = "chat" }}

[[arms]]
name = "treatment"
agent = "frond_harbor:Frond"
model = "anthropic/claude-opus-5-5"
options = {{ layout = "turns", effort = "high" }}

[[claims]]
id = "pass"
metric = "pass"
treatment = "treatment"
control = "control"
kind = "superiority"

[[claims]]
id = "cost"
metric = "cost"
treatment = "treatment"
control = "control"
kind = "ratio-below"
bound = 1.0
"""


class SpecTest(BenchCase):
    def test_the_run_order_is_a_seeded_permutation_without_excluded_tasks(self):
        names = [f"task-{i:02d}" for i in range(10)] + ["broken"]
        path = self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names)))
        first, again = spec.load(path), spec.load(path)
        self.assertEqual(first.tasks, again.tasks)
        self.assertEqual(sorted(first.tasks), names[:10])
        self.assertNotEqual(list(first.tasks), names[:10])  # shuffled
        self.assertEqual(first.excluded, ("broken",))
        self.assertEqual([len(b) for b in first.batches()], [4, 4, 2])

    def test_a_claim_on_an_unknown_arm_is_refused(self):
        path = self.write_spec(SPEC.format(tasks='"a"').replace('control = "control"', 'control = "nobody"'))
        with self.assertRaises(ValueError):
            spec.load(path)


class MatrixTest(BenchCase):
    def test_arms_alternate_by_batch_and_commands_carry_the_arm(self):
        path = self.write_spec(SPEC.format(tasks=", ".join(f'"t{i}"' for i in range(8))))
        s = spec.load(path)
        plan = matrix.cells(s)
        self.assertEqual(
            [(c.batch, c.arm.name) for c in plan],
            [(1, "control"), (1, "treatment"), (2, "treatment"), (2, "control")],
        )
        argv = matrix.command(s, plan[1], self.dir / "jobs", self.dir / "ca.crt")
        joined = " ".join(argv)
        self.assertIn("--job-name T1-treatment-b01", joined)
        self.assertIn("--ak layout=turns --ak effort=high", joined)
        self.assertIn("-k 2 -n 2", joined)
        self.assertIn("--extra-docker-compose", joined)
        self.assertNotIn("NonZeroAgentExitCodeError", joined)  # an agent's own failure is never retried
        self.assertEqual(sum(a == "-i" for a in argv), 4)
        self.assertTrue(all(argv[i + 1].startswith("terminal-bench/") for i, a in enumerate(argv) if a == "-i"))
        self.assertNotIn("--extra-docker-compose", matrix.command(s, plan[1], self.dir / "jobs", None))

    def test_job_state_comes_from_harbors_result(self):
        jobs = self.dir / "jobs"
        self.assertEqual(matrix.state(jobs, "J"), "new")
        (jobs / "J").mkdir(parents=True)
        self.assertEqual(matrix.state(jobs, "J"), "partial")
        result = {"finished_at": "2026-11-03T10:00:00", "stats": {"n_pending_trials": 0, "n_running_trials": 0}}
        (jobs / "J" / "result.json").write_text(json.dumps(result))
        self.assertEqual(matrix.state(jobs, "J"), "done")

    def test_preflight_refuses_a_daemon_whose_exec_umask_is_not_022(self):
        s = spec.load(self.write_spec(SPEC.format(tasks='"t0"')))

        def docker(umask: str):
            def run(argv, **_):
                out = {"run": "c0\n", "exec": umask + "\n"}.get(argv[1], "")
                return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

            return run

        with mock.patch("subprocess.run", side_effect=docker("0000")):
            problems = matrix.preflight(s, None)
        self.assertTrue(any("umask 0000" in p and "G26" in p for p in problems), problems)
        with mock.patch("subprocess.run", side_effect=docker("0022")):
            self.assertFalse([p for p in matrix.preflight(s, None) if "umask" in p])

    def test_a_dry_run_prints_every_job_and_runs_nothing(self):
        path = self.write_spec(SPEC.format(tasks=", ".join(f'"t{i}"' for i in range(8))))
        with mock.patch("subprocess.Popen") as popen, mock.patch("builtins.print") as out:
            self.assertEqual(matrix.main([str(path), "--dry-run", "--jobs", str(self.dir / "jobs")]), 0)
        popen.assert_not_called()
        printed = "\n".join(str(call.args[0]) for call in out.call_args_list)
        self.assertEqual(printed.count("[new] T1-"), 4)
        self.assertEqual(printed.count("harbor run"), 4)


def fake_trial(job: Path, task: str, n: int, *, reward: float | None, cost_tokens: int = 1000, started: str = ""):
    """A trial directory as Harbor and frond's adapter leave it."""
    directory = job / f"{task}__{n}"
    (directory / "agent" / "frond").mkdir(parents=True)
    result: dict = {
        "task_id": {"name": task},
        "started_at": started or f"2026-11-03T10:{n:02d}:00Z",
        "agent_execution": {"started_at": "2026-11-03T10:00:00Z", "finished_at": "2026-11-03T10:05:00Z"},
        "verifier_result": {"rewards": {"reward": reward}},
        "exception_info": None,
    }
    if reward is None:  # the environment failed to start: the agent never ran
        result.update(agent_execution=None, verifier_result=None, exception_info={"exception_type": "RuntimeError"})
    (directory / "result.json").write_text(json.dumps(result))
    call = {"model": "claude-opus-5-5", "usage": {"input": cost_tokens, "cache_read": 0, "cache_write": 0, "output": 0}}
    (directory / "agent" / "frond" / "calls.jsonl").write_text(json.dumps(call) + "\n")
    metrics = {"failed_edits": 1, "steps": 10, "config": {"layout": "turns"}}
    (directory / "agent" / "frond" / "metrics.json").write_text(json.dumps(metrics))


class AnalyzeTest(BenchCase):
    def test_a_clear_win_holds_and_infrastructure_failures_do_not_count(self):
        names = [f"t{i:02d}" for i in range(16)]
        s = spec.load(self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names))))
        control, treatment = self.dir / "T1-control-b01", self.dir / "T1-treatment-b01"
        for i, task in enumerate(names):
            for n in range(2):
                fake_trial(control, task, n, reward=1.0 if i < 3 else 0.0, cost_tokens=2000)
                fake_trial(treatment, task, n, reward=1.0 if i < 14 else 0.0, cost_tokens=1000)
        fake_trial(treatment, "t00", 9, reward=None)  # an environment that never started
        fake_trial(treatment, "t15", 8, reward=1.0, started="2026-11-03T11:00:00Z")  # a third valid trial: ignored
        summary = analyze.analyze(s, analyze.job_dirs(s, self.dir), analyze.load_prices())
        arms = summary["arms"]
        self.assertEqual(arms["treatment"]["infrastructure_failures"], ["t00 (RuntimeError)"])
        self.assertAlmostEqual(arms["treatment"]["pass_rate"], 14 / 16)
        self.assertAlmostEqual(arms["control"]["pass_rate"], 3 / 16)
        self.assertAlmostEqual(arms["treatment"]["cost_per_trial"], 1000 * 4 / 1e6)
        self.assertEqual(len(arms["treatment"]["configurations"]), 1)
        claims = summary["claims"]
        self.assertTrue(claims["pass"]["holds"])
        self.assertLess(claims["pass"]["p"], 0.01)
        self.assertEqual(claims["pass"]["sequence"]["decision"], "holds")
        self.assertAlmostEqual(claims["cost"]["estimate"], 0.5)
        self.assertTrue(claims["cost"]["holds"])
        text = analyze.report(summary)
        self.assertIn("| pass | superiority | 16 |", text)
        self.assertIn("Infrastructure failures in treatment", text)

    def test_a_reference_agents_provider_failure_is_not_scored(self):
        trial = self.dir / "job" / "t__1"
        trial.mkdir(parents=True)
        result = {
            "task_id": {"name": "t"},
            "agent_execution": {"started_at": "2026-11-03T10:00:00Z", "finished_at": "2026-11-03T10:00:01Z"},
            "verifier_result": {"rewards": {"reward": 0.0}},
            "exception_info": {"exception_type": "ApiRateLimitError"},
            "agent_result": {"cost_usd": 0.0},
        }
        (trial / "result.json").write_text(json.dumps(result))
        loaded = analyze.load_trial(trial, "claude-code", analyze.load_prices())
        assert loaded is not None
        self.assertIsNone(loaded.reward)

    def test_a_call_is_priced_by_its_own_model(self):
        prices = analyze.load_prices()
        usage = {"input": 1_000_000, "cache_read": 600_000, "cache_write": 100_000, "output": 10_000}
        cost = analyze.call_cost("anthropic/claude-opus-5-5", usage, prices)
        self.assertAlmostEqual(cost or 0.0, 0.3 * 4 + 0.6 * 0.2 + 0.1 * 5 + 0.01 * 20)
        self.assertIsNone(analyze.call_cost("someone/unknown-model", usage, prices))


if __name__ == "__main__":
    unittest.main()
