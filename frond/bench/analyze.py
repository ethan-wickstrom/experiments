"""Evaluate an experiment from its Harbor jobs: per-task results, the pre-registered claims, and a report.

    python -m bench.analyze bench/experiments/e6-layout.toml --jobs jobs/E6 --out bench/results/2026-11-20-e6

Each claim compares a treatment arm with a control arm on one metric, task by task. The decision rule, fixed here
before any data: a claim holds when its one-sided p-value, Holm-adjusted across the spec's claims, is below alpha.
Pass-rate claims also get a confidence sequence, which says after each batch whether the claim is already decided
(``stats.betting_cs``). Trials that failed before their agent started are infrastructure failures: they are
reported and left out, never counted as the agent's failures. Only the first ``trials`` valid trials of a task
count, in the order they started, so a retry can never pick the better of two outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tomllib
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import fmean, pvariance, variance
from typing import Any

from .spec import BENCH, BOUNDED, Claim, Spec, load
from .stats import bootstrap, bootstrap_interval, difference_cs, holm, wilcoxon

TOKEN_KEYS = ("input", "cache_read", "cache_write", "output")
COUNTERS = ("failed_edits", "parse_failures", "syntax_errors", "steps")


@dataclass
class Trial:
    arm: str
    task: str
    name: str
    reward: float | None  # None: an infrastructure failure, which does not count
    cost: float | None  # USD at list prices; None when a model's price is unknown
    started: str = ""
    seconds: float | None = None  # the agent's execution time
    tokens: dict[str, int] = field(default_factory=dict)
    counters: dict[str, float] = field(default_factory=dict)
    exception: str = ""
    config: dict[str, Any] = field(default_factory=dict)  # frond's recorded configuration, to check the arm's setup


def load_prices(path: Path = BENCH / "prices.toml") -> dict[str, dict[str, float]]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def call_cost(model: str, usage: dict[str, int], prices: dict[str, dict[str, float]]) -> float | None:
    """One call's cost: uncached input, cache reads, cache writes and output, each at its own price."""
    name = model.split("/")[-1].lower()
    keys = [key for key in prices if name.startswith(key)]
    if not keys:
        return None
    price = prices[max(keys, key=len)]
    uncached = max(0, usage.get("input", 0) - usage.get("cache_read", 0) - usage.get("cache_write", 0))
    return (
        uncached * price["input"]
        + usage.get("cache_read", 0) * price["cache_read"]
        + usage.get("cache_write", 0) * price["cache_write"]
        + usage.get("output", 0) * price["output"]
    ) / 1e6


def _seconds(span: dict[str, Any] | None) -> float | None:
    if not span or not span.get("started_at") or not span.get("finished_at"):
        return None
    start, end = (datetime.fromisoformat(span[k].replace("Z", "+00:00")) for k in ("started_at", "finished_at"))
    return (end - start).total_seconds()


