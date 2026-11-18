import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { cache, collect, load } from "../collect.ts";
import { empty, readout, score } from "../score.ts";
import { fitSites } from "../sites.ts";
import { isDeepStrictEqual as equal } from "node:util";
import type { Trace } from "../../cwm.ts";
import { boundary, cases, example } from "./cases.ts";
import { digest, type Example } from "./types.ts";

const [cacheDir, dest] = process.argv.slice(2);
if (!cacheDir || !dest) throw new Error("Usage: bun prepare.ts CACHE NEW_DATASET");
const fixtures = [...cases()];
const sourceSets = ["train", "test"].map(
  (split) =>
    new Set(fixtures.filter((r) => r.split === split).map((r) => JSON.stringify(r.program.files))),
);
assert.equal(sourceSets[0]!.intersection(sourceSets[1]!).size, 0);
const collected = await collect(
  cacheDir,
  4,
  fixtures.map((c) => c.program),
);
assert.equal(collected.failed, 0, "Do not drop failed oracle runs");
const path = await cache(cacheDir);
const train: Trace[] = [],
  test: Trace[] = [];
for (const { split, program } of fixtures)
  (split === "train" ? train : test).push(await load(path(program), program));

function verifySplit(rows: Example[]) {
  const twins = Map.groupBy(rows, (e) => digest([{ ...e.input, signal: null }]));
  for (const pair of twins.values()) {
    assert.equal(pair.length, 2);
    const [a, b] = pair as [Example, Example];
    assert.notEqual(a.input.signal, null);
    assert.equal(a.input.signal, !b.input.signal);
    assert.deepEqual(a.after[0], b.after[0]);
    assert.notDeepEqual(a.after[1], b.after[1]);
  }
  const cells = Map.groupBy(rows, (e) => JSON.stringify([e.input.setup, e.input.write]));
  assert.equal(cells.size, 8);
  assert([...cells.values()].every((cell) => cell.length === 4));
  return cells;
}
const training = train.map(example),
  heldout = test.map(example);
const trainCells = verifySplit(training),
  testCells = verifySplit(heldout);
for (const cell of testCells.keys()) assert(!trainCells.has(cell));
for (const field of ["setup", "write"] as const) {
  assert.deepEqual(
    new Set(training.map((e) => e.input[field])),
    new Set(heldout.map((e) => e.input[field])),
  );
}
const inputs = heldout.map((e) => e.input);
await mkdir(dest);
const save = (name: string, data: unknown) =>
  Bun.write(join(dest, name + ".json"), JSON.stringify(data) + "\n");
await save("train", training);
await save("inputs", inputs);
await save("labels", { digest: digest(inputs), states: heldout.map((e) => e.after) });
const paired = test.map((t) => ({ t, ...boundary(t) }));
for (const group of Map.groupBy(paired, (row) =>
  digest([{ ...row.example.input, signal: null }]),
).values()) {
  assert.equal(group.length, 2);
  assert.deepEqual(group[0]!.pre, group[1]!.pre, "Raw pre-write frames must be indistinguishable");
}
const raw = Object.fromEntries(
  (["source", "filename-blind", "syntax", "syntax+operands", "readout"] as const).map((name) => {
    const predict = name === "readout" ? readout : fitSites(name, train),
      counts = empty(),
      atWrite = { arraysCorrect: 0, frameCorrect: 0, wrongArrays: 0, abstained: 0 };
    for (const { t, pre, post } of paired) {
      score(predict, t, counts);
      const next = predict({ files: t.files, fn: t.fn, entry: t.entry, args: [] }, pre);
      if (!next) atWrite.abstained++;
      else if ("locals" in next && ["a", "b"].every((k) => equal(next.locals[k], post.locals[k])))
        atWrite.arraysCorrect++;
      else atWrite.wrongArrays++;
      if (equal(next, post)) atWrite.frameCorrect++;
    }
    return [name, { ...counts, atWrite }];
  }),
);
await save("oracle", {
  train: train.length,
  test: test.length,
  raw,
  inputsSHA256: digest(inputs),
  testOutcomes: [...new Set(test.map((t) => JSON.stringify(t.outcome)))],
});
