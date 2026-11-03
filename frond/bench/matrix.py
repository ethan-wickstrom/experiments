"""Run an experiment spec on Harbor: every arm on every task, ``trials`` times each, batch by batch, resumably.

    python -m bench.matrix bench/experiments/e0-pilot.toml --dry-run
    python -m bench.matrix bench/experiments/e0-pilot.toml [--jobs jobs/E0] [--arms opus] [--batches 1,2]

Each (batch, arm) pair is one Harbor job named ``<id>-<arm>-b<NN>`` under the jobs directory. Within a batch the
arms run back to back, and their order alternates from one batch to the next (ABBA), so slow drift in the API or the
VM falls on every arm alike. A finished job is skipped; an unfinished one is resumed with ``harbor job resume``.
``bench.prune`` runs beside each job. With ``stop_early = true`` in the spec, the run stops after any batch at which
every pass-rate claim is decided by its confidence sequence (``bench.analyze``).

Only failures before the agent starts are retried. Harbor reruns a retried trial under the same name, overwriting
the first attempt, so retrying an agent's own failure would keep the better of two outcomes.

Before each Harbor job the runner adds what every trial under ``jobs/`` has cost to the most the job could cost,
and stops if that would pass the program's cap in ``budget.toml`` (``bench.budget``, D43).

A jobs directory belongs to one version of the spec and of frond's source: resuming it after either changed is
refused, since the experiment would mix two setups under one name (F8). The run exits 1 if any Harbor job failed
(F6); the analysis reports the tasks still short of their trials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analyze import analyze, call_cost, job_dirs, load_prices
from .budget import Budget, has_guess, job_estimate, load_budget, spending
from .prune import prune_while
from .spec import BENCH, Arm, Spec, load

FROND = BENCH.parent
# The dspy extra and pin serve Harbor's own dspy-rlm agent (E11), which runs in Harbor's process and still passes
# max_iterations, which DSPy renamed in 3.3. frond installs its own pinned DSPy in the task container.
HARBOR = ("uvx", "--from", "harbor[dspy]==0.25.0", "--with", "dspy>=3.1.3,<3.3", "harbor")
OVERLAY = BENCH / "compose" / "egress-ca.yaml"
RETRY_ON = (  # failures before the agent runs (Harbor's "sandbox failed" class, and docker compose errors)
    "EnvironmentStartTimeoutError",
    "SandboxBuildFailedError",
    "AgentSetupTimeoutError",
    "HealthcheckError",
    "RuntimeError",
)
KEYS = {"anthropic/": "ANTHROPIC_API_KEY", "openai/": "OPENAI_API_KEY", "gemini/": "GEMINI_API_KEY"}
# Other names a key may be stored under in the environment: the owner keeps the Anthropic key as CLAUDE_API_KEY (REQ-1)
ALIASES = {"ANTHROPIC_API_KEY": ("CLAUDE_API_KEY",)}


def with_aliases(env: dict[str, str]) -> dict[str, str]:
    """``env`` with each provider key set from an alias when it is missing, under the name Harbor and frond read."""
    out = dict(env)
    for key, names in ALIASES.items():
        if not out.get(key):
            found = next((out[name] for name in names if out.get(name)), None)
            if found is not None:
                out[key] = found
    return out


PROBE_IMAGE = "mirror.gcr.io/library/alpine:3.20"
SOURCES = ("src", "bench/frond_harbor.py", "pyproject.toml", "uv.lock")  # what a trial's frond is built from


@dataclass(frozen=True)
class Cell:
    batch: int
    arm: Arm
    tasks: tuple[str, ...]

    def name(self, spec: Spec) -> str:
        return f"{spec.id}-{self.arm.name}-b{self.batch:02d}"


def cells(spec: Spec) -> list[Cell]:
    out: list[Cell] = []
    for batch, tasks in enumerate(spec.batches(), start=1):
        order = spec.arms if batch % 2 else tuple(reversed(spec.arms))  # ABBA across batches
        out.extend(Cell(batch, arm, tasks) for arm in order)
    return out


def egress_ca() -> Path | None:
    """The CA bundle task containers must trust, on a host that re-terminates TLS (D27)."""
    for value in (os.environ.get("FROND_EGRESS_CA"), os.environ.get("SSL_CERT_FILE")):
        if value and Path(value).is_file():
            return Path(value)
    return None


def command(spec: Spec, cell: Cell, jobs: Path, ca: Path | None) -> list[str]:
    org = spec.dataset.split("/", 1)[0]
    argv = [*HARBOR, "run", "-d", spec.dataset, "-a", cell.arm.agent, "-e", "docker"]
    argv += ["-k", str(spec.trials_of(cell.arm)), "-n", str(spec.concurrency)]
    argv += ["--job-name", cell.name(spec), "-o", str(jobs)]
    argv += ["--delete", "--max-retries", "2"]
    for name in RETRY_ON:
        argv += ["--retry-include", name]
    if cell.arm.model:
        argv += ["-m", cell.arm.model]
    for key, value in cell.arm.options.items():
        argv += ["--ak", f"{key}={value}"]
    if spec.timeout_multiplier != 1.0:
        argv += ["--timeout-multiplier", str(spec.timeout_multiplier)]
    if ca is not None:
        argv += ["--extra-docker-compose", str(OVERLAY)]
    for task in cell.tasks:
        argv += ["-i", f"{org}/{task}"]
    return argv


def state(jobs: Path, name: str) -> str:
    """'new', 'partial' or 'done', from the job's own result file."""
    directory = jobs / name
    if not directory.is_dir():
        return "new"
    try:
        result = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "partial"
    stats = result.get("stats") or {}
    pending = (stats.get("n_pending_trials") or 0) + (stats.get("n_running_trials") or 0)
    return "done" if result.get("finished_at") and not pending else "partial"


