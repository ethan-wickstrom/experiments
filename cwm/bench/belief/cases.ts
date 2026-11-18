import assert from "node:assert/strict";
import { parseSync } from "oxc-parser";
import type { Frame, Program, Trace } from "../../cwm.ts";
import type { Example } from "./types.ts";

// Preselected before collecting labels. Each row and column occurs twice in each split.
const setups = [
  "flag ? a : [...a]",
  "!flag ? a.slice() : a",
  "flag ? [...a] : a",
  "!flag ? a : a.slice()",
];
const writes = ["a[index]++", "a[1 - index] -= 2", "a[1 - index] += 3", "a[index]--"];

function scaffold(setup: string, write: string) {
  return `export function run(flag: boolean, index: number) {
  const a = [2, 5];
  const b = ${setup};
  flag = false;
  ${write};
  return 7;
}`;
}

export function cases(): { split: "train" | "test"; program: Program }[] {
  const runs: ReturnType<typeof cases> = [];
  const entry = "probe.ts",
    fn = "run";
  for (const [row, setup] of setups.entries()) {
    for (const [column, write] of writes.entries()) {
      const source = scaffold(setup, write);
      for (const flag of [false, true]) {
        for (const index of [0, 1]) {
          runs.push({
            split: (row + column) % 2 === 0 ? "train" : "test",
            program: { entry, fn, files: { [entry]: source }, args: [flag, index] },
          });
        }
      }
    }
  }
  return runs;
}

const compact = (s: string) => s.replace(/\s+/gu, "");
function layout(t: Pick<Program, "entry" | "files" | "fn">) {
  const source = t.files[t.entry];
  assert(source && Object.keys(t.files).length === 1 && t.fn === "run", "Expected one entry");
  const syntax = parseSync(t.entry, source);
  const exp = syntax.program.body[0];
  const fn = exp?.type === "ExportNamedDeclaration" && exp.declaration;
  assert(!syntax.errors.length && fn && fn.type === "FunctionDeclaration" && fn.body);
  const spans = fn.body.body;
  const decl = spans[1],
    stmt = spans[3];
  const init = decl?.type === "VariableDeclaration" && decl.declarations[0]?.init;
  assert(init && stmt?.type === "ExpressionStatement", "Missing setup/write");
  // These keys are whitespace-normalized source expressions, never generator indices.
  const slice = (n: { start: number; end: number }) => compact(source.slice(n.start, n.end));
  const setup = slice(init),
    write = slice(stmt.expression);
  assert(
    setups.some((s) => compact(s) === setup) &&
      writes.some((w) => compact(w) === write) &&
      compact(source) === compact(scaffold(setup, write)) &&
      spans.length === 5 &&
      spans[0]?.type === "VariableDeclaration" &&
      spans[2]?.type === "ExpressionStatement" &&
      spans[4]?.type === "ReturnStatement",
    "Unsupported fixture",
  );
  const starts = [
    0,
    ...Array.from(source.matchAll(/\r\n|[\r\n\u2028\u2029]/gu), (m) => m.index + m[0].length),
  ];
  return {
    setup,
    write,
    phase(this: void, frame: Frame) {
      const site = frame.stack[0]!;
      assert(
        frame.stack.length === 1 && site.file === t.entry && site.fn === t.fn,
        "Unexpected guest stack",
      );
      const start = starts[site.line - 1];
      assert(start !== undefined && site.column >= 1, "Invalid pause location");
      const offset = start + site.column - 1;
      assert(offset < (starts[site.line] ?? source.length), "Invalid pause column");
      const phase = spans.findIndex((s, i) => {
        const n = i === 3 ? stmt.expression : s;
        return offset >= n.start && offset < n.end;
      });
      assert(phase >= 0, "Pause is outside the observed statements");
      return phase;
    },
  };
}

function value(f: Frame, name: string) {
  const v = f.locals[name];
  assert(v?.exact, `Missing or inexact ${name}`);
  return v.value;
}
function arrays(f: Frame) {
  return ["a", "b"].map((name) => {
    const v = value(f, name);
    assert(
      Array.isArray(v) &&
        v.length === 2 &&
        v.every((n): n is number => typeof n === "number" && Number.isSafeInteger(n)),
      "Expected two integer slots",
    );
    return [...v];
  });
}

/** One adjacent V8 pause pair; the successor is a label, not an input. */
export function boundary(t: Trace) {
  const { setup, write, phase } = layout(t);
  const start = t.frames.findIndex((f) => f.stack[0]?.fn === t.fn);
  assert(start >= 0, "Missing entry pause");
  const frames = t.frames.slice(start);
  const phases = frames.map(phase);
  assert.equal(phases[0], 0, "Missing initial observation");
  assert.equal(phases.at(-1), 4, "Missing successor");
  const signal = value(frames[0]!, "flag");
  assert(typeof signal === "boolean", "Missing prefix flag");
  for (const [i, p] of phases.entries()) {
    const prev = phases[i - 1] ?? 0;
    assert(p === prev || p === prev + 1, "Missing, repeated or out-of-order statement");
    const f = frames[i]!;
    assert.deepEqual(Object.keys(f.locals).sort(), ["a", "b", "flag", "index"]);
    assert.equal(value(f, "flag"), p < 3 ? signal : false, "Unexpected flag change");
    assert.equal(f.kind, i === phases.length - 1 ? "return" : "step", "Unexpected pause kind");
  }
  // Attribute the store to the sole write→return boundary, not the first pair
  // with different values. All earlier/later overlapping pairs must agree.
  const next = phases.indexOf(4);
  const pre = frames[next - 1]!;
  const index = value(pre, "index");
  assert(index === 0 || index === 1, "Unexpected write input");
  const before = arrays(pre),
    after = arrays(frames[next]!);
  assert.deepEqual(before[0], before[1], "Twins must have equal pre-write arrays");
  for (const [i, p] of phases.entries()) {
    const f = frames[i]!;
    assert.equal(value(f, "index"), index);
    if (p === 1) assert.deepEqual(value(f, "a"), before[0], "Array changed during setup");
    if (p >= 2) assert.deepEqual(arrays(f), i < next ? before : after, "Unexpected array change");
  }
  const changed = after[0]!.filter((v, k) => v !== before[0]![k]);
  assert.equal(changed.length, 1, "Expected one nonzero write on a");
  if (!after[1]!.every((v, k) => v === before[1]![k]))
    assert.deepEqual(after[1], after[0], "Unexpected change on b");
  assert.deepEqual(t.outcome, { kind: "returned", result: { exact: true, value: 7 } });
  assert.deepEqual(frames.at(-1)!.value, t.outcome.result);
  return {
    example: { input: { setup, write, signal, index, before }, after },
    pre,
    post: frames[next]!,
  };
}

export const example = (t: Trace): Example => boundary(t).example;
