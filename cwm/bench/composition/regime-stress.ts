import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { type Atom, fit } from "./model.ts";
import { sourceOf } from "./cases.ts";
import { example, project } from "./project.ts";

// The oracle adapter alone sees these spellings. Both committees receive only the opaque key.
const dictionary = { k17: "^", k42: "|" } as const;
type Key = keyof typeof dictionary;
type Pair = readonly [number, number];
const keys: Key[] = ["k17", "k42"];
const train: Pair[] = [
  [1, 4],
  [1, 8],
  [2, 4],
  [2, 8],
];
const pool: Pair[] = [
  [1, 16],
  [3, 5],
  [2, 16],
  [6, 3],
  [7, 9],
];
const test: Pair[] = [
  [3, 1],
  [6, 5],
  [9, 3],
  [12, 10],
  [15, 7],
  [5, 5],
  [33, 35],
];

type Query = { key: Key; pair: Pair };
const queries = (pairs: Pair[]) => keys.flatMap((key) => pairs.map((pair) => ({ key, pair })));
const expr = (op: Key): Atom["expr"] => ({ op, l: { slot: 0 }, r: { slot: 1 } });
type Candidate = { name: string; apply: (x: number, y: number) => number };
const extra: Candidate[] = [
  { name: "AND", apply: (x, y) => x & y },
  { name: "OR", apply: (x, y) => x | y },
  { name: "XOR", apply: (x, y) => x ^ y },
];

function committee(key: Key, rows: Atom[]) {
  const local = rows.filter((r) => r.expr.op === key);
  const frozen = fit(local);
  const coeff = frozen.survivors[key] ?? [];
  // These votes are only used in the enlarged committee; the original calls frozen.next.
  const candidates: Candidate[] = coeff.map((c) => ({
    name: "poly " + c.join(","),
    apply: (x, y) => c[0]! + c[1]! * x + c[2]! * y + c[3]! * x * y,
  }));
  candidates.push(...extra.filter((h) => local.every((r) => h.apply(r.x, r.y) === r.z)));
  const votes = ([x, y]: Pair) => candidates.map((h) => h.apply(x, y));
  return {
    survivors: candidates.map((h) => h.name),
    votes,
    predict(pair: Pair) {
      const p = {
        params: 2,
        names: ["x", "y", "m"],
        code: [{ expr: expr(key), line: 2, returns: false }],
      };
      const next = frozen.next(p, { pc: 0, store: [...pair] });
      const v = votes(pair);
      return {
        original: next && "store" in next ? next.store[2] : undefined,
        enlarged: v.length && v.every((n) => n === v[0]) ? v[0] : undefined,
      };
    },
  };
}
function choose(key: Key, c: ReturnType<typeof committee>, available: Pair[]) {
  const scores = available.map((pair) => {
    const v = c.votes(pair);
    return v.reduce((sum, n, i) => sum + v.slice(i + 1).filter((m) => m !== n).length, 0);
  });
  const i = scores.indexOf(Math.max(...scores));
  return { key, pair: available[i]!, scores, votes: c.votes(available[i]!) };
}

async function labels(dir: string, name: string, expected: Query[], collect: boolean) {
  const { readTraces, trace } = await import("../../cwm.ts");
  const path = join(dir, name + ".jsonl");
  const programs = expected.map(({ key, pair }) => {
    const entry = key + ".ts";
    return {
      files: {
        [entry]: sourceOf({ id: key, body: [`const m = x ${dictionary[key]} y;`, "return m;"] }),
      },
      entry,
      fn: "run",
      args: [...pair],
    };
  });
  if (collect) {
    const lines = [];
    for (const p of programs) lines.push(JSON.stringify(await trace(p)));
    await writeFile(path, lines.join("\n") + "\n", { flag: "wx" });
  }
  const traces = await Array.fromAsync(readTraces(path));
  assert.equal(traces.length, expected.length);
  return traces.map(({ frames, outcome, ...input }, i) => {
    assert.deepEqual(input, programs[i]);
    const { key, pair } = expected[i]!;
    const r = example(project({ ...input, frames, outcome }));
    assert.deepEqual([r.x, r.y], pair);
    return { ...r, expr: expr(key) };
  });
}

async function run(dir: string, collect: boolean) {
  if (collect) {
    assert.equal(Bun.version, "1.4.4");
    assert.equal(Bun.spawnSync(["node", "--version"]).stdout.toString().trim(), "v24.19.0");
    await mkdir(dir);
  }
  const initial = await labels(dir, "train", queries(train), collect);
  const before = keys.map((key) => committee(key, initial));
  const choices = keys.map((key, i) => choose(key, before[i]!, pool));
  const receipt = join(dir, "choices.json");
  if (collect) await writeFile(receipt, JSON.stringify(choices) + "\n", { flag: "wx" });
  assert.deepEqual(JSON.parse(await readFile(receipt, "utf8")), choices);
  const acquired = await labels(dir, "acquired", choices, collect);
  const after = keys.map((key) => committee(key, [...initial, ...acquired]));

  // Freeze both models' outputs before collecting or reading any evaluation label.
  const predictions = [before, after].map((stage) =>
    queries(test).map(({ key, pair }) => stage[keys.indexOf(key)]!.predict(pair)),
  );
  const held = await labels(dir, "held", queries(test), collect);
  return keys.map((key, i) => {
    const metrics = predictions.map((stage) => {
      const counts = () => ({ exact: 0, wrong: 0, abstain: 0 });
      const result = { original: counts(), enlarged: counts() };
      held.forEach((truth, j) => {
        if (truth.expr.op !== key) return;
        for (const kind of ["original", "enlarged"] as const) {
          const n = stage[j]![kind];
          result[kind][n === undefined ? "abstain" : n === truth.z ? "exact" : "wrong"]++;
        }
      });
      return result;
    });
    return {
      ...choices[i],
      observed: acquired[i]!.z,
      before: { survivors: before[i]!.survivors, ...metrics[0] },
      after: { survivors: after[i]!.survivors, ...metrics[1] },
    };
  });
}

if (import.meta.main) {
  const [mode, dir] = process.argv.slice(2);
  if (!dir || (mode !== "collect" && mode !== "score"))
    throw new Error("Usage: regime-stress.ts collect|score DIR");
  console.log(JSON.stringify(await run(dir, mode === "collect"), null, 2));
}
