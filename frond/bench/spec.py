"""Experiment specs: what an experiment runs and what it claims, fixed in a TOML file before it runs.

``bench/matrix.py`` runs a spec and ``bench/analyze.py`` evaluates it, from the same file, so the analysis is
pre-registered: the tasks, their order, the arms, the trials and every claim with its test and margin are committed
before the first trial. A spec looks like this (see ``bench/experiments/`` for real ones):

    id = "E6"
    title = "The per-step cache layout cuts cost at least 3x without lowering pass rate"
    dataset = "terminal-bench/terminal-bench@4.0.0"
    tasks = "datasets/terminal-bench@4.0.0.txt"   # a file of task names, relative to bench/, or a list
    exclude = ["results/2026-11-03-e0a-oracle/oracle-failures.txt"]
    sample = 22                                    # optional: a seeded sample of the remaining tasks
    trials = 3
    batch = 11                                     # tasks per batch; arms alternate within each batch
    seed = 6
    concurrency = 2
    alpha = 0.05
    stop_early = true                              # stop once every pass-rate claim is decided

    [[arms]]
    name = "frond"
    agent = "frond_harbor:Frond"
    model = "anthropic/claude-opus-5-5"
    options = { layout = "turns", effort = "high" }

    [[claims]]
    id = "H6-pass"
    metric = "pass"
    treatment = "frond"
    control = "chat"
    kind = "non-inferiority"   # or "superiority", or "ratio-below" (treatment/control of the metric's total)
    margin = 0.05
"""

from __future__ import annotations

import random
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BENCH = Path(__file__).resolve().parent
KINDS = ("superiority", "non-inferiority", "ratio-below")
BOUNDED = ("pass",)  # metrics in [0, 1] per task, which the sequential analysis covers


@dataclass(frozen=True)
class Arm:
    name: str
    agent: str  # a Harbor agent name ("oracle", "claude-code", "terminus-2") or an import path
    model: str | None = None
    options: dict[str, str] = field(default_factory=dict)  # Harbor agent kwargs (--ak key=value)
    trials: int | None = None  # this arm's trials per task, when it differs from the spec's


@dataclass(frozen=True)
class Claim:
    id: str
    metric: str
    treatment: str
    control: str
    kind: str
    margin: float = 0.0  # non-inferiority: how much worse the treatment may be
    bound: float = 1.0  # ratio-below: the ratio the upper interval end must stay under
    lower_is_better: bool = False  # e.g. failed edits; pass is higher-is-better


@dataclass(frozen=True)
class Spec:
    id: str
    title: str
    dataset: str
    tasks: tuple[str, ...]  # in run order: a seeded permutation of the chosen tasks
    trials: int
    batch: int
    seed: int
    concurrency: int
    alpha: float
    arms: tuple[Arm, ...]
    claims: tuple[Claim, ...]
    excluded: tuple[str, ...] = ()  # tasks left out, with the reason recorded by the exclusion file
    timeout_multiplier: float = 1.0
    agent_timeout_multiplier: float = 1.0  # of each task's agent timeout; TB 4.0 specs set 0.25: 2 hours (D59)
    stop_early: bool = False  # stop after a batch at which every pass-rate claim's confidence sequence decides
    path: Path | None = None

    def batches(self) -> list[tuple[str, ...]]:
        return [self.tasks[i : i + self.batch] for i in range(0, len(self.tasks), self.batch)]

    def trials_of(self, arm: Arm) -> int:
        return arm.trials if arm.trials is not None else self.trials

    def arm(self, name: str) -> Arm:
        for arm in self.arms:
            if arm.name == name:
                return arm
        raise KeyError(f"{self.id} has no arm {name!r}")


def _names(value: Any, base: Path) -> list[str]:
    """Task names from a list, or from a file with one name per line (# comments allowed)."""
    if isinstance(value, list):
        return [str(v) for v in value]
    lines = (base / str(value)).read_text(encoding="utf-8").splitlines()
    return [line.split("#", 1)[0].strip() for line in lines if line.split("#", 1)[0].strip()]


def load(path: Path) -> Spec:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    seed = int(data.get("seed", 0))
    chosen = _names(data["tasks"], BENCH)
    dropped: set[str] = set()
    for item in data.get("exclude", []):  # task names, or files of task names
        dropped.update(_names(item, BENCH) if str(item).endswith(".txt") else [str(item)])
    excluded = sorted(dropped & set(chosen))
    remaining = sorted(set(chosen) - dropped)
    if "sample" in data:
        remaining = sorted(random.Random(seed).sample(remaining, int(data["sample"])))
    order = list(remaining)
    random.Random(seed).shuffle(order)  # the pre-registered run order, which the sequential analysis follows
    arms = tuple(
        Arm(
            a["name"],
            a["agent"],
            a.get("model"),
            {k: str(v) for k, v in a.get("options", {}).items()},
            int(a["trials"]) if "trials" in a else None,
        )
        for a in data["arms"]
    )
    claims = tuple(Claim(**c) for c in data.get("claims", []))
    names = {a.name for a in arms}
    if len(names) != len(arms):
        raise ValueError(f"{path}: arm names repeat")
    if len({c.id for c in claims}) != len(claims):  # results are keyed by id: a repeat would drop a claim (F7)
        raise ValueError(f"{path}: claim ids repeat")
    for claim in claims:
        if claim.kind not in KINDS:
            raise ValueError(f"{path}: claim {claim.id} has kind {claim.kind!r}; expected one of {KINDS}")
        if {claim.treatment, claim.control} - names:
            raise ValueError(f"{path}: claim {claim.id} compares arms that the spec does not define")
    return Spec(
        id=data["id"],
        title=data.get("title", ""),
        dataset=data["dataset"],
        tasks=tuple(order),
        trials=int(data.get("trials", 1)),
        batch=int(data.get("batch", len(order) or 1)),
        seed=seed,
        concurrency=int(data.get("concurrency", 1)),
        alpha=float(data.get("alpha", 0.05)),
        arms=arms,
        claims=claims,
        excluded=tuple(excluded),
        timeout_multiplier=float(data.get("timeout_multiplier", 1.0)),
        agent_timeout_multiplier=float(data.get("agent_timeout_multiplier", 1.0)),
        stop_early=bool(data.get("stop_early", False)),
        path=path,
    )
