import { atomic, compositions, freshInputs, negative, sourceOf, trainInputs } from "./cases.ts";

export function manifest() {
  return [
    ...atomic.map((spec) => ({ split: "train" as const, spec, pairs: trainInputs })),
    ...compositions.map((spec) => ({ split: "fresh" as const, spec, pairs: freshInputs })),
    { split: "negative" as const, spec: negative, pairs: freshInputs },
  ].flatMap(({ split, spec, pairs }) => {
    const entry = spec.id + ".ts";
    return pairs.map((args) => ({
      split,
      id: spec.id,
      program: { files: { [entry]: sourceOf(spec) }, entry, fn: "run", args: [...args] },
    }));
  });
}