def load_trial(directory: Path, arm: str, prices: dict[str, dict[str, float]]) -> Trial | None:
    try:
        result = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None  # not a trial, or one still running
    task = str((result.get("task_id") or {}).get("name") or result.get("task_name") or "").split("/")[-1]
    exception = result.get("exception_info") or {}
    execution = result.get("agent_execution") or {}
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    # None when the environment or the agent's installation failed: then nothing the agent did is measured
    reward = None if exception and not execution.get("started_at") else float(rewards.get("reward") or 0.0)
    export = directory / "agent" / "frond"
    tokens = dict.fromkeys(TOKEN_KEYS, 0)
    cost: float | None
    if (export / "calls.jsonl").is_file():  # frond: price every call by its own model (main and sub differ)
        cost = 0.0
        for line in (export / "calls.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            usage = record.get("usage") or {}
            for key in TOKEN_KEYS:
                tokens[key] += int(usage.get(key) or 0)
            one = call_cost(str(record.get("model") or ""), usage, prices)
            cost = None if one is None or cost is None else cost + one
    else:  # other agents: what Harbor recorded
        agent = result.get("agent_result") or {}
        tokens.update(
            input=int(agent.get("n_input_tokens") or 0),
            cache_read=int(agent.get("n_cache_tokens") or 0),
            output=int(agent.get("n_output_tokens") or 0),
        )
        cost = agent.get("cost_usd")
    counters: dict[str, float] = {}
    config: dict[str, Any] = {}
    try:
        metrics = json.loads((export / "metrics.json").read_text(encoding="utf-8"))
        counters = {key: float(metrics[key]) for key in COUNTERS if isinstance(metrics.get(key), (int, float))}
        config = metrics.get("config") or {}
    except (OSError, ValueError):
        pass
    return Trial(
        arm=arm,
        task=task,
        name=directory.name,
        reward=reward,
        cost=cost,
        started=str(result.get("started_at") or ""),
        seconds=_seconds(execution),
        tokens=tokens,
        counters=counters,
        exception=str(exception.get("exception_type") or ""),
        config=config,
    )


def load_arm(job_dirs: list[Path], arm: str, trials: int, prices: dict[str, dict[str, float]]) -> list[Trial]:
    """Every trial of an arm, keeping only the first ``trials`` valid ones per task, by start time."""
    found = [
        trial
        for job in job_dirs
        for directory in sorted(job.iterdir())
        if directory.is_dir() and (trial := load_trial(directory, arm, prices)) is not None
    ]
    found.sort(key=lambda t: t.started)
    kept: list[Trial] = []
    valid: dict[str, int] = {}
    for trial in found:
        if trial.reward is None:
            kept.append(trial)  # reported as an infrastructure failure, never scored
        elif valid.get(trial.task, 0) < trials:
            valid[trial.task] = valid.get(trial.task, 0) + 1
            kept.append(trial)
    return kept


def value(trial: Trial, metric: str) -> float | None:
    if trial.reward is None:
        return None
    if metric == "pass":
        return trial.reward
    if metric == "cost":
        return trial.cost
    if metric == "seconds":
        return trial.seconds
    if metric.endswith("_tokens"):
        return float(trial.tokens.get(metric.removesuffix("_tokens"), 0))
    return trial.counters.get(metric)


def task_means(trials: list[Trial], metric: str) -> dict[str, float]:
    by_task: dict[str, list[float]] = {}
    for trial in trials:
        v = value(trial, metric)
        if v is not None:
            by_task.setdefault(trial.task, []).append(v)
    return {task: fmean(values) for task, values in by_task.items()}


def evaluate(claim: Claim, spec: Spec, arms: dict[str, list[Trial]], sequential_claims: int) -> dict[str, Any]:
    treated, control = task_means(arms[claim.treatment], claim.metric), task_means(arms[claim.control], claim.metric)
    tasks = [t for t in spec.tasks if t in treated and t in control]  # paired, in the pre-registered order
    out: dict[str, Any] = {"claim": asdict(claim), "tasks": len(tasks)}
    if not tasks:
        return {**out, "p": 1.0, "note": "no task has results in both arms"}
    if claim.kind == "ratio-below":
        rows = [(treated[t], control[t]) for t in tasks]

        def ratio(sample: Sequence[tuple[float, float]]) -> float:
            denominator = sum(c for _, c in sample)
            return sum(t for t, _ in sample) / denominator if denominator else math.inf

        estimate = ratio(rows)
        low, high = bootstrap_interval(rows, ratio, seed=spec.seed)
        resampled = bootstrap(rows, ratio, seed=spec.seed + 1)
        p = (1 + sum(r >= claim.bound for r in resampled)) / (len(resampled) + 1)  # H0: ratio >= bound
        return {**out, "estimate": estimate, "interval": [low, high], "p": p}
    sign = -1.0 if claim.lower_is_better else 1.0
    diffs = [sign * (treated[t] - control[t]) for t in tasks]
    boundary = -claim.margin if claim.kind == "non-inferiority" else 0.0
    _, p, nonzero = wilcoxon([d - boundary for d in diffs], "greater")  # H0: differences centred at the boundary
    low, high = bootstrap_interval(diffs, fmean, seed=spec.seed)
    out.update(estimate=fmean(diffs), interval=[low, high], p=p, nonzero=nonzero)
    if claim.metric in BOUNDED:
        sequence = difference_cs(diffs, alpha=spec.alpha / max(1, sequential_claims))
        decided = next(
            (
                (i + 1, "holds" if lo > boundary else "fails")
                for i, (lo, hi) in enumerate(sequence)
                if lo > boundary or hi < boundary
            ),
            None,
        )
        out["sequence"] = {
            "final": list(sequence[-1]),
            "decided_after_tasks": decided[0] if decided else None,
            "decision": decided[1] if decided else "open",
        }
    return out


def arm_summary(trials: list[Trial], spec: Spec) -> dict[str, Any]:
    scored = [t for t in trials if t.reward is not None]
    passes = task_means(trials, "pass")
    costs = [t.cost for t in scored if t.cost is not None]
    solved = sum(t.reward or 0.0 for t in scored)
    out: dict[str, Any] = {
        "tasks": len(passes),
        "trials": len(scored),
        "infrastructure_failures": [f"{t.task} ({t.exception})" for t in trials if t.reward is None],
        "pass_rate": fmean(passes.values()) if passes else None,
        "pass_rate_interval": list(bootstrap_interval(list(passes.values()), fmean, seed=spec.seed))
        if passes
        else None,
        "cost_per_trial": fmean(costs) if costs else None,
        "cost_per_solved": sum(costs) / solved if costs and solved and len(costs) == len(scored) else None,
        "never_passed": sorted(task for task, rate in passes.items() if rate == 0),
        # E0 sizes the later experiments from these: how much a task's outcome varies from trial to trial, and how
        # much pass rates vary between tasks
        "within_task_variance": _within_variance(scored),
        "between_task_variance": pvariance(list(passes.values())) if len(passes) > 1 else None,
        # one entry per distinct frond configuration the arm's trials ran with: more than one means a setup error
        "configurations": sorted({json.dumps(t.config, sort_keys=True) for t in scored if t.config}),
    }
    for key in TOKEN_KEYS:
        out[f"{key}_tokens_per_trial"] = fmean(t.tokens.get(key, 0) for t in scored) if scored else None
    for key in COUNTERS:
        counted = [t.counters[key] for t in scored if key in t.counters]
        out[f"{key}_per_trial"] = fmean(counted) if counted else None
    return out


def _within_variance(trials: list[Trial]) -> float | None:
    by_task: dict[str, list[float]] = {}
    for trial in trials:
        by_task.setdefault(trial.task, []).append(trial.reward or 0.0)
    variances = [variance(rewards) for rewards in by_task.values() if len(rewards) > 1]
    return fmean(variances) if variances else None


def analyze(spec: Spec, jobs: dict[str, list[Path]], prices: dict[str, dict[str, float]]) -> dict[str, Any]:
    arms = {arm.name: load_arm(jobs.get(arm.name, []), arm.name, spec.trials_of(arm), prices) for arm in spec.arms}
    sequential = sum(1 for c in spec.claims if c.metric in BOUNDED and c.kind != "ratio-below")
    claims = {c.id: evaluate(c, spec, arms, sequential) for c in spec.claims}
    adjusted = holm({cid: result["p"] for cid, result in claims.items()})
    for cid, result in claims.items():
        result["p_holm"] = adjusted[cid]
        result["holds"] = adjusted[cid] < spec.alpha
    digest = hashlib.sha256(spec.path.read_bytes()).hexdigest()[:12] if spec.path else ""
    return {
        "experiment": spec.id,
        "title": spec.title,
        "spec": _shown(spec.path),
        "spec_sha256": digest,
        "alpha": spec.alpha,
        "excluded_tasks": list(spec.excluded),
        "arms": {name: arm_summary(trials, spec) for name, trials in arms.items()},
        "claims": claims,
        "per_task": {name: dict(sorted(task_means(trials, "pass").items())) for name, trials in arms.items()},
    }


def _shown(path: Path | None) -> str:
    """A spec's path relative to ``frond/`` when it is inside it."""
    if path is None:
        return ""
    return str(path.relative_to(BENCH.parent)) if path.is_relative_to(BENCH.parent) else str(path)


def _fmt(x: Any, digits: int = 3) -> str:
    if x is None:
        return "–"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def report(summary: dict[str, Any]) -> str:
    lines = [f"# {summary['experiment']}: {summary['title']}", ""]
    lines.append(f"Spec `{summary['spec']}` (sha256 {summary['spec_sha256']}), alpha {summary['alpha']}.")
    if summary["excluded_tasks"]:
        lines.append(f"Excluded before the run: {', '.join(summary['excluded_tasks'])}.")
    lines += ["", "| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Failed edits/trial |"]
    lines.append("|---|---|---|---|---|---|---|")
    for name, arm in summary["arms"].items():
        ci = arm["pass_rate_interval"]
        rate = f"{_fmt(arm['pass_rate'])} ({_fmt(ci[0])}–{_fmt(ci[1])})" if ci else "–"
        lines.append(
            f"| {name} | {arm['tasks']} | {arm['trials']} | {rate} | {_fmt(arm['cost_per_trial'], 2)} | "
            f"{_fmt(arm['cost_per_solved'], 2)} | {_fmt(arm['failed_edits_per_trial'], 2)} |"
        )
    if summary["claims"]:
        lines += ["", "| Claim | Kind | Tasks | Estimate (95% CI) | p | Holm p | Holds | Sequence |"]
        lines.append("|---|---|---|---|---|---|---|---|")
        for cid, c in summary["claims"].items():
            interval = c.get("interval") or [None, None]
            estimate = f"{_fmt(c.get('estimate'))} ({_fmt(interval[0])} to {_fmt(interval[1])})"
            seq = c.get("sequence")
            seq_text = f"{seq['decision']} after {seq['decided_after_tasks']} tasks" if seq else "–"
            lines.append(
                f"| {cid} | {c['claim']['kind']} | {c['tasks']} | {estimate} | {_fmt(c['p'], 4)} | "
                f"{_fmt(c['p_holm'], 4)} | {'yes' if c['holds'] else 'no'} | {seq_text} |"
            )
    for name, arm in summary["arms"].items():
        if arm["infrastructure_failures"]:
            failures = ", ".join(arm["infrastructure_failures"])
            lines += ["", f"Infrastructure failures in {name}, not scored: {failures}."]
        if arm["never_passed"]:
            lines += ["", f"Never passed in {name}: {', '.join(arm['never_passed'])}."]
    return "\n".join(lines) + "\n"


def job_dirs(spec: Spec, root: Path) -> dict[str, list[Path]]:
    """The job directories ``bench/matrix.py`` made for each arm: ``<root>/<id>-<arm>-b<batch>``."""
    return {arm.name: sorted(p for p in root.glob(f"{spec.id}-{arm.name}-b*") if p.is_dir()) for arm in spec.arms}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("spec", type=Path)
    parser.add_argument("--jobs", type=Path, help="the matrix runner's jobs directory (default: jobs/<id>)")
    parser.add_argument("--job", action="append", default=[], metavar="ARM=DIR", help="a Harbor job dir for an arm")
    parser.add_argument("--out", type=Path, help="write summary.json and report.md here")
    parser.add_argument("--failing", metavar="ARM", help="print the tasks ARM did not always pass, one per line")
    args = parser.parse_args(argv)
    spec = load(args.spec)
    jobs = job_dirs(spec, args.jobs or Path("jobs") / spec.id)
    for item in args.job:
        arm, _, directory = item.partition("=")
        jobs.setdefault(arm, []).append(Path(directory))
    summary = analyze(spec, jobs, load_prices())
    if args.failing:
        rates = summary["per_task"].get(args.failing, {})
        scored = set(rates)
        for task in spec.tasks:
            if task not in scored or rates[task] < 1.0:
                print(task)
        return 0
    text = report(summary)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
        (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
