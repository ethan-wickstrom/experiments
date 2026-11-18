import { expect, test } from "bun:test";
import { trace } from "../../cwm.ts";
import { atomic, sourceOf, trainInputs } from "./cases.ts";
import { fit, rollout, type Atom } from "./model.ts";
import { plan } from "./plan.ts";
import { example, project } from "./project.ts";

const binary: Atom["expr"] = { op: "+", l: { slot: 0 }, r: { slot: 1 } };
const p = plan(sourceOf(atomic[0]!));
const row = (x: number, y: number, z: number): Atom => ({ expr: binary, x, y, z });
const start = (x: number, y: number) => ({ pc: 0, store: [x, y] });

test("operator meaning comes from labels, not from the parser or host", () => {
  const model = fit(trainInputs.map(([x, y]) => row(x, y, x - y)));
  expect(model.survivors["+"]).toEqual([[0, 1, -1, 0]]);
  expect(rollout(model, p, start(8, 1))).toEqual([{ pc: 1, store: [8, 1, 7] }, { returned: 7 }]);
  const nested = plan(sourceOf({ id: "dev", body: ["const s = x + (y + x);", "return s;"] }));
  expect(rollout(model, nested, start(8, 1)).at(-1)).toEqual({ returned: 15 });
});

test("empty evidence, inconsistent labels and out-of-span queries do not invent answers", () => {
  expect(fit([]).next(p, start(1, 1))).toBeUndefined();
  const ambiguous = fit([row(1, 1, 2)]);
  expect(ambiguous.survivors["+"]!.length).toBeGreaterThan(1);
  expect(ambiguous.next(p, start(1, 1))).toEqual({ pc: 1, store: [1, 1, 2] });
  expect(ambiguous.next(p, start(2, 3))).toBeUndefined();
  expect(fit([row(1, 1, 2), row(1, 1, 3)]).next(p, start(1, 1))).toBeUndefined();
  const model = fit(trainInputs.map(([x, y]) => row(x, y, x + y)));
  for (const n of [NaN, 0, -0, 0.5, Number.MAX_SAFE_INTEGER])
    expect(model.next(p, start(n, 2))).toBeUndefined();
  expect(() => plan(sourceOf({ id: "bad", body: ["return Math.max(x,y);"] }))).toThrow();
});

test("atomic supervision is the newly visible store, not the copied return", async () => {
  const t = await trace({
    entry: "train.ts",
    fn: "run",
    files: { "train.ts": sourceOf(atomic[0]!) },
    args: [8, 1],
  });
  const changed = { ...t, outcome: { ...t.outcome, result: { exact: true, value: 500 } } };
  expect(example(project(changed))).toEqual(row(8, 1, 9));
  const corrupt = structuredClone(t);
  const stop = corrupt.frames.find((f) => f.locals["m"]?.exact)!;
  stop.locals["m"] = { exact: false, value: "<unavailable>" };
  expect(() => project(corrupt)).toThrow("observed exact safe integer");
});
