import { expect, test } from "bun:test";
import { rejects } from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  WorldModel,
  applyEdit,
  episode,
  evaluate,
  mutations,
  readTraces,
  repair,
  trace,
  transitions,
  type Json,
  type Program,
} from "./cwm.ts";

function program(source: string, args: Json[] = []): Program {
  return { files: { "main.ts": source }, entry: "main.ts", fn: "run", args };
}

test("captures all six insertions from the CWM figure, before and after each splice", async () => {
  const source = `export function run(nums: number[]) {
  let a = 0;
  for (let i = 0, n = nums.length; i < n; i++) {
    nums.splice(i, 0, nums[a]);
    a += 1;
  }
  return nums;
}`;
  const input = [1, 3, -1, 1, -2, 6];
  const run = await trace(program(source, [input]));
  const invocation = `console.log(JSON.stringify(run(${JSON.stringify(input)})))`;
  const native = await Bun.$`${process.execPath} -e ${source + "\n" + invocation}`.quiet();
  const expected = native.json();
  expect(expected).toEqual([1, 1, 1, 1, 1, 1, 1, 3, -1, 1, -2, 6]);
  expect(run.outcome).toEqual({ kind: "returned", result: { value: expected, exact: true } });
  for (const [line, growth] of [
    [4, 0],
    [5, 1],
  ] as const) {
    const sizes = run.frames
      .filter((f) => f.stack[0]?.line === line)
      .map((f) => (f.locals.nums!.value as number[]).length);
    expect([...new Set(sizes)]).toEqual(input.map((_, i) => input.length + i + growth));
  }
  expect(run.args).toEqual([input]);
});

test("links cyclic ESM, live bindings and nested re-exports; maps recursive frames to TypeScript", async () => {
  const spec = program('export { count as run } from "./lib/count.ts";', ["strawberry"]);
  spec.files["lib/count.ts"] = `import { match } from "./match.js";
export enum Letter { R = "r" }
export function count(s: string): number {
  return s.length ? match(s[0]) + count(s.slice(1)) : 0;
}`;
  spec.files["lib/match.ts"] = `import { Letter } from "./count.ts";
export const match = (s: string) => +(s === Letter.R);`;
  const { frames, outcome } = await trace(spec);
  expect(outcome.result).toEqual({ value: 3, exact: true });
  expect(frames.some((f) => f.stack[0]?.file === "lib/match.ts" && f.stack[1]?.line === 4)).toBe(
    true,
  );
  expect(frames.some((f) => f.stack.filter((s) => s.fn === "count").length >= 10)).toBe(true);
});

test("caught exceptions, await and finally keep their actual order and outcome", async () => {
  const spec = program(
    `export async function run({n}: {n:number}) {
  const original = n;
  try { await Promise.resolve(); throw "caught"; }
  catch (n) { return [n, original]; }
  finally { if (original < 0) throw "overridden"; }
}`,
    [{ n: 2 }],
  );
  const [good, bad] = await Promise.all([trace(spec), trace({ ...spec, args: [{ n: -2 }] })]);
  expect(good.frames.some((f) => f.kind === "exception" && f.value?.value === "caught")).toBe(true);
  expect(
    good.frames.some((f) => f.locals.n?.value === "caught" && f.locals.original?.value === 2),
  ).toBe(true);
  expect(good.outcome.result.value).toEqual(["caught", 2]);
  expect(bad.outcome).toEqual({ kind: "threw", result: { value: "overridden", exact: true } });
});

test("snapshots never invoke object accessors and incomplete values cannot pass a repair", async () => {
  const spec = program(`export function run() {
  let calls = 0;
  const obj = { get field() { calls++; return 1; } };
  return [obj, calls];
}`);
  const [step] = (await episode(spec, ["run"], [{ field: "<unavailable>" }, 0])).steps;
  expect(step && "verdict" in step && step.verdict).toBe("unknown");
  expect(step && "execution" in step && step.execution.outcome.result.value).toEqual([
    { field: "<unavailable>" },
    0,
  ]);
});

