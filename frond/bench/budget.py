"""The program's spending cap (ledger REQ-1, decision D43).

Spent is every trial under ``jobs/`` at list prices: frond's calls from its export, other agents' from Harbor's
``cost_usd`` (``analyze.load_trial``). Before each Harbor job, ``bench.matrix`` adds the most the job could cost and
refuses to start it if the total would pass the cap in ``budget.toml``. A job is assumed to cost its remaining trials
times the most one trial of its model has cost so far, scaled by the margin, or, before any trial of the model, the
per-trial guess scaled by the arm's step limit. Within a job, the key's Console spend limit is what stops it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .analyze import load_trial
from .spec import BENCH, Arm

BUDGET = BENCH / "budget.toml"


@dataclass(frozen=True)
class Budget:
    usd: float
    margin: float
    guess: dict[str, float]  # prices.toml-style model key -> USD per trial at 40 steps, before one is measured


def load_budget(path: Path = BUDGET) -> Budget:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Budget(float(data["usd"]), float(data.get("margin", 1.5)), {k: float(v) for k, v in data["guess"].items()})


def _key(model: str, keys: list[str]) -> str | None:
    """The longest key the model's name starts with, after any "provider/" prefix (as prices.toml matches)."""
    name = model.split("/")[-1].lower()
    matches = [key for key in keys if name.startswith(key)]
    return max(matches, key=len) if matches else None


@dataclass
class Spending:
    total: float  # USD every trial cost
    worst: dict[str, float]  # model -> the most one trial cost
    unknown: list[str]  # trials of a model whose cost cannot be told: a call with no price, or none reported


def spending(roots: list[Path], prices: dict[str, dict[str, float]]) -> Spending:
    """What every trial anywhere under ``roots`` cost (a trial is a directory with ``result.json`` and ``agent/``),
    each counted once, and the most one trial of each model cost, by the model Harbor gave its agent, frond or not."""
    out = Spending(0.0, {}, [])
    results = sorted({r.resolve() for root in roots if root.is_dir() for r in root.rglob("result.json")})
    for result in results:
        if not (result.parent / "agent").is_dir():
            continue  # a job's result, not a trial's
        trial = load_trial(result.parent, "", prices)
        if trial is None:
            continue
        if trial.cost is None:
            if trial.model:  # spent something that cannot be counted: the cap cannot be kept (fail closed)
                out.unknown.append(result.parent.name)
            continue
        out.total += trial.cost
        out.worst[trial.model] = max(out.worst.get(trial.model, 0.0), trial.cost)
    return out


def has_guess(model: str, budget: Budget) -> bool:
    return _key(model, list(budget.guess)) is not None


def job_estimate(arm: Arm, trials: int, worst: dict[str, float], budget: Budget) -> float:
    """The most ``trials`` trials of ``arm`` are assumed to cost; 0 for an arm with no model (the oracle)."""
    if not arm.model or trials <= 0:
        return 0.0
    steps = max(1.0, float(arm.options.get("max_steps", 40)) / 40)
    key = _key(arm.model, list(budget.guess))
    guess = budget.guess[key] * steps if key is not None else 0.0
    measured = max(worst.get(arm.model, 0.0), worst.get("", 0.0))  # "": a cost with no model named: assume it
    return trials * max(guess, measured) * budget.margin if measured else trials * guess
