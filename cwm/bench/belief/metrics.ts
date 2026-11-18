import type { Atom, Example, Forecast } from "./types.ts";

export function decision(dist: Atom[]) {
  const sorted = [...dist].sort((a, b) => b.prob - a.prob);
  return sorted[0] && (!sorted[1] || sorted[0].prob - sorted[1].prob > 1e-12)
    ? sorted[0].state
    : undefined;
}

export function measure(rows: Example[], predict: Forecast) {
  let right = 0,
    wrong = 0,
    brier = 0,
    nll = 0;
  const cells = new Map<string, boolean>();
  for (const { input, after } of rows) {
    const key = JSON.stringify([input.setup, input.write]),
      truth = JSON.stringify(after);
    const dist = predict(input);
    const byState = new Map(dist.map((a) => [JSON.stringify(a.state), a.prob]));
    if (
      byState.size !== dist.length ||
      dist.some((a) => !Number.isFinite(a.prob) || a.prob <= 0) ||
      (dist.length && Math.abs(dist.reduce((s, a) => s + a.prob, 0) - 1) > 1e-8)
    )
      throw new Error("Malformed predictive distribution");
    const p = byState.get(truth) ?? 0;
    const guess = decision(dist),
      correct = JSON.stringify(guess) === truth;
    if (correct) right++;
    else if (guess) wrong++;
    cells.set(key, (cells.get(key) ?? true) && correct);
    brier += dist.length ? 1 - 2 * p + dist.reduce((s, a) => s + a.prob ** 2, 0) : 2;
    nll -= Math.log(p);
  }
  if (!rows.length) throw new Error("Empty evaluation split");
  return {
    right,
    wrong,
    abstain: rows.length - right - wrong,
    perfectCells: [...cells.values()].filter(Boolean).length,
    brier: brier / rows.length,
    nll: Number.isFinite(nll) ? nll / rows.length : "Infinity",
  };
}
