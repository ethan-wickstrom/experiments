import { isDeepStrictEqual as equal } from "node:util";
import { readTraces, type Trace } from "../../cwm.ts";
import { freshInputs } from "./cases.ts";
import { manifest } from "./manifest.ts";
import { fit, rollout, type Mode, type Model } from "./model.ts";
import { example, project, type Sample } from "./project.ts";

function count() {
  return { stores: { exact: 0, wrong: 0, abstain: 0 }, rollouts: { exact: 0, total: 0 } };
}

function trial(model: Model, { p, states, end }: Sample) {
  const path = rollout(model, p, states[0]!);
  const complete = equal(path, [...states.slice(1), end]);
  const stores = states.slice(1).map((truth, i) => {
    const guess = model.next(p, states[i]!);
    return !guess ? "abstain" : equal(guess, truth) ? "exact" : "wrong";
  });
  return { complete, stores, firstExact: equal(path[0], states[1]) };
}

export function score(records: readonly Trace[]) {
  const expected = manifest();
  if (expected.length !== records.length) throw new Error("Incomplete manifest");
  const samples = expected.map(({ split, id, program }, i) => {
    const { frames, outcome, ...input } = records[i]!;
    if (!equal(input, program)) throw new Error("Wrong source, split or input at record " + i);
    return { split, id, sample: project({ ...input, frames, outcome }), raw: frames.length };
  });
  const rows = samples.filter((r) => r.split === "train").map((r) => example(r.sample));
  const fresh = samples.filter((r) => r.split === "fresh");
  function evaluate(mode: Mode) {
    const model = fit(rows, mode);
    const total = count(),
      negative = count();
    const families: Record<string, ReturnType<typeof count>> = {};
    const contrast = new Map<string, ReturnType<typeof trial>[]>();
    for (const { split, id, sample } of samples) {
      if (split === "train") continue;
      const result = trial(model, sample);
      const summary = split === "negative" ? negative : total;
      const family = (families[id] ??= count());
      for (const metric of [summary, family]) {
        for (const key of result.stores) metric.stores[key]++;
        metric.rollouts.total++;
        if (result.complete) metric.rollouts.exact++;
      }
      if (id.startsWith("contrast-")) {
        const k = JSON.stringify(sample.states[0]!.store);
        const group = contrast.get(k) ?? [];
        group.push(result);
        contrast.set(k, group);
      }
    }
    const both = [...contrast.values()].filter(
      (g) => g.length === 2 && g.every((r) => r.firstExact && r.complete),
    ).length;
    return {
      fresh: total,
      negative,
      families,
      contrastPairs: { exact: both, total: contrast.size },
    };
  }
  for (const input of freshInputs) {
    const pair = fresh.filter(
      (r) => r.id.startsWith("contrast-") && equal(r.sample.states[0]!.store, [...input]),
    );
    if (
      pair.length !== 2 ||
      !equal(pair[0]!.sample.end, pair[1]!.sample.end) ||
      equal(pair[0]!.sample.states[1], pair[1]!.sample.states[1])
    )
      throw new Error("Invalid contrast pair");
  }
  return {
    trainingRows: rows.length,
    survivors: fit(rows).survivors,
    rawAdjacentFresh: { total: fresh.reduce((n, s) => n + s.raw, 0), predicted: 0 },
    compose: evaluate("compose"),
    whole: evaluate("whole"),
    permuted: evaluate("permuted"),
  };
}

if (import.meta.main) {
  if (!process.argv[2]) throw new Error("Usage: bun score.ts EVIDENCE.jsonl");
  console.log(JSON.stringify(score(await Array.fromAsync(readTraces(process.argv[2]))), null, 2));
}
