import assert from "node:assert/strict";
import { expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { fitStructured } from "../../structured.ts";
import { loadSplit } from "./replay.ts";

const file = (name: string) =>
  fileURLToPath(new URL("./data/" + name + ".jsonl.gz", import.meta.url));
const base = (await loadSplit(file("varied"), "varied")).map((r) => r.trace);
const joins = (await loadSplit(file("targeted"), "targeted")).map((r) => r.trace);

test("a known invocation predicts detached complete raw paths through a join and backedge", async () => {
  const model = fitStructured([...base, ...joins]);
  const testRuns = await loadSplit(file("junction"), "junction");
  for (const {
    trace: { frames, outcome, ...call },
  } of testRuns) {
    const i = frames.findIndex((f) => f.stack[0]?.fn === call.fn);
    expect(model.predict(call.files, frames[i - 1]!)).toBeUndefined();
    const first = model.start(call);
    expect(first).toEqual(frames[i]!);
    expect([...model.rollout(call.files, first!, 128)]).toEqual([...frames.slice(i + 1), outcome]);
  }
});

test("an edited source or incomplete scope cannot reuse a prior prediction", () => {
  const model = fitStructured(base);
  const { frames: _frames, outcome: _outcome, ...call } = base[0]!;
  const first = model.start(call)!;
  const stable = structuredClone(first);
  expect(model.predict(call.files, first)).toBeDefined();
  expect(first).toEqual(stable);
  const masked = structuredClone(first);
  Object.values(masked.locals)[0]!.exact = false;
  expect(model.predict(call.files, masked)).toBeUndefined();
  expect(
    model.predict(call.files, { ...first, stack: [...first.stack, ...first.stack] }),
  ).toBeUndefined();
  const files = { ...call.files };
  files[call.entry] = "export function run(x:number,y:number){return Math.max(x,y);}";
  expect(model.predict(files, first)).toBeUndefined();
  expect(model.start({ ...call, files })).toBeUndefined();
  expect(model.start({ ...call, args: [] })).toBeUndefined();
  const sparse: number[] = [];
  sparse.length = call.args.length;
  expect(model.start({ ...call, args: sparse })).toBeUndefined();
  expect(model.start(call)).toEqual(stable);
});

test("scoring rejects a schema-valid split with missing intermediate pauses", async () => {
  const dir = await mkdtemp(join(tmpdir(), "cwm-replay-"));
  try {
    const held = (await loadSplit(file("held"), "held")).map(({ trace }) => ({
      ...trace,
      frames: [trace.frames[0], trace.frames.at(-1)],
    }));
    const path = join(dir, "held.jsonl");
    await writeFile(path, held.map((t) => JSON.stringify(t)).join("\n") + "\n");
    await assert.rejects(loadSplit(path, "held"), /Changed observations/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
test("an omitted first loop iteration invalidates training even in the adjacent-only ablation", () => {
  const run = structuredClone(base.find((t) => t.entry === "count-plain.ts" && t.args[0] === 5)!);
  run.frames.splice(1, 2);
  expect(() => fitStructured([run], { entryEvidence: false })).toThrow("entry store");
});