def environment(ca: Path | None) -> dict[str, str]:
    env = with_aliases(dict(os.environ))
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(BENCH), env.get("PYTHONPATH", "")) if p)
    if ca is not None:
        env["FROND_EGRESS_CA"] = str(ca)
    return env


def exec_umask() -> str:
    """The umask of a process started by ``docker exec``, which is how Harbor runs agents, solutions and tests.

    It is the daemon's umask, not the container's; "unknown" when no probe container could start (G26).
    """
    started = subprocess.run(
        ["docker", "run", "-d", "--rm", PROBE_IMAGE, "sleep", "60"], capture_output=True, text=True, check=False
    )
    if started.returncode != 0:
        return "unknown"
    container = started.stdout.strip()
    try:
        shown = subprocess.run(
            ["docker", "exec", container, "sh", "-c", "umask"], capture_output=True, text=True, check=False
        )
        return shown.stdout.strip() or "unknown"
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)


def harbor_ready(attempts: int = 3, timeout: float = 300.0) -> bool:
    """Whether Harbor's tool environment installs and starts, tried a few times with a timeout each.

    uvx installs Harbor's environment on first use, with no timeout of its own on a download that stalls: on
    2026-11-03 one hung for minutes before the smoke run's job could start, and would have held a sweep just as long
    (G32). A fresh attempt opens new connections; the environment is cached once one succeeds.
    """
    for _ in range(attempts):
        try:
            done = subprocess.run([*HARBOR, "--version"], capture_output=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            continue
        if done.returncode == 0:
            return True
    return False


def models_of(arm: Arm) -> list[str]:
    """The models a frond arm calls: its own, and the sub-model it names or frond picks for it."""
    if not arm.model:
        return []
    if not arm.agent.startswith("frond"):
        return [arm.model]
    from frond.agent.lm import resolve_models  # frond's own rule for the default sub-model

    choice = resolve_models(arm.model, arm.options.get("sub_model"))
    return list(dict.fromkeys([choice.main, choice.sub]))


def preflight(spec: Spec, ca: Path | None) -> list[str]:
    """What would make every trial fail, or bias every arm alike, checked before spending anything."""
    problems: list[str] = []
    if subprocess.run(["docker", "info"], capture_output=True, check=False).returncode != 0:
        problems.append("Docker is not running: run scripts/dev-env.sh")
    else:
        umask = exec_umask()  # unmeasured counts as wrong: a run that cannot check its environment does not start
        if umask == "unknown":
            problems.append(
                f"the umask of docker exec could not be measured, because {PROBE_IMAGE} did not start: "
                "check Docker and the network (G26)"
            )
        elif umask != "0022":
            problems.append(
                f"docker exec runs with umask {umask}, not 0022, so files agents and tests create get other modes "
                "than on a standard host (G26): stop dockerd and run scripts/dev-env.sh"
            )
    if not harbor_ready():
        problems.append(f"Harbor's environment did not install or start: try `{shlex.join([*HARBOR, '--version'])}`")
    budget, prices = load_budget(), load_prices()
    for arm in spec.arms:
        problems.extend(
            f"arm {arm.name}: no price for {model} in bench/prices.toml, so its cost is unknown"
            for model in models_of(arm)
            if call_cost(model, {}, prices) is None
        )
        if arm.model and not has_guess(arm.model, budget):
            problems.append(f"arm {arm.name}: no per-trial guess for {arm.model} in bench/budget.toml (D43)")
        for prefix, key in KEYS.items():
            if arm.model and arm.model.startswith(prefix) and not with_aliases(dict(os.environ)).get(key):
                problems.append(f"arm {arm.name} needs {key} (ledger REQ-1)")
    if ca is None:
        print("note: no egress CA is set; on a host that re-terminates TLS, set FROND_EGRESS_CA (D27)", file=sys.stderr)
    return problems


def source_digest() -> str:
    """A digest of what a trial's frond is built from, its files' bytes whatever git's state (F8)."""
    digest = hashlib.sha256()
    for entry in SOURCES:
        path = FROND / entry
        files = (
            sorted(f for f in path.rglob("*") if f.is_file() and "__pycache__" not in f.parts)
            if path.is_dir()
            else [path]
        )
        for file in files:
            if file.is_file():
                digest.update(f"{file.relative_to(FROND)}\0".encode() + file.read_bytes() + b"\0")
    return digest.hexdigest()


def resumable(manifest: dict[str, Any], current: dict[str, Any], allow_changed_source: bool) -> list[str]:
    """Why the jobs a manifest records cannot be continued by this spec and source (nothing when they can)."""
    if not manifest.get("runs"):
        return []
    problems = []
    if manifest.get("spec_sha256") and manifest["spec_sha256"] != current["spec_sha256"]:
        problems.append("its jobs ran another version of this spec: give this one a new --jobs directory")
    if manifest.get("source_sha256") not in (None, current["source_sha256"]) and not allow_changed_source:
        problems.append(
            "its jobs ran another version of frond's source: use a new --jobs directory, or pass "
            "--allow-changed-source when the change cannot affect the arms"
        )
    return problems


def remaining(job: Path, tasks: Sequence[str], trials: int) -> int:
    """How many trials of a job have yet to finish."""
    done = _finished(job)
    return sum(max(0, trials - done.get(task, 0)) for task in tasks)


def pending(job: Path, tasks: Sequence[str], trials: int) -> set[str]:
    """The tasks of a job with fewer than ``trials`` finished trials, from Harbor's per-trial result.json."""
    done = _finished(job)
    return {task for task in tasks if done.get(task, 0) < trials}


def _finished(job: Path) -> dict[str, int]:
    done: dict[str, int] = {}
    for result in job.glob("*/result.json"):
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("finished_at"):  # named as load_trial names it
            task = str((data.get("task_id") or {}).get("name") or data.get("task_name") or "").split("/")[-1]
            done[task] = done.get(task, 0) + 1
    return done


def affordable(spec: Spec, cell: Cell, jobs: Path, budget: Budget) -> tuple[bool, str]:
    """Whether the program's cap allows starting this cell's job, and the spending it was judged on. Every trial
    under ``jobs/`` and under this run's jobs directory counts, wherever it is nested; a trial whose cost cannot be
    told stops the run, since the cap could not be kept."""
    spent = spending([FROND / "jobs", jobs], load_prices())
    if spent.unknown:
        return False, f"cannot count the cost of {len(spent.unknown)} trials ({', '.join(spent.unknown[:3])})"
    trials = remaining(jobs / cell.name(spec), cell.tasks, spec.trials_of(cell.arm))
    estimate = job_estimate(cell.arm, trials, spent.worst, budget)
    text = f"spent ${spent.total:.2f} of ${budget.usd:.2f}; {cell.name(spec)} could cost up to ${estimate:.2f}"
    return spent.total + estimate <= budget.usd, text


def provenance(spec: Spec) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=FROND, capture_output=True, text=True, check=False).stdout.strip()

    return {
        "spec": str(spec.path),
        "spec_sha256": hashlib.sha256(spec.path.read_bytes()).hexdigest() if spec.path else "",
        "frond_commit": git("rev-parse", "HEAD"),
        "frond_dirty": bool(git("status", "--porcelain")),
        "source_sha256": source_digest(),
        "harbor": " ".join(HARBOR),
    }