test("replays a Unicode-offset mutation, does not count a helper return as a pass", async () => {
  const spec = program(
    'import { sum } from "./lib.ts"; export function run(){ return [sum(6, 2)]; }',
  );
  spec.files["lib.ts"] = "/* 🪴 + */ export const sum = (lhs:number, rhs:number) => (lhs + rhs);";
  const edit = (await mutations(spec)).find((e) => e.file === "lib.ts")!;
  expect(edit.before).toBe("lhs + rhs");
  const mutant = applyEdit(spec, edit);
  expect(() => applyEdit(mutant, edit)).toThrow("does not match");
  const history = await repair(spec, edit, [8]);
  expect(history.steps.map((s) => ("verdict" in s ? s.verdict : "edit"))).toEqual([
    "fail",
    "edit",
    "pass",
  ]);
  expect(history.initial).toEqual(mutant);
  const undo = history.steps[1]!.action;
  if (undo === "run") throw new Error("Missing repair");
  expect(applyEdit(mutant, undo)).toEqual(spec);
  const failed = await episode(mutant, [edit, "run"], [8]);
  expect(failed.steps[0]).toHaveProperty("error");
  expect(failed.steps[1]).toHaveProperty("verdict", "fail");
});

test("rejects non-repository imports, bad entrypoints, malformed code and exhausted budgets", async () => {
  await rejects(trace(program('export { run } from "node:path";')), /Not a repository import/);
  await rejects(trace(program("export const run = () => import('./later.ts');")), /static/);
  await rejects(trace(program("export function other(){}")), /Missing export/);
  await rejects(trace(program("export const run = 1;")), /not callable/);
  await rejects(trace(program("export const run = (")), /main.ts/);
  await rejects(
    trace(program("export function run(){return 3;}"), { maxFrames: 1 }),
    /frame limit/,
  );
  await rejects(
    trace(program("export function run(){return new Promise(() => {});}"), { timeoutMs: 400 }),
    /deadline/,
  );
  await rejects(trace(program("export function run(){}", [Infinity])), /JSON/);
});

test("learns an unseen affine return and rolls forward without executing the held-out program", async () => {
  const spec = program("export function run(x:number, y:number) { return 2*x - 3*y + 7; }");
  const train = await Promise.all(
    [
      [0, 1],
      [2, 1],
      [1, 3],
      [4, 0],
      [-1, 2],
    ].map((args) => trace({ ...spec, args })),
  );
  const model = new WorldModel().fit(train);
  const testRun = await trace({ ...spec, args: [8, -2] });
  const start = testRun.frames.find((f) => f.stack[0]?.fn === "run")!;
  const predicted = [...model.rollout(spec.files, start, 8)];
  expect(predicted).toEqual([
    ...testRun.frames.slice(testRun.frames.indexOf(start) + 1),
    testRun.outcome,
  ]);
  expect(testRun.outcome.result.value).toBe(29);
  expect(train.every((r) => r.outcome.result.value !== 29)).toBe(true);
  const score = evaluate(model, [testRun]);
  expect(score.total).toBe([...transitions(testRun)].length);
  expect(score.correct).toBeGreaterThanOrEqual(predicted.length);
  expect(model.predict({}, start)).toBeUndefined();
});

test("JSONL round-trips real traces and rejects corrupt input at its physical line", async () => {
  const run = await trace(program('export const run = () => "<|action_sep|>\\n";'));
  const dir = await mkdtemp(join(tmpdir(), "cwm-"));
  try {
    const path = join(dir, "trace.jsonl");
    await Bun.write(path, JSON.stringify(run) + "\r\n\n");
    expect(await Array.fromAsync(readTraces(path))).toEqual([run]);
    await Bun.write(path, JSON.stringify(run) + "\n\n{}\n");
    await rejects(Array.fromAsync(readTraces(path)), /line 3/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
