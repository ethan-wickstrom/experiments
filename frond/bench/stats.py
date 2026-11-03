"""Statistics for paired agent comparisons, standard library only (research.md, "Statistics").

The task is the unit. Each arm's trials on a task give that task's mean; comparisons use per-task paired differences.

Fixed-size analysis, at the end of an experiment: the exact Wilcoxon signed-rank test, percentile bootstrap intervals
over tasks, and Holm's correction across the pre-registered claims.

Sequential analysis, after every batch: a betting confidence sequence for the mean difference (Waudby-Smith and
Ramdas, "Estimating means of bounded random variables by betting", JRSS-B 2024, arXiv 2010.09686). It holds at all
times at once, so the program may look after each batch and stop as soon as a claim is decided, and the chance that
any look is wrong stays below alpha. A fixed-size test read after every batch would not keep that guarantee.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from typing import Literal

Alternative = Literal["two-sided", "greater", "less"]
_DIGITS = 9  # differences of trial means such as 2/3 - 1/3 and 1 - 2/3 must tie exactly


def midranks(values: Sequence[float]) -> list[float]:
    """Ranks from 1, with tied values sharing the mean of their positions."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def wilcoxon(diffs: Sequence[float], alternative: Alternative = "two-sided") -> tuple[float, float, int]:
    """Signed-rank test that the differences are symmetric about 0: (W+, p, number of nonzero differences).

    Zero differences are dropped, as Wilcoxon did. Tied magnitudes share midranks, and the null distribution is
    computed exactly over all 2^n sign assignments of those ranks, so ties need no normal approximation.
    "greater" tests whether the differences tend to be positive.
    """
    d = [x for x in (round(v, _DIGITS) for v in diffs) if x != 0]
    n = len(d)
    if n == 0:
        return 0.0, 1.0, 0
    doubled = [round(2 * r) for r in midranks([abs(x) for x in d])]  # midranks are multiples of 1/2
    w_plus = sum(r for r, x in zip(doubled, d, strict=True) if x > 0)
    counts = [1] + [0] * sum(doubled)  # counts[s]: sign assignments whose positive ranks sum to s
    for r in doubled:
        for s in range(len(counts) - 1, r - 1, -1):
            counts[s] += counts[s - r]
    total = 2**n
    p_greater = sum(counts[w_plus:]) / total
    p_less = sum(counts[: w_plus + 1]) / total
    p = {"greater": p_greater, "less": p_less}.get(alternative, min(1.0, 2 * min(p_greater, p_less)))
    return w_plus / 2, p, n


def bootstrap[T](
    rows: Sequence[T], statistic: Callable[[Sequence[T]], float], *, resamples: int = 10_000, seed: int = 0
) -> list[float]:
    """``statistic`` over ``resamples`` resamples of ``rows`` (tasks), drawn with replacement."""
    rng = random.Random(seed)
    n = len(rows)
    return [statistic([rows[rng.randrange(n)] for _ in range(n)]) for _ in range(resamples)]


def bootstrap_interval[T](
    rows: Sequence[T],
    statistic: Callable[[Sequence[T]], float],
    *,
    level: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap interval of ``statistic`` over ``rows`` (tasks)."""
    if not rows:
        return math.nan, math.nan
    values = sorted(bootstrap(rows, statistic, resamples=resamples, seed=seed))
    low = values[max(0, math.floor((1 - level) / 2 * resamples))]
    high = values[min(resamples - 1, math.ceil((1 + level) / 2 * resamples) - 1)]
    return low, high


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm's step-down adjustment: reject a claim when its adjusted p is below alpha (family-wise error)."""
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - i) * p))
        adjusted[name] = running
    return adjusted


def betting_cs(
    xs: Sequence[float], *, alpha: float = 0.05, grid: int = 1000, c: float = 0.5, theta: float = 0.5
) -> list[tuple[float, float]]:
    """Confidence sequence for the mean of observations in [0, 1]: one interval after each observation.

    Hedged capital with predictable plug-in bets (Waudby-Smith and Ramdas 2024, section 4). For each candidate mean m
    two gamblers bet that the mean is above and below m; m leaves the set once their combined wealth reaches 1/alpha.
    By Ville's inequality the true mean leaves it with probability at most alpha, at any time, so the intervals,
    intersected over time, hold simultaneously. Candidates are a grid; each end is widened by half a grid step.
    """
    candidates = [(k + 0.5) / grid for k in range(grid)]
    log_up = [0.0] * grid
    log_down = [0.0] * grid
    threshold = math.log(1 / alpha)
    log_theta, log_rest = math.log(theta), math.log(1 - theta)
    mean_sum, square_sum = 0.5, 0.25  # the plug-in estimates start from mean 1/2 and variance 1/4
    low, high = 0.0, 1.0
    out: list[tuple[float, float]] = []
    for t, x in enumerate(xs, start=1):
        if not 0.0 <= x <= 1.0:
            raise ValueError(f"observation {x} is outside [0, 1]")
        variance = square_sum / t  # estimated from the observations before this one, as betting requires
        bet = math.sqrt(2 * math.log(2 / alpha) / (variance * t * math.log(t + 1)))
        kept: list[float] = []
        for k, m in enumerate(candidates):
            log_up[k] += math.log1p(min(bet, c / m) * (x - m))
            log_down[k] += math.log1p(-min(bet, c / (1 - m)) * (x - m))
            a, b = log_theta + log_up[k], log_rest + log_down[k]
            top = max(a, b)
            if top + math.log(math.exp(a - top) + math.exp(b - top)) < threshold:
                kept.append(m)
        if kept:
            low = max(low, kept[0] - 0.5 / grid)
            high = min(high, kept[-1] + 0.5 / grid)
        out.append((low, high))
        mean_sum += x
        square_sum += (x - mean_sum / (t + 1)) ** 2
    return out


def difference_cs(diffs: Sequence[float], *, alpha: float = 0.05, grid: int = 1000) -> list[tuple[float, float]]:
    """``betting_cs`` for per-task differences in [-1, 1], mapped to [0, 1] and back."""
    return [(2 * lo - 1, 2 * hi - 1) for lo, hi in betting_cs([(d + 1) / 2 for d in diffs], alpha=alpha, grid=grid)]
