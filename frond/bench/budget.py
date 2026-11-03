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


def spending(experiments: list[Path], prices: dict[str, dict[str, float]]) -> tuple[float, dict[str, float]]:
    """USD that every trial in these experiments' jobs directories cost (<experiment>/<job>/<trial>), and the most one
    trial of each model cost, by the model frond recorded."""
    total, worst = 0.0, {}
    results = sorted({r.resolve() for root in experiments for r in root.glob("*/*/result.json")})
    for result in results:
        if not (result.parent / "agent").is_dir():
            continue  # not a trial
        trial = load_trial(result.parent, "", prices)
        if trial is None or trial.cost is None:
            continue
        total += trial.cost
        model = str(trial.config.get("model") or "")
        if model:
            worst[model] = max(worst.get(model, 0.0), trial.cost)
    return total, worst


def has_guess(model: str, budget: Budget) -> bool:
    return _key(model, list(budget.guess)) is not None


def job_estimate(arm: Arm, trials: int, worst: dict[str, float], budget: Budget) -> float:
    """The most ``trials`` trials of ``arm`` are assumed to cost; 0 for an arm with no model (the oracle)."""
    if not arm.model or trials <= 0:
        return 0.0
    steps = max(1.0, float(arm.options.get("max_steps", 40)) / 40)
    key = _key(arm.model, list(budget.guess))
    guess = budget.guess[key] * steps if key is not None else 0.0
    measured = worst.get(arm.model, 0.0)
    return trials * max(guess, measured) * budget.margin if measured else trials * guess
