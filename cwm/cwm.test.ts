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
  type Frame,
  type Json,
  type Program,
  type Trace,
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
  const expected = [1, 1, 1, 1, 1, 1, 1, 3, -1, 1, -2, 6];
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

test("inspecting Error locals leaves getter counts equal to plain Node", async () => {
  for (const key of ["stack", "name", "message"]) {
    const source = `export function run(){
      let calls=0;
      const error=new Error("x");
      Object.defineProperty(error,${JSON.stringify(key)},{get(){calls++;return "observed";}});
      const observed={error};
      return calls;
    }`;
    const plain = Bun.spawnSync([
      "node",
      "--input-type=module",
      "-e",
      source + ";console.log(run())",
    ]);
    expect(plain.success).toBe(true);
    const calls = JSON.parse(plain.stdout.toString());
    expect(calls).toBe(0);
    const traced = await trace(program(source));
    expect(traced.outcome).toEqual({ kind: "returned", result: { value: calls, exact: true } });
    expect(
      traced.frames.some((f) => f.locals.error?.value === "<error>" && !f.locals.error.exact),
    ).toBe(true);
    expect(
      traced.frames
        .filter((f) => f.locals.calls?.exact)
        .every((f) => f.locals.calls?.value === calls),
    ).toBe(true);
  }
});

test("a live namespace with an uninitialized export is opaque", async () => {
  const t = await trace(
    program(
      'import * as self from "./main.ts"; function init(ns){return 1;} export const later=init(self); export function run(){return later;}',
    ),
  );
  expect(t.outcome).toEqual({ kind: "returned", result: { value: 1, exact: true } });
  expect(t.frames.find((f) => f.stack[0]?.fn === "init")?.locals.ns).toEqual({
    value: "<module namespace>",
    exact: false,
  });
});

test("an Error exposed by the pause itself cannot become an accepted episode", async () => {
  const spec = program('export function run(){throw new Error("unsupported")}');
  const [step] = (await episode(spec, ["run"], null)).steps;
  expect(step && "error" in step && step.error).toContain("Cannot faithfully observe");
  expect(step).not.toHaveProperty("execution");
});

test("replays a Unicode-offset mutation, does not count a helper return as a pass", async () => {
  const spec = program(
    'import { sum } from "./lib.ts"; const target = () => [8]; export function run(){ return [sum(target()[0]-2, 2)]; }',
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
  const expected = [8];
  const failed = await episode(mutant, [edit, "run"], expected);
  mutant.files["lib.ts"] = "";
  edit.after = "";
  expected.pop();
  expect(failed.steps[0]).toHaveProperty("error");
  expect(failed.steps[0]!.action).not.toEqual(edit);
  expect(failed.initial).not.toEqual(mutant);
  expect(failed.expected).toEqual([8]);
  expect(failed.steps[1]).toHaveProperty("verdict", "fail");
});

test("rejects non-repository imports, bad entrypoints and invalid programs", async () => {
  await rejects(trace(program('export { run } from "node:path";')), /Not a repository import/);
  await rejects(trace(program("export const run = () => import('./later.ts');")), /static/);
  await rejects(trace(program("export function other(){}")), /Missing export/);
  await rejects(trace(program("export const run = 1;")), /not callable/);
  await rejects(trace(program("export const run = (")), /main.ts/);
  await rejects(trace(program("export function run(){}", [Infinity])), /JSON/);
  const extra = { ...program(""), description: "not a trace field" };
  await rejects(trace(extra), /excess property/);
  await rejects(trace(program("", [-0])), /losslessly/);
});

test("frame exhaustion interrupts a busy guest; the wall deadline also covers idle promises", async () => {
  const source = "export function run(stall:boolean){ return stall ? new Promise(()=>{}) : 3; }";
  const limits = { timeoutMs: 3000 };
  const [complete] = await Promise.all([
    trace(program(source, [false]), limits),
    rejects(trace(program(source, [true]), limits), /deadline/),
    rejects(
      trace(program("export function run(){let i=0; while(true){i++;}}"), {
        ...limits,
        maxFrames: 1,
      }),
      /frame limit/,
    ),
  ]);
  expect(complete.outcome.result).toEqual({ value: 3, exact: true });
});

test("coupled scalar inputs identify a law only on their observed subspace", () => {
  const spec = program("return x + y");
  const site = { file: "main.ts", line: 1, column: 1, fn: "run" };
  const observation = (x: number, y: number): Frame => ({
    kind: "step",
    stack: [site],
    locals: { x: { value: x, exact: true }, y: { value: y, exact: true } },
  });
  for (const scale of [0.5, 1e-16]) {
    const train: Trace[] = [0, 2, 4, 6].map((x) => ({
      ...spec,
      frames: [observation(x, x)],
      outcome: { kind: "returned", result: { value: x * scale, exact: true } },
    }));
    const model = new WorldModel().fit(train);
    const query = observation(1, 1);
    query.stack = [{ fn: site.fn, column: site.column, line: site.line, file: site.file }];
    expect(model.predict(spec.files, query)).toEqual({
      kind: "returned",
      result: { value: scale, exact: true },
    });
    expect(model.predict(spec.files, observation(1, 3))).toBeUndefined();
  }
  const state = observation(1, 1);
  const conflicts: Trace[] = [true, false].map((value) => ({
    ...spec,
    frames: [state],
    outcome: { kind: "returned", result: { value, exact: true } },
  }));
  for (const order of [conflicts, conflicts.toReversed()]) {
    expect(new WorldModel().fit(order).predict(spec.files, state)).toBeUndefined();
  }
});

test("learns an unseen affine return and rolls forward without executing the held-out program", async () => {
  const spec = program(
    "function affine(x:number,y:number){return 2*x-3*y+7;}\nexport function run(x:number,y:number){return affine(x,y);}",
  );
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

test("trace JSONL preserves arbitrary keys and rejects invalid nested records", async () => {
  const site = { file: "main.ts", line: 1, column: 1, fn: "run" };
  const result = { exact: true, value: { ["__proto__"]: [null, true, 1, "text"] } };
  const frame: Frame = { kind: "step", stack: [site], locals: { ["__proto__"]: result } };
  const record: Trace = {
    ...program("", [result.value]),
    frames: [frame],
    outcome: { kind: "returned", result },
  };
  const dir = await mkdtemp(join(tmpdir(), "cwm-schema-"));
  try {
    const path = join(dir, "trace.jsonl");
    await Bun.write(path, JSON.stringify(record));
    const [decoded] = await Array.fromAsync(readTraces(path));
    expect(decoded).toStrictEqual(record);
    for (const invalid of [
      { ...record, extra: true },
      { ...record, frames: [{ ...frame, extra: true }] },
      { ...record, frames: [{ ...frame, stack: [] }] },
      { ...record, frames: [{ ...frame, stack: [{ ...site, line: 0 }] }] },
      { ...record, frames: [{ ...frame, stack: [{ ...site, column: 1.5 }] }] },
      {
        ...record,
        frames: [{ ...frame, stack: [{ ...site, line: Number.MAX_SAFE_INTEGER + 1 }] }],
      },
      { ...record, frames: [{ ...frame, kind: "return" }] },
      { ...record, frames: [{ ...frame, kind: "exception" }] },
      { ...record, frames: [{ ...frame, value: result }] },
      { ...record, frames: [{ ...frame, locals: [] }] },
      { ...record, outcome: { kind: "returned", result: { ...result, extra: true } } },
    ]) {
      await Bun.write(path, "\n" + JSON.stringify(invalid));
      await rejects(Array.fromAsync(readTraces(path)), /line 2/);
    }
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