def run_cell(argv: list[str], env: dict[str, str], log: Path, keep: Callable[[], set[str]] | None = None) -> int:
    """Run one Harbor job, pruning unused images beside it except those of the tasks ``keep`` names."""
    with open(log, "a", encoding="utf-8") as out:
        process = subprocess.Popen(argv, cwd=FROND, env=env, stdout=out, stderr=subprocess.STDOUT)
        pruner = threading.Thread(
            target=prune_while, args=(process.pid, 60.0, str(log.with_suffix(".prune.log")), keep), daemon=True
        )
        pruner.start()
        return process.wait()


def decided(spec: Spec, jobs: Path) -> bool:
    """Whether every pass-rate claim's confidence sequence has reached a decision."""
    summary = analyze(spec, job_dirs(spec, jobs), load_prices())
    sequences = [c["sequence"] for c in summary["claims"].values() if "sequence" in c]
    return bool(sequences) and all(s["decision"] != "open" for s in sequences)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("spec", type=Path)
    parser.add_argument("--jobs", type=Path, help="where Harbor writes the jobs (default: jobs/<id>)")
    parser.add_argument("--arms", help="comma-separated arm names to run (default: all)")
    parser.add_argument("--batches", help="comma-separated batch numbers to run (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="print each job's state and command, run nothing")
    parser.add_argument(
        "--allow-changed-source",
        action="store_true",
        help="resume jobs that ran another version of frond's source (recorded in matrix.json)",
    )
    args = parser.parse_args(argv)
    spec = load(args.spec.resolve())
    jobs = (args.jobs or FROND / "jobs" / spec.id).resolve()
    arms = set(args.arms.split(",")) if args.arms else {a.name for a in spec.arms}
    batches = {int(b) for b in args.batches.split(",")} if args.batches else None
    ca = egress_ca()
    chosen = [c for c in cells(spec) if c.arm.name in arms and (batches is None or c.batch in batches)]
    print(f"{spec.id}: {len(spec.tasks)} tasks in {len(spec.batches())} batches, arms {', '.join(sorted(arms))}")
    if args.dry_run:
        for cell in chosen:
            name = cell.name(spec)
            print(f"\n[{state(jobs, name)}] {name}: {len(cell.tasks)} tasks")
            print(f"  {shlex.join(command(spec, cell, jobs, ca))}")
        return 0
    problems = preflight(spec, ca)
    if problems:
        print("cannot run:\n- " + "\n- ".join(problems), file=sys.stderr)
        return 2
    jobs.mkdir(parents=True, exist_ok=True)
    manifest_path = jobs / "matrix.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"runs": []}
    current = provenance(spec)
    refused = resumable(manifest, current, args.allow_changed_source)
    if refused:
        print(f"cannot resume {jobs}:\n- " + "\n- ".join(refused), file=sys.stderr)
        return 2
    manifest.update(current)
    env = environment(ca)
    budget = load_budget()
    failed: list[str] = []
    for i, cell in enumerate(chosen):
        name = cell.name(spec)
        status = state(jobs, name)
        if status != "done":
            # each Harbor job builds frond's wheel anew, so a source edited during the run would reach later arms
            if not args.allow_changed_source and source_digest() != current["source_sha256"]:
                print(f"stopping before {name}: frond's source changed during the run (F8, D42)", file=sys.stderr)
                manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
                return 2
            allowed, spending_text = affordable(spec, cell, jobs, budget)
            print(f"budget: {spending_text}", flush=True)
            if not allowed:
                print(f"stopping before {name}: it could pass the cap in bench/budget.toml (D43)", file=sys.stderr)
                manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
                return 4
            argv = command(spec, cell, jobs, ca)
            if status == "partial":
                argv = [*HARBOR, "job", "resume", "-p", str(jobs / name)]
            started = time.time()
            print(f"{time.strftime('%H:%M:%S')} {name} ({status}): {len(cell.tasks)} tasks", flush=True)
            trials = spec.trials_of(cell.arm)
            run = {
                "job": name,
                "argv": argv,
                "started": started,
                "exit": None,  # recorded before Harbor starts, so a run killed midway still binds the directory
                "source_sha256": current["source_sha256"],
                "allowed_changed_source": args.allow_changed_source,
            }
            manifest["runs"].append(run)
            manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
            code = run_cell(
                argv,
                env,
                jobs / f"{name}.log",
                lambda job=jobs / name, tasks=cell.tasks, k=trials: pending(job, tasks, k),
            )
            run.update(seconds=round(time.time() - started), exit=code)
            if code != 0:
                failed.append(name)
            manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
        batch_done = i + 1 == len(chosen) or chosen[i + 1].batch != cell.batch
        # an early stop reads a whole batch: never one where a job failed or left trials unfinished
        complete = batch_done and all(
            c.name(spec) not in failed and remaining(jobs / c.name(spec), c.tasks, spec.trials_of(c.arm)) == 0
            for c in chosen
            if c.batch == cell.batch
        )
        if complete and spec.stop_early and decided(spec, jobs):
            print(f"every pass-rate claim is decided after batch {cell.batch}: stopping (stop_early)")
            break
    if failed:  # Harbor exits 0 when a job finishes, whatever its trials did: a failure is the job's own
        print(f"Harbor failed in {', '.join(failed)}: see their logs; rerunning resumes them", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
