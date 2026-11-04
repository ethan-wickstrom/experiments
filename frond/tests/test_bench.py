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
from bench import budget as budget_mod
from bench.spec import BENCH
from bench.stats import betting_cs, bootstrap_interval, bootstrap_t_below, difference_cs, holm, midranks, wilcoxon


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


class BootstrapTTest(unittest.TestCase):
    """The ratio claims' test (F5): H0 mean >= 0, with the null imposed and a studentized statistic."""

    def test_too_few_or_unvarying_values_say_nothing(self):
        self.assertEqual(bootstrap_t_below([-0.001, -0.001]), 1.0)  # Devin's example: the old test gave 1/10001
        self.assertEqual(bootstrap_t_below([-0.5] * 10), 1.0)

    def test_a_clear_effect_is_found_and_none_is_not(self):
        rng = random.Random(3)
        below = [rng.gauss(-1.0, 1.0) for _ in range(30)]
        self.assertLess(bootstrap_t_below(below, resamples=2000), 0.01)
        centred = [x + 1.0 for x in below]
        self.assertGreater(bootstrap_t_below(centred, resamples=2000), 0.05)

    def test_under_the_null_it_rejects_at_about_alpha_on_skewed_data(self):
        rng = random.Random(11)
        datasets, rejected = 300, 0
        for i in range(datasets):
            draws = [rng.expovariate(1.0) - 1.0 for _ in range(20)]  # mean 0, right-skewed, like costs
            rejected += bootstrap_t_below(draws, resamples=499, seed=i) < 0.05
        self.assertLess(rejected / datasets, 0.09)  # 0.05, plus three standard errors of the estimate


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
        jobs = mock.patch.object(matrix, "JOBS", self.dir / "checkout-jobs")  # never the checkout's real trials
        jobs.start()
        self.addCleanup(jobs.stop)

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

    def test_repeated_claim_ids_are_refused(self):  # results are keyed by id: one would vanish from Holm (F7)
        path = self.write_spec(SPEC.format(tasks='"a"').replace('id = "cost"', 'id = "pass"'))
        with self.assertRaisesRegex(ValueError, "claim ids repeat"):
            spec.load(path)

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

        def docker(umask: str | None):  # None: the probe container cannot start
            def run(argv, **_):
                failed = umask is None and argv[1] == "run"
                out = {"run": "c0\n", "exec": f"{umask}\n"}.get(argv[1], "")
                return subprocess.CompletedProcess(argv, int(failed), stdout="" if failed else out, stderr="")

            return run

        with mock.patch("subprocess.run", side_effect=docker("0000")):
            problems = matrix.preflight(s, None)
        self.assertTrue(any("umask 0000" in p and "G26" in p for p in problems), problems)
        with mock.patch("subprocess.run", side_effect=docker(None)):
            problems = matrix.preflight(s, None)
        self.assertTrue(any("could not be measured" in p for p in problems), problems)  # unmeasured is refused too
        with mock.patch("subprocess.run", side_effect=docker("0022")):
            self.assertFalse([p for p in matrix.preflight(s, None) if "umask" in p])

    def test_a_stalled_harbor_install_is_retried_then_refused(self):  # a hung uvx download (G32)
        stalled = subprocess.TimeoutExpired(["uvx"], 300)
        ok = subprocess.CompletedProcess([], 0, stdout=b"0.25.0", stderr=b"")
        with mock.patch("subprocess.run", side_effect=[stalled, ok]) as run:
            self.assertTrue(matrix.harbor_ready())
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.kwargs["timeout"], 300.0)
        with mock.patch("subprocess.run", side_effect=stalled) as run:
            self.assertFalse(matrix.harbor_ready())
        self.assertEqual(run.call_count, 3)
        s = spec.load(self.write_spec(SPEC.format(tasks='"t0"')))
        with mock.patch.object(matrix, "harbor_ready", return_value=False), mock.patch("subprocess.run"):
            self.assertTrue(any("Harbor's environment" in p for p in matrix.preflight(s, None)))

    def test_the_anthropic_key_may_be_stored_as_claude_api_key(self):  # the owner's name for it (REQ-1)
        env = matrix.with_aliases({"CLAUDE_API_KEY": "secret-value", "PATH": "/bin"})
        self.assertEqual(env["ANTHROPIC_API_KEY"], "secret-value")
        both = matrix.with_aliases({"CLAUDE_API_KEY": "alias", "ANTHROPIC_API_KEY": "direct"})
        self.assertEqual(both["ANTHROPIC_API_KEY"], "direct")  # an explicit key wins
        self.assertNotIn("ANTHROPIC_API_KEY", matrix.with_aliases({"PATH": "/bin"}))

    def test_jobs_of_another_spec_or_source_are_not_resumed(self):  # F8
        current = {"spec_sha256": "s1", "source_sha256": "c1"}
        self.assertEqual(matrix.resumable({"runs": []}, current, False), [])
        ran = {"runs": [{"job": "J"}], "spec_sha256": "s1", "source_sha256": "c1"}
        self.assertEqual(matrix.resumable(ran, current, False), [])
        self.assertIn("another version of this spec", matrix.resumable({**ran, "spec_sha256": "s0"}, current, True)[0])
        changed = {**ran, "source_sha256": "c0"}
        self.assertIn("frond's source", matrix.resumable(changed, current, False)[0])
        self.assertEqual(matrix.resumable(changed, current, True), [])  # allowed, and recorded with each run
        self.assertEqual(matrix.source_digest(), matrix.source_digest())

    def test_a_failed_harbor_job_fails_the_run(self):  # Harbor exits 0 whatever its trials did: 1 means the job (F6)
        path = self.write_spec(SPEC.format(tasks='"t0", "t1"'))
        with (
            mock.patch.object(matrix, "preflight", return_value=[]),
            mock.patch.object(matrix, "run_cell", side_effect=[1, 0]) as run,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(matrix.main([str(path), "--jobs", str(self.dir / "jobs")]), 1)
        self.assertEqual(run.call_count, 2)  # the other jobs still ran
        manifest = json.loads((self.dir / "jobs" / "matrix.json").read_text())
        self.assertEqual([r["exit"] for r in manifest["runs"]], [1, 0])

    def test_a_source_edited_during_the_run_stops_it_before_the_next_job(self):  # each job builds its own wheel
        path = self.write_spec(SPEC.format(tasks='"t0"'))
        digests = iter(["c1", "c1", "c2"])  # provenance, first job, second job
        with (
            mock.patch.object(matrix, "preflight", return_value=[]),
            mock.patch.object(matrix, "affordable", return_value=(True, "")),
            mock.patch.object(matrix, "source_digest", side_effect=lambda: next(digests)),
            mock.patch.object(matrix, "run_cell", return_value=0) as run,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(matrix.main([str(path), "--jobs", str(self.dir / "jobs")]), 2)
        self.assertEqual(run.call_count, 1)

    def test_finished_trials_are_named_as_the_analysis_names_them(self):  # Devin, #23
        job = self.dir / "job"
        (job / "a__1").mkdir(parents=True)
        (job / "a__1" / "result.json").write_text(json.dumps({"task_id": {"name": "a"}, "finished_at": "2026-11-03"}))
        self.assertEqual(matrix.remaining(job, ["a"], 2), 1)

    def test_no_early_stop_on_a_batch_with_a_failed_job(self):  # Devin, #23
        names = [f"t{i}" for i in range(4)]
        body = SPEC.format(tasks=", ".join(f'"{n}"' for n in names)).replace(
            "concurrency = 2", "concurrency = 2\nstop_early = true"
        )
        path = self.write_spec(body)
        with (
            mock.patch.object(matrix, "preflight", return_value=[]),
            mock.patch.object(matrix, "affordable", return_value=(True, "")),
            mock.patch.object(matrix, "run_cell", side_effect=[1, 0, 0, 0]),
            mock.patch.object(matrix, "decided", return_value=True) as decided,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(matrix.main([str(path), "--jobs", str(self.dir / "jobs")]), 1)
        decided.assert_not_called()  # the failed batch is never read for a stop

    def test_a_job_is_recorded_before_harbor_starts(self):  # a run killed midway still binds its directory (#23)
        path = self.write_spec(SPEC.format(tasks='"t0"'))
        seen: list[dict] = []

        def run(*_args, **_kwargs):
            seen.append(json.loads((self.dir / "jobs" / "matrix.json").read_text()))
            return 0

        with (
            mock.patch.object(matrix, "preflight", return_value=[]),
            mock.patch.object(matrix, "affordable", return_value=(True, "")),
            mock.patch.object(matrix, "run_cell", side_effect=run),
            mock.patch("builtins.print"),
        ):
            matrix.main([str(path), "--jobs", str(self.dir / "jobs")])
        self.assertEqual(seen[0]["runs"][0]["exit"], None)
        self.assertTrue(seen[0]["source_sha256"])

    def test_pending_tasks_are_those_short_of_finished_trials(self):
        job = self.dir / "job"
        for name, task, finished in (
            ("a__1", "a", True),
            ("a__2", "a", True),
            ("b__1", "b", True),
            ("b__2", "b", False),
        ):
            (job / name).mkdir(parents=True)
            result = {
                "task_name": f"terminal-bench/{task}",
                "finished_at": "2026-11-03T10:00:00Z" if finished else None,
            }
            (job / name / "result.json").write_text(json.dumps(result))
        self.assertEqual(matrix.pending(job, ["a", "b", "c"], 2), {"b", "c"})

    def test_the_pruner_keeps_images_of_tasks_with_trials_pending(self):  # F2
        from bench import prune

        scans = iter(
            [
                ({"img-a", "img-b"}, {"img-a": "task-a", "img-b": "task-b"}),  # both in use by their trials
                ({"img-a", "img-b"}, {}),  # both unused
                ({"img-a", "img-b"}, {}),  # still unused: removable, unless their task has trials to come
            ]
        )
        removed: list[str] = []

        def rmi(argv, **_):
            removed.append(argv[2])
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        def sleep(_):
            if len(sleeps) == 2:
                raise StopIteration
            sleeps.append(1)

        sleeps: list[int] = []
        with (
            mock.patch.object(prune, "scan", side_effect=lambda: next(scans)),
            mock.patch.object(prune, "created_between", return_value={}),
            mock.patch.object(prune.subprocess, "run", side_effect=rmi),
            mock.patch.object(prune.time, "sleep", side_effect=sleep),
            self.assertRaises(StopIteration),
        ):
            prune.prune_while(None, 0, str(self.dir / "prune.log"), pending=lambda: {"task-a"})
        self.assertEqual(removed, ["img-b"])

    def test_the_pruner_learns_owners_from_containers_it_never_saw(self):  # created and removed between passes (#23)
        from bench import prune

        scans = iter([({"img-a"}, {}), ({"img-a"}, {}), ({"img-a"}, {})])  # never seen in use
        removed: list[str] = []
        sleeps: list[int] = []

        def sleep(_):
            if len(sleeps) == 2:
                raise StopIteration
            sleeps.append(1)

        with (
            mock.patch.object(prune, "scan", side_effect=lambda: next(scans)),
            mock.patch.object(prune, "created_between", side_effect=[{"img-a": "task-a"}, {}, {}]),
            mock.patch.object(prune.subprocess, "run", side_effect=lambda argv, **_: removed.append(argv[2])),
            mock.patch.object(prune.time, "sleep", side_effect=sleep),
            self.assertRaises(StopIteration),
        ):
            prune.prune_while(None, 0, str(self.dir / "prune.log"), pending=lambda: {"task-a"})
        self.assertEqual(removed, [])

    def test_a_dry_run_prints_every_job_and_runs_nothing(self):
        path = self.write_spec(SPEC.format(tasks=", ".join(f'"t{i}"' for i in range(8))))
        with mock.patch("subprocess.Popen") as popen, mock.patch("builtins.print") as out:
            self.assertEqual(matrix.main([str(path), "--dry-run", "--jobs", str(self.dir / "jobs")]), 0)
        popen.assert_not_called()
        printed = "\n".join(str(call.args[0]) for call in out.call_args_list)
        self.assertEqual(printed.count("[new] T1-"), 4)
        self.assertEqual(printed.count("harbor run"), 4)


CONTROL = {"model": "anthropic/claude-opus-5-5", "layout": "chat", "effort": "high"}  # as frond records SPEC's arms
TREATMENT = {"model": "anthropic/claude-opus-5-5", "layout": "turns", "effort": "high"}


class BudgetTest(BenchCase):
    """The program's cap (D43): a job that could pass it does not start."""

    def test_a_job_is_assumed_to_cost_its_guess_until_its_model_is_measured(self):
        budget = budget_mod.Budget(usd=100.0, margin=1.5, guess={"claude-opus-5-5": 2.0})
        arm = spec.Arm("opus", "frond_harbor:Frond", "anthropic/claude-opus-5-5", {"max_steps": "80"}, None)
        self.assertEqual(budget_mod.job_estimate(arm, 10, {}, budget), 10 * 2.0 * 2)  # 80 steps: twice the guess
        measured = {"anthropic/claude-opus-5-5": 5.0}
        self.assertEqual(budget_mod.job_estimate(arm, 10, measured, budget), 10 * 5.0 * 1.5)
        oracle = spec.Arm("oracle", "oracle", None, {}, None)
        self.assertEqual(budget_mod.job_estimate(oracle, 56, measured, budget), 0.0)

    def test_spending_counts_every_trial_and_the_costliest_per_model(self):
        root = self.dir / "jobs" / "E9"
        fake_trial(root / "E9-a-b01", "t0", 0, reward=1.0, cost_tokens=1_000_000)  # $4 of Opus input
        fake_trial(root / "E9-a-b01", "t1", 0, reward=0.0, cost_tokens=500_000)
        nested = self.dir / "jobs" / "runs" / "E8" / "E8-a-b01"  # a --jobs directory nested deeper still counts
        fake_trial(nested, "t0", 0, reward=1.0, cost_tokens=250_000)
        reference = self.dir / "jobs" / "E9" / "E9-cc-b01" / "t2__0"  # another agent: Harbor's model and cost only
        (reference / "agent").mkdir(parents=True)
        result = {
            "task_id": {"name": "t2"},
            "config": {"agent": {"model_name": "anthropic/claude-opus-5-5"}},
            "agent_execution": {"started_at": "2026-11-03T10:00:00Z"},
            "verifier_result": {"rewards": {"reward": 1.0}},
            "agent_result": {"cost_usd": 7.0},
        }
        (reference / "result.json").write_text(json.dumps(result))
        spent = budget_mod.spending([self.dir / "jobs", nested.parent], analyze.load_prices())  # counted once each
        self.assertAlmostEqual(spent.total, 4.0 + 2.0 + 1.0 + 7.0)
        self.assertAlmostEqual(spent.worst["anthropic/claude-opus-5-5"], 7.0)  # the reference agent's trial too
        self.assertEqual(spent.unknown, [])

    def test_recorded_spending_counts_and_stands_in_for_its_jobs(self):  # G37: what jobs/ cannot show
        lost = budget_mod.Spent(3.0, "jobs lost with an earlier VM")
        killed = budget_mod.Spent(1.5, "trials killed before writing their cost", jobs="E0-aborted")
        fake_trial(self.dir / "jobs" / "E0-aborted" / "E0-a-b01", "t0", 0, reward=1.0, cost_tokens=1_000_000)
        broken = self.dir / "jobs" / "E0-aborted" / "E0-a-b01" / "t1__0"  # killed: a result, no cost
        (broken / "agent").mkdir(parents=True)
        (broken / "result.json").write_text(json.dumps({"config": {"agent": {"model_name": "anthropic/x"}}}))
        fake_trial(self.dir / "jobs" / "E1" / "E1-a-b01", "t0", 0, reward=1.0, cost_tokens=500_000)
        spent = budget_mod.spending([self.dir / "jobs"], analyze.load_prices(), (lost, killed))
        self.assertAlmostEqual(spent.total, 3.0 + 1.5 + 2.0)  # E0-aborted's trials are replaced by its entry
        self.assertEqual(spent.unknown, [])
        recorded = budget_mod.load_budget().spent
        self.assertTrue(recorded and all(s.usd > 0 and s.why for s in recorded))

    def test_a_trial_whose_cost_cannot_be_told_stops_the_run(self):  # fail closed (Codex, #23)
        path = self.write_spec(SPEC.format(tasks='"t0"'))
        s = spec.load(path)
        jobs = self.dir / "jobs"
        fake_trial(jobs / "T1-control-b01", "t0", 0, reward=1.0, config=CONTROL)
        calls = jobs / "T1-control-b01" / "t0__0" / "agent" / "frond" / "calls.jsonl"
        calls.write_text(calls.read_text() + json.dumps({"model": "someone/unpriced", "usage": {"input": 5}}) + "\n")
        allowed, text = matrix.affordable(s, matrix.cells(s)[0], jobs, budget_mod.load_budget())
        self.assertFalse(allowed)
        self.assertIn("cannot count the cost of 1 trials", text)

    def test_the_runner_stops_before_a_job_that_could_pass_the_cap(self):
        path = self.write_spec(SPEC.format(tasks='"t0", "t1"'))
        tight = budget_mod.Budget(usd=0.01, margin=1.5, guess={"claude-opus-5-5": 2.0})
        with (
            mock.patch.object(matrix, "preflight", return_value=[]),
            mock.patch.object(matrix, "load_budget", return_value=tight),
            mock.patch.object(matrix, "run_cell", return_value=0) as run,
            mock.patch("builtins.print"),
        ):
            self.assertEqual(matrix.main([str(path), "--jobs", str(self.dir / "jobs")]), 4)
        run.assert_not_called()

    def test_reference_agents_are_estimated_by_their_bounds_and_refused_without(self):  # G33
        budget = budget_mod.Budget(usd=100.0, margin=1.5, guess={"claude-opus-5-5": 4.0})
        model = "anthropic/claude-opus-5-5"
        capped = spec.Arm("cc", "claude-code", model, {"max_budget_usd": "10"}, None)
        self.assertEqual(budget_mod.job_estimate(capped, 3, {model: 50.0}, budget), 30.0)  # the cap, not history
        turns = spec.Arm("t2", "terminus-2", model, {"max_turns": "150"}, None)
        self.assertEqual(budget_mod.job_estimate(turns, 2, {}, budget), 2 * 4.0 * 150 / 40)
        self.assertFalse(budget_mod.unbounded(capped) or budget_mod.unbounded(turns))
        self.assertTrue(budget_mod.unbounded(spec.Arm("cc", "claude-code", model, {}, None)))
        self.assertTrue(budget_mod.unbounded(spec.Arm("x", "some-new-agent", model, {}, None)))
        self.assertFalse(budget_mod.unbounded(spec.Arm("rlm", "dspy-rlm", model, {}, None)))  # bounded by default
        self.assertFalse(budget_mod.unbounded(spec.Arm("oracle", "oracle", None, {}, None)))
        for name in ("e11-references", "smoke"):
            loaded = spec.load(BENCH / "experiments" / f"{name}.toml")
            self.assertFalse([a.name for a in loaded.arms if budget_mod.unbounded(a)], name)

    def test_e0_fits_the_cap_on_the_guesses_alone(self):
        e0 = spec.load(BENCH / "experiments" / "e0-pilot.toml")
        budget = budget_mod.load_budget()
        planned = sum(
            budget_mod.job_estimate(c.arm, len(c.tasks) * e0.trials_of(c.arm), {}, budget) for c in matrix.cells(e0)
        )
        self.assertLessEqual(planned, budget.usd)  # $76.50 (D48): the guard must not stop E0 on its guesses alone

    def test_a_frond_arms_sub_model_needs_a_price_too(self):  # Codex, #23
        body = SPEC.format(tasks='"t0"').replace('options = {{ layout = "chat" }}', 'options = {{ layout = "chat" }}')
        path = self.write_spec(
            body.replace('options = { layout = "chat" }', 'options = { layout = "chat", sub_model = "someone/cheap" }')
        )
        s = spec.load(path)
        self.assertEqual(matrix.models_of(s.arms[0]), ["anthropic/claude-opus-5-5", "someone/cheap"])
        with mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="")):
            problems = matrix.preflight(s, None)
        self.assertTrue(any("no price for someone/cheap" in p for p in problems), problems)

    def test_an_arm_with_no_price_or_guess_cannot_spend(self):
        path = self.write_spec(SPEC.format(tasks='"t0"').replace("anthropic/claude-opus-5-5", "someone/new-model", 1))
        s = spec.load(path)
        with mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="")):
            problems = matrix.preflight(s, None)
        self.assertTrue(any("no price for someone/new-model" in p for p in problems), problems)
        self.assertTrue(any("no per-trial guess for someone/new-model" in p for p in problems), problems)


