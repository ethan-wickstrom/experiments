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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analyze import analyze, job_dirs, load_prices
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
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(BENCH), env.get("PYTHONPATH", "")) if p)
    if ca is not None:
        env["FROND_EGRESS_CA"] = str(ca)
    return env


def preflight(spec: Spec, ca: Path | None) -> list[str]:
    """What would make every trial fail, checked before spending anything."""
    problems: list[str] = []
    if subprocess.run(["docker", "info"], capture_output=True, check=False).returncode != 0:
        problems.append("Docker is not running: run scripts/dev-env.sh")
    for arm in spec.arms:
        for prefix, key in KEYS.items():
            if arm.model and arm.model.startswith(prefix) and not os.environ.get(key):
                problems.append(f"arm {arm.name} needs {key} (ledger REQ-1)")
    if ca is None:
        print("note: no egress CA is set; on a host that re-terminates TLS, set FROND_EGRESS_CA (D27)", file=sys.stderr)
    return problems


def provenance(spec: Spec) -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=FROND, capture_output=True, text=True, check=False).stdout.strip()

    return {
        "spec": str(spec.path),
        "spec_sha256": hashlib.sha256(spec.path.read_bytes()).hexdigest() if spec.path else "",
        "frond_commit": git("rev-parse", "HEAD"),
        "frond_dirty": bool(git("status", "--porcelain")),
        "harbor": " ".join(HARBOR),
    }


def run_cell(argv: list[str], env: dict[str, str], log: Path) -> int:
    with open(log, "a", encoding="utf-8") as out:
        process = subprocess.Popen(argv, cwd=FROND, env=env, stdout=out, stderr=subprocess.STDOUT)
        pruner = threading.Thread(
            target=prune_while, args=(process.pid, 60.0, str(log.with_suffix(".prune.log"))), daemon=True
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
    manifest.update(provenance(spec))
    env = environment(ca)
    for i, cell in enumerate(chosen):
        name = cell.name(spec)
        status = state(jobs, name)
        if status != "done":
            argv = command(spec, cell, jobs, ca)
            if status == "partial":
                argv = [*HARBOR, "job", "resume", "-p", str(jobs / name)]
            started = time.time()
            print(f"{time.strftime('%H:%M:%S')} {name} ({status}): {len(cell.tasks)} tasks", flush=True)
            code = run_cell(argv, env, jobs / f"{name}.log")
            manifest["runs"].append(
                {"job": name, "argv": argv, "started": started, "seconds": round(time.time() - started), "exit": code}
            )
            manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
        batch_done = i + 1 == len(chosen) or chosen[i + 1].batch != cell.batch
        if batch_done and spec.stop_early and decided(spec, jobs):
            print(f"every pass-rate claim is decided after batch {cell.batch}: stopping (stop_early)")
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
