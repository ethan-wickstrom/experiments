import assert from "node:assert/strict";
import * as S from "effect/Schema";
import { Bundle, Input, Labels, digest, list, strict, type Atom } from "./types.ts";
import { decision, measure } from "./metrics.ts";
const [xs, bundle, labels] = process.argv.slice(2);
if (!xs || !bundle || !labels)
  throw new Error("Usage: bun score.ts INPUTS.json FORECASTS.json LABELS.json");
const inputs = S.decodeUnknownSync(list(Input), strict)(await Bun.file(xs).json());
const guesses = S.decodeUnknownSync(Bundle, strict)(await Bun.file(bundle).json());
const truth = S.decodeUnknownSync(Labels, strict)(await Bun.file(labels).json());
assert.equal(digest(inputs), guesses.digest);
assert.equal(guesses.digest, truth.digest);
assert.equal(inputs.length, truth.states.length);
const rows = inputs.map((input, i) => ({ input, after: truth.states[i]! }));
const twins = Map.groupBy(
  inputs.map((x, i) => ({ x, i })),
  ({ x }) => digest([{ ...x, signal: null }]),
);
const scores = guesses.models.map(({ name, predictions }) => {
  assert.equal(predictions.length, rows.length);
  const dist = new Map<Input, Atom[]>(inputs.map((x, i) => [x, predictions[i]!]));
  const predict = (x: Input) => dist.get(x)!;
  const cells = [...Map.groupBy(rows, (e) => JSON.stringify([e.input.setup, e.input.write]))].map(
    ([source, group]) => ({ source, ...measure(group, predict) }),
  );
  let swappedPairs = 0;
  for (const pair of twins.values()) {
    assert.equal(pair.length, 2);
    const [a, b] = pair as [{ x: Input; i: number }, { x: Input; i: number }];
    const sa = decision(predict(a.x)),
      sb = decision(predict(b.x));
    if (
      sa &&
      sb &&
      JSON.stringify(sa[0]) === JSON.stringify(sb[0]) &&
      JSON.stringify(sa[1]) !== JSON.stringify(sb[1]) &&
      JSON.stringify(sa) === JSON.stringify(truth.states[a.i]) &&
      JSON.stringify(sb) === JSON.stringify(truth.states[b.i])
    )
      swappedPairs++;
  }
  return { name, ...measure(rows, predict), swappedPairs, cells };
});
console.log(JSON.stringify({ inputsSHA256: truth.digest, scores }, null, 2));