def fake_trial(
    job: Path,
    task: str,
    n: int,
    *,
    reward: float | None,
    cost_tokens: int = 1000,
    started: str = "",
    config: dict | None = None,
    refusal: str = "",
):
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
    metrics = {"failed_edits": 1, "steps": 10, "config": config if config is not None else TREATMENT}
    if refusal:  # the provider refused a call: the trial ends as its failure, unscored (G43)
        metrics.update(error_kind="provider", refusal=refusal)
    (directory / "agent" / "frond" / "metrics.json").write_text(json.dumps(metrics))


class AnalyzeTest(BenchCase):
    def test_trials_stopped_by_a_reference_agents_bound_are_counted(self):  # G39
        model = "anthropic/claude-opus-5-5"
        capped = spec.Arm("cc", "claude-code", model, {"max_budget_usd": "10"}, None)
        turns = spec.Arm("t2", "terminus-2", model, {"max_turns": "150"}, None)
        frond = spec.Arm("f", "frond_harbor:Frond", model, {}, None)

        def trial(cost: float | None = None, turns: int | None = None) -> analyze.Trial:
            return analyze.Trial("x", "t", "t__1", 1.0, cost, turns=turns)

        self.assertTrue(analyze.stopped_by_bound(trial(cost=9.7), capped))
        self.assertFalse(analyze.stopped_by_bound(trial(cost=3.0), capped))
        self.assertTrue(analyze.stopped_by_bound(trial(turns=150), turns))
        self.assertFalse(analyze.stopped_by_bound(trial(turns=40), turns))
        self.assertIsNone(analyze.stopped_by_bound(trial(turns=None), turns))
        self.assertIsNone(analyze.stopped_by_bound(trial(cost=9.9), frond))
        job = self.dir / "job"
        directory = job / "t__1"
        (directory / "agent").mkdir(parents=True)
        result = {
            "task_id": {"name": "t"},
            "agent_execution": {"started_at": "2026-11-03T10:00:00Z"},
            "verifier_result": {"rewards": {"reward": 0.0}},
            "agent_result": {"cost_usd": 2.0, "metadata": {"n_episodes": 150}},
        }
        (directory / "result.json").write_text(json.dumps(result))
        loaded = analyze.load_trial(directory, "t2", analyze.load_prices())
        assert loaded is not None
        self.assertEqual(loaded.turns, 150)

    def test_the_report_shows_protocol_adherence_per_step(self):  # E0's first question (D46)
        arms = {
            "haiku": {
                "steps_per_trial": 20.0,
                "parse_failures_per_trial": 5.0,
                "parse_recovered_per_trial": 3.0,
                "unparsed_steps_per_trial": 2.0,
                "cut_off_replies_per_trial": None,
                "syntax_errors_per_trial": 1.0,
                "sub_parse_failures_per_trial": 0.0,
            },
            "empty": {"steps_per_trial": None},
        }
        table = "\n".join(analyze.protocol_table(arms))
        self.assertIn("| haiku | 20.0 | 0.250 | 0.150 | 0.100 | – | 0.050 | 0.00/trial |", table)
        self.assertNotIn("| empty |", table)
        self.assertEqual(analyze.protocol_table({"empty": {"steps_per_trial": None}}), [])
        forked = {**arms["haiku"], "branch_steps_per_trial": 5.0}  # Codex, #36: branch replies are counted too
        self.assertIn("| forked | 25.0 | 0.200 |", "\n".join(analyze.protocol_table({"forked": forked})))

    def test_a_clear_win_holds_and_infrastructure_failures_do_not_count(self):
        names = [f"t{i:02d}" for i in range(16)]
        s = spec.load(self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names))))
        control, treatment = self.dir / "T1-control-b01", self.dir / "T1-treatment-b01"
        for i, task in enumerate(names):
            for n in range(2):
                cost = 2000 + 37 * i  # tasks differ in cost, as they do
                fake_trial(control, task, n, reward=1.0 if i < 3 else 0.0, cost_tokens=cost, config=CONTROL)
                fake_trial(treatment, task, n, reward=1.0 if i < 14 else 0.0, cost_tokens=cost // 2 + 13 * (i % 5))
        fake_trial(treatment, "t00", 9, reward=None)  # an environment that never started
        fake_trial(treatment, "t15", 8, reward=1.0, started="2026-11-03T11:00:00Z")  # a third valid trial: ignored
        summary = analyze.analyze(s, analyze.job_dirs(s, self.dir), analyze.load_prices())
        arms = summary["arms"]
        self.assertEqual(arms["treatment"]["infrastructure_failures"], ["t00 (RuntimeError)"])
        self.assertAlmostEqual(arms["treatment"]["pass_rate"], 14 / 16)
        self.assertAlmostEqual(arms["control"]["pass_rate"], 3 / 16)
        self.assertEqual(len(arms["treatment"]["configurations"]), 1)
        self.assertEqual(arms["treatment"]["incomplete_tasks"], [])
        claims = summary["claims"]
        self.assertTrue(claims["pass"]["holds"])
        self.assertLess(claims["pass"]["p"], 0.01)
        self.assertEqual(claims["pass"]["sequence"]["decision"], "holds")
        self.assertAlmostEqual(claims["cost"]["estimate"], 0.51, places=2)
        self.assertTrue(claims["cost"]["holds"])
        self.assertEqual((claims["pass"]["rule"], claims["cost"]["rule"]), ("Holm", "Holm"))
        text = analyze.report(summary)
        self.assertIn("| pass | superiority | 16 |", text)
        self.assertIn("Infrastructure failures and misconfigured trials in treatment", text)

    def test_refusals_are_counted_per_arm_and_flagged_above_e0bs_rate(self):  # B20, D61
        names = [f"t{i:02d}" for i in range(8)]
        s = spec.load(self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names))))
        control, treatment = self.dir / "T1-control-b01", self.dir / "T1-treatment-b01"
        for i, task in enumerate(names):
            for n in range(2):
                fake_trial(control, task, n, reward=1.0, config=CONTROL, refusal="cyber" if (i, n) == (0, 0) else "")
                refused = "reasoning_extraction" if i < 3 else ""
                fake_trial(treatment, task, n, reward=1.0, refusal=refused)
        summary = analyze.analyze(s, analyze.job_dirs(s, self.dir), analyze.load_prices())
        arms = summary["arms"]
        self.assertEqual((arms["control"]["refused_trials"], arms["control"]["all_trials"]), (1, 16))
        self.assertEqual(arms["treatment"]["refusals"], {"reasoning_extraction": 6})
        self.assertEqual(arms["treatment"]["trials"], 10)  # refused trials are not scored
        text = analyze.report(summary)
        self.assertIn(
            "Refused by the provider in treatment: 6 of 16 trials (reasoning_extraction 6). That is more", text
        )
        self.assertIn("Refused by the provider in control: 1 of 16 trials (cyber 1).\n", text + "\n")

    def test_a_trial_that_did_not_run_its_arm_is_not_scored(self):
        names = [f"t{i:02d}" for i in range(4)]
        s = spec.load(self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names))))
        treatment = self.dir / "T1-treatment-b01"
        fake_trial(treatment, "t00", 0, reward=1.0, config={**TREATMENT, "layout": "chat"})  # the control's layout
        fake_trial(treatment, "t00", 1, reward=0.0, started="2026-11-03T10:30:00Z")
        fake_trial(treatment, "t00", 2, reward=0.0, started="2026-11-03T10:40:00Z")
        trials = analyze.load_arm(
            [treatment], "treatment", 2, analyze.load_prices(), analyze.expected_config(s.arms[1])
        )
        scored = [t for t in trials if t.reward is not None]
        self.assertEqual([t.name for t in scored], ["t00__1", "t00__2"])  # the next valid trials take its place
        [wrong] = [t for t in trials if t.reward is None]
        self.assertIn("layout='chat', spec 'turns'", wrong.exception)
        self.assertEqual(analyze.misconfigured({}, analyze.expected_config(s.arms[1])), [])  # another agent: unchecked

    def test_tasks_short_of_their_trials_are_reported(self):
        names = [f"t{i:02d}" for i in range(4)]
        s = spec.load(self.write_spec(SPEC.format(tasks=", ".join(f'"{n}"' for n in names))))
        for task in names[:3]:
            for n in range(2):
                fake_trial(self.dir / "T1-control-b01", task, n, reward=0.0, config=CONTROL)
        fake_trial(self.dir / "T1-control-b01", "t03", 0, reward=0.0, config=CONTROL)
        summary = analyze.analyze(s, analyze.job_dirs(s, self.dir), analyze.load_prices())
        self.assertEqual(summary["arms"]["control"]["incomplete_tasks"], ["t03"])
        self.assertEqual(summary["arms"]["treatment"]["incomplete_tasks"], sorted(names))
        self.assertIn(
            "Incomplete: control has 7 of 8 planned valid trials; 1 tasks are short: t03.", analyze.report(summary)
        )

    def test_a_spec_that_may_stop_early_decides_by_rules_valid_at_any_stop(self):
        names = [f"t{i:02d}" for i in range(12)]
        body = SPEC.format(tasks=", ".join(f'"{n}"' for n in names)).replace(
            "concurrency = 2", "concurrency = 2\nstop_early = true"
        )
        s = spec.load(self.write_spec(body))
        self.assertTrue(s.stop_early)
        for i, task in enumerate(names):
            for n in range(2):
                cost = 2000 + 41 * i
                fake_trial(self.dir / "T1-control-b01", task, n, reward=0.0, cost_tokens=cost, config=CONTROL)
                win = 1.0 if i < 6 else 0.0  # half the tasks flip from fail to pass
                fake_trial(self.dir / "T1-treatment-b01", task, n, reward=win, cost_tokens=cost // 2 + 17 * (i % 3))
        summary = analyze.analyze(s, analyze.job_dirs(s, self.dir), analyze.load_prices())
        passed, cost = summary["claims"]["pass"], summary["claims"]["cost"]
        self.assertLess(passed["p"] * 2, 0.05)  # Holm on the fixed-size test would call it, which is not valid here
        self.assertEqual((passed["rule"], passed["sequence"]["decision"]), ("confidence sequence", "open"))
        self.assertFalse(passed["holds"])  # the sequence decides, and has not yet
        looks = len(s.batches())
        self.assertEqual(cost["rule"], f"p x {looks} looks x 2 claims")
        self.assertAlmostEqual(cost["p_adjusted"], min(1.0, cost["p"] * looks * 2))

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
