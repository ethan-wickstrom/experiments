import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { isDeepStrictEqual as equal } from "node:util";
import { readTraces, transitions, WorldModel, type Trace } from "../../cwm.ts";
import { fitStructured } from "../../structured.ts";
import { cache, collect, load } from "../collect.ts";
import { readout } from "../score.ts";
import { fitSites } from "../sites.ts";
import { confirmation } from "./confirmation.ts";
import { cases, type Split } from "./cases.ts";

function manifestFor(split: Split | "confirm") {
  return split === "confirm"
    ? confirmation.map((program) => ({ program, family: program.entry, layout: "confirmation" }))
    : cases(split);
}
async function loadSplit(file: string, split: Split | "confirm") {
  const traces = await Array.fromAsync(readTraces(file)),
    manifest = manifestFor(split);
  assert.equal(traces.length, manifest.length);
  return traces.map((trace, i) => {
    const { frames: _frames, outcome: _outcome, ...p } = trace;
    const { program, family, layout } = manifest[i]!;
    assert.deepEqual(p, program);
    return { trace, family, layout };
  });
}
const hits = () => ({ exact: 0, wrong: 0, abstain: 0 });
const ratio = () => ({ exact: 0, total: 0 });
const horizons = [1, 2, 4, 8, 16, 32];
const counts = () => ({
  module: hits(),
  nonterminal: hits(),
  terminal: hits(),
  paths: ratio(),
  survival: Object.fromEntries(horizons.map((k) => [k, ratio()])),
});
type Predict = WorldModel["predict"];
export function measure(predict: Predict, t: Trace, groups: ReturnType<typeof counts>[]) {
  const start = t.frames.findIndex((f) => f.stack[0]?.fn === t.fn && f.stack[0].file === t.entry);
  assert(start >= 0, "Missing function entry");
  for (const [i, [f, truth]] of [...transitions(t)].entries()) {
    const guess = predict(t.files, f),
      outcome = !guess ? "abstain" : equal(truth, guess) ? "exact" : "wrong";
    for (const g of groups)
      g[i < start ? "module" : "stack" in truth ? "nonterminal" : "terminal"][outcome]++;
  }
  let current = t.frames[start]!,
    prefix = 0;
  for (let i = start; i < t.frames.length; i++) {
    const pred = predict(t.files, current);
    if (!pred || !equal(pred, t.frames[i + 1] ?? t.outcome)) break;
    prefix++;
    if (!("stack" in pred)) break;
    current = pred;
  }
  const length = t.frames.length - start;
  for (const g of groups) {
    g.paths.total++;
    if (prefix === length) g.paths.exact++;
    for (const k of horizons.filter((n) => n <= length)) {
      g.survival[k]!.total++;
      if (prefix >= k) g.survival[k]!.exact++;
    }
  }
  return { first: prefix > 0, complete: prefix === length };
}
function compare(train: Trace[], held: Awaited<ReturnType<typeof loadSplit>>) {
  const base = new WorldModel().fit(train);
  const syntax = fitSites("syntax+operands", train);
  const models: Record<string, Predict> = {
    syntax: (files, f) => syntax({ files, entry: f.stack[0]!.file, fn: "run", args: [] }, f),
    learned: fitStructured(train, { entryEvidence: false }).predict,
    mapped: fitStructured(train, { entryEvidence: false, mappedReturns: true }).predict,
    offsets: fitStructured(train, { entryEvidence: false, offsets: true }).predict,
    permuted: fitStructured(train, { entryEvidence: false, permuted: true }).predict,
    retrieval: (files, f) => base.predict(files, f),
    readout: (files, f) => readout({ files, entry: f.stack[0]!.file, fn: "run", args: [] }, f),
  };
  return Object.fromEntries(
    Object.entries(models).map(([name, predict]) => {
      const total = counts(),
        families: Record<string, ReturnType<typeof counts>> = {},
        layouts: typeof families = {};
      const twins = new Map<string, ReturnType<typeof measure>[]>();
      for (const { trace, layout, family } of held) {
        const row = measure(predict, trace, [
          total,
          (families[family] ??= counts()),
          (layouts[layout] ??= counts()),
        ]);
        if (family === "plusTwin" || family === "minusTwin") {
          const k = JSON.stringify([layout, trace.args]),
            rs = twins.get(k) ?? [];
          rs.push(row);
          twins.set(k, rs);
        }
      }
      const joint = { first: 0, complete: 0, total: twins.size };
      for (const pair of twins.values()) {
        assert.equal(pair.length, 2);
        if (pair.every((r) => r.first)) joint.first++;
        if (pair.every((r) => r.complete)) joint.complete++;
      }
      return [name, { total, families, layouts, joint }];
    }),
  );
}
function invocationCeiling(rows: Trace[]) {
  const groups = new Map<string, Map<string, number>>();
  for (const t of rows) {
    const i = t.frames.findIndex((f) => f.stack[0]?.fn === t.fn && f.stack[0].file === t.entry);
    assert(i > 0);
    const prefix = JSON.stringify([t.files, t.entry, t.fn, t.frames.slice(0, i)]);
    const target = JSON.stringify(t.frames[i]),
      group = groups.get(prefix) ?? new Map<string, number>();
    group.set(target, 1 + (group.get(target) ?? 0));
    groups.set(prefix, group);
  }
  return {
    groups: groups.size,
    maxExact: [...groups.values()].reduce((s, g) => s + Math.max(...g.values()), 0),
    total: rows.length,
  };
}
function fromCall(train: Trace[], held: Trace[]) {
  const withEntry = fitStructured(train),
    adjacent = fitStructured(train, { entryEvidence: false });
  const totals = () => ({
    first: hits(),
    callPaths: ratio(),
    observedPaths: ratio(),
    adjacentPaths: ratio(),
  });
  const total = totals(),
    families: Record<string, ReturnType<typeof totals>> = {};
  for (const { frames, outcome, ...call } of held) {
    const index = frames.findIndex(
      (f) => f.stack[0]?.fn === call.fn && f.stack[0].file === call.entry,
    );
    assert(index >= 0);
    const start = withEntry.start(call),
      truth = [...frames.slice(index + 1), outcome];
    const first = !start ? "abstain" : equal(start, frames[index]) ? "exact" : "wrong";
    function complete(model: typeof adjacent, f: typeof start) {
      return !!f && equal([...model.rollout(call.files, f, 2048)], truth);
    }
    const observed = frames[index]!;
    const callPath = first === "exact" && complete(withEntry, start),
      current = complete(withEntry, observed),
      old = complete(adjacent, observed);
    for (const g of [total, (families[call.entry] ??= totals())]) {
      g.first[first]++;
      for (const [name, success] of [
        ["callPaths", callPath],
        ["observedPaths", current],
        ["adjacentPaths", old],
      ] as const) {
        g[name].total++;
        if (success) g[name].exact++;
      }
    }
  }
  return { total, families };
}
if (import.meta.main) {
  const [action, a, b, c] = process.argv.slice(2);
  if (
    action === "collect" &&
    (a === "fixed" || a === "varied" || a === "held" || a === "confirm") &&
    b &&
    c
  ) {
    assert.equal(Bun.version, "1.4.4");
    assert.equal(Bun.spawnSync(["node", "-v"]).stdout.toString().trim(), "v24.19.0");
    const inputs = manifestFor(a).map((r) => r.program),
      result = await collect(b, 4, inputs);
    assert.equal(result.failed, 0);
    const file = await cache(b);
    const rows = await Promise.all(inputs.map((p) => load(file(p), p)));
    await writeFile(c, rows.map((t) => JSON.stringify(t)).join("\n") + "\n", { flag: "wx" });
    console.log(JSON.stringify(result));
  } else if (action === "confirm" && a && b) {
    const train = (await loadSplit(a, "varied")).map((r) => r.trace),
      held = (await loadSplit(b, "confirm")).map((r) => r.trace);
    console.log(JSON.stringify(fromCall(train, held), null, 2));
  } else if (action === "score" && a && b && c) {
    const held = await loadSplit(c, "held");
    console.log(
      JSON.stringify(
        {
          invocationCeiling: invocationCeiling(held.map((r) => r.trace)),
          curricula: Object.fromEntries(
            await Promise.all(
              (
                [
                  ["fixed", a],
                  ["varied", b],
                ] as const
              ).map(async ([split, file]) => [
                split,
                compare(
                  (await loadSplit(file, split)).map((r) => r.trace),
                  held,
                ),
              ]),
            ),
          ),
        },
        null,
        2,
      ),
    );
  } else
    throw Error(
      "Usage: collect fixed|varied|held|confirm CACHE NEW.jsonl | score FIXED VARIED HELD | confirm VARIED CONFIRM",
    );
}
