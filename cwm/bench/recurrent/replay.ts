import { createHash } from "node:crypto";
import { join } from "node:path";
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { isDeepStrictEqual as equal } from "node:util";
import { readTraces, transitions, WorldModel, type Trace } from "../../cwm.ts";
import { fitStructured } from "../../structured.ts";
import { cache, collect, load } from "../collect.ts";
import { readout } from "../score.ts";
import { fitSites } from "../sites.ts";
import { repeated, targeted, junctionTest } from "./junctions.ts";
import { confirmation } from "./confirmation.ts";
import { cases, type Split } from "./cases.ts";

import { blind } from "./blind.ts";

const later = { blind, confirm: confirmation, repeated, targeted, junction: junctionTest };
type Dataset = Split | keyof typeof later;
function manifestFor(split: Dataset) {
  if (split === "fixed" || split === "varied" || split === "held") return cases(split);
  return later[split].map((program) => ({ program, family: program.entry, layout: split }));
}
const fingerprints: Record<Dataset, string> = {
  blind: "a085a9cf560ad70b519f9599f9d9b4255c8a0c11408395bf4f7023af586a9fe8",
  fixed: "96c458b2c043df456f0db53129d51beaedfed0b5c6164f5d6a2039b87d9972fb",
  varied: "978ef5696d8adeb08edfbff83588831d39e435a54e9b4f6087da12d5cc085797",
  held: "eb3245bb7150ff452424501863d2ad51c4d2a38d4d6a5f65ea15c3d019d6e2a8",
  confirm: "55a5797fea66cdec766a991ca376a49f0553e9a231c02d0139f9b19a3f88a450",
  repeated: "1f409b7e8466526e390744741f7ca3b510141045e3978b64c7f7d07532b976de",
  targeted: "b11701d34315e4fa4075142e90725855cad6a325569b897deeda1ff383cf4469",
  junction: "33cc905d487ee0312542ac27bd6b06482f7393846ef77535d7e8cd4b14d76ee5",
};
function isDataset(name: string): name is Dataset {
  return Object.hasOwn(fingerprints, name);
}
export async function loadSplit(file: string, split: Dataset) {
  const traces = await Array.fromAsync(readTraces(file)),
    manifest = manifestFor(split);
  assert.equal(traces.length, manifest.length);
  // Bind the entire normalized observation sequence before any label can enter a score.
  const hash = createHash("sha256");
  for (const t of traces) hash.update(JSON.stringify(t) + "\n");
  assert.equal(hash.digest("hex"), fingerprints[split], "Changed observations in " + split);
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
  nextLocals: hits(),
  nextEventAndStack: hits(),
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
    for (const g of groups) {
      g[i < start ? "module" : "stack" in truth ? "nonterminal" : "terminal"][outcome]++;
      if (i >= start && "stack" in truth) {
        const frame = guess && "stack" in guess ? guess : undefined;
        g.nextLocals[
          !guess ? "abstain" : frame && equal(frame.locals, truth.locals) ? "exact" : "wrong"
        ]++;
        g.nextEventAndStack[
          !guess
            ? "abstain"
            : frame && frame.kind === truth.kind && equal(frame.stack, truth.stack)
              ? "exact"
              : "wrong"
        ]++;
      }
    }
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
    persistence: (_files, f) => f,
    syntax: (files, f) => syntax({ files, entry: f.stack[0]!.file, fn: "run", args: [] }, f),
    learned: fitStructured(train, { joinContext: false, entryEvidence: false }).predict,
    mapped: fitStructured(train, { joinContext: false, entryEvidence: false, mappedReturns: true })
      .predict,
    offsets: fitStructured(train, { joinContext: false, entryEvidence: false, offsets: true })
      .predict,
    permuted: fitStructured(train, { joinContext: false, entryEvidence: false, permuted: true })
      .predict,
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
  const withEntry = fitStructured(train, { joinContext: false }),
    adjacent = fitStructured(train, { joinContext: false, entryEvidence: false });
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
async function fromDirectory(dir: string, split: Dataset) {
  const file = join(dir, split + ".jsonl");
  return (await loadSplit((await Bun.file(file).exists()) ? file : file + ".gz", split)).map(
    (r) => r.trace,
  );
}
function projections(traces: Trace[]) {
  const report = () => ({ frames: 0, maskedFrames: 0, snapshots: 0, maskedSnapshots: 0 });
  const module = report(),
    root = report();
  for (const t of traces)
    for (const f of t.frames) {
      const group = f.stack[0]?.fn === t.fn && f.stack[0].file === t.entry ? root : module;
      const slots = Object.values(f.locals);
      if (f.value) slots.push(f.value);
      const masked = slots.filter((s) => !s.exact).length;
      group.frames++;
      if (masked) group.maskedFrames++;
      group.snapshots += slots.length;
      group.maskedSnapshots += masked;
    }
  return {
    runs: traces.length,
    module,
    root,
    maskedOutcomes: traces.filter((t) => !t.outcome.result.exact).length,
  };
}
if (import.meta.main) {
  const [action, a, b, c] = process.argv.slice(2);
  if (action === "collect" && a && isDataset(a) && b && c) {
    assert.equal(Bun.version, "1.4.4");
    assert.equal(Bun.spawnSync(["node", "-v"]).stdout.toString().trim(), "v24.19.0");
    const inputs = manifestFor(a).map((r) => r.program),
      result = await collect(b, 4, inputs);
    assert.equal(result.failed, 0);
    const file = await cache(b);
    const rows = await Promise.all(inputs.map((p) => load(file(p), p)));
    await writeFile(c, rows.map((t) => JSON.stringify(t)).join("\n") + "\n", { flag: "wx" });
    console.log(JSON.stringify(result));
  } else if (action === "audit" && a) {
    const result: Record<string, ReturnType<typeof projections>> = {};
    for (const split of Object.keys(fingerprints).filter(isDataset))
      result[split] = projections(await fromDirectory(a, split));
    console.log(JSON.stringify(result, null, 2));
  } else if (action === "junctions" && a) {
    const rows = (s: Dataset) => fromDirectory(a, s);
    const base = await rows("varied");
    const scores = [];
    for (const extra of ["repeated", "targeted"] as const) {
      const train = [...base, ...(await rows(extra))];
      for (const joinContext of [false, true]) {
        const model = fitStructured(train, { joinContext });
        for (const split of ["junction", "confirm", "held"] as const) {
          const total = counts(),
            families: Record<string, ReturnType<typeof counts>> = {};
          for (const t of await rows(split))
            measure(model.predict, t, [total, (families[t.entry] ??= counts())]);
          scores.push({ extra, joinContext, split, total, families });
        }
      }
    }
    console.log(JSON.stringify(scores, null, 2));
  } else if (action === "blind" && a) {
    const model = fitStructured([
      ...(await fromDirectory(a, "varied")),
      ...(await fromDirectory(a, "targeted")),
    ]);
    const total = counts(),
      families: Record<string, ReturnType<typeof counts>> = {};
    const first = hits(),
      callPaths = ratio();
    for (const { frames, outcome, ...call } of await fromDirectory(a, "blind")) {
      const t = { ...call, frames, outcome };
      measure(model.predict, t, [total, (families[call.entry] ??= counts())]);
      const i = frames.findIndex(
        (f) => f.stack[0]?.fn === call.fn && f.stack[0].file === call.entry,
      );
      const guess = model.start(call);
      const hit = equal(guess, frames[i]);
      first[!guess ? "abstain" : hit ? "exact" : "wrong"]++;
      callPaths.total++;
      if (
        guess &&
        hit &&
        equal([...model.rollout(call.files, guess, 2048)], [...frames.slice(i + 1), outcome])
      )
        callPaths.exact++;
    }
    console.log(JSON.stringify({ first, callPaths, total, families }, null, 2));
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
      "Usage: collect SPLIT CACHE NEW.jsonl | score FIXED VARIED HELD | confirm VARIED CONFIRM | junctions DIR | blind DIR | audit DIR",
    );
}
