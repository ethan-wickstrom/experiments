import * as S from "effect/Schema";
import { fit } from "./model.ts";
import { fitJoint } from "./joint.ts";
import { cover, uniform } from "./curriculum.ts";
import { Example, Input, digest, list, strict, type Atom, type Forecast } from "./types.ts";

function lookup(train: Example[]): Forecast {
  const table = new Map<string, Map<string, Atom>>();
  for (const { input, after } of train) {
    const key = digest([input]),
      y = JSON.stringify(after),
      counts = table.get(key) ?? new Map<string, Atom>();
    counts.set(y, { state: after, prob: (counts.get(y)?.prob ?? 0) + 1 });
    table.set(key, counts);
  }
  return (x) => {
    const counts = [...(table.get(digest([x]))?.values() ?? [])];
    const n = counts.reduce((s, a) => s + a.prob, 0);
    return counts.map((a) => ({ ...a, prob: a.prob / n }));
  };
}

export function forecasts(train: Example[], inputs: Input[]) {
  const models: { name: string; predictions: Atom[][] }[] = [];
  function record(name: string, predict: Forecast, masked = false) {
    models.push({
      name,
      predictions: inputs.map((x) => predict(masked ? { ...x, signal: null } : x)),
    });
  }
  const factor = fit(train);
  const selected = cover(train.map((e) => e.input));
  const budget = selected.length;
  record("cover-" + budget, fit(selected.map((i) => train[i]!)));
  for (let seed = 1; seed <= 20; seed++)
    record(
      "uniform-" + budget + "-" + seed,
      fit(uniform(train.length, budget, seed).map((i) => train[i]!)),
    );
  record("persist", (x) => [{ state: x.before, prob: 1 }]);
  record("joint-lookup", lookup(train));
  record("factor", factor);
  record("factor-masked", factor, true);
  record("no-labels", fit([]));
  record(
    "flipped-training-signal",
    fit(
      train.map((e) => ({
        ...e,
        input: { ...e.input, signal: e.input.signal === null ? null : !e.input.signal },
      })),
    ),
  );
  for (const seed of [1, 2, 3]) {
    const joint = fitJoint(train, seed);
    record("mlp-" + seed, joint);
    record("mlp-masked-" + seed, joint, true);
  }
  return { digest: digest(inputs), models };
}

if (import.meta.main) {
  const [train, inputs] = process.argv.slice(2);
  if (!train || !inputs) throw new Error("Usage: bun predict.ts TRAIN.json INPUTS.json");
  console.log(
    JSON.stringify(
      forecasts(
        S.decodeUnknownSync(list(Example), strict)(await Bun.file(train).json()),
        S.decodeUnknownSync(list(Input), strict)(await Bun.file(inputs).json()),
      ),
    ),
  );
}
