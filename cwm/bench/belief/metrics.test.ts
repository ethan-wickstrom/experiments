import { expect, test } from "bun:test";
import * as S from "effect/Schema";
import { measure } from "./metrics.ts";
import { Input, strict } from "./types.ts";
import { cover } from "./curriculum.ts";

const x = { setup: "s", write: "w", index: 1, signal: null, before: [[2], [2]] };

test("identical inputs with two successors have a proper score even when no decision is justified", () => {
  const states = [
    [[3], [2]],
    [[3], [3]],
  ];
  const rows = states.map((after) => ({ input: x, after }));
  const balanced = measure(rows, () => states.map((state) => ({ state, prob: 0.5 })));
  expect(balanced).toEqual({
    right: 0,
    wrong: 0,
    abstain: 2,
    perfectCells: 0,
    brier: 0.5,
    nll: Math.log(2),
  });
  expect(measure(rows, () => [{ state: states[0]!, prob: 1 }])).toMatchObject({
    right: 1,
    wrong: 1,
    brier: 1,
    nll: "Infinity",
  });
  expect(() => S.decodeUnknownSync(Input, strict)({ ...x, after: states[0] })).toThrow();
  expect(() => measure(rows, () => states.map((state) => ({ state, prob: 1 })))).toThrow();
});

test("coverage includes unmatched contexts, not only the matched pairs", () => {
  const rows = [
    ["a", "x"],
    ["b", "x"],
    ["c", "y"],
    ["c", "z"],
  ].map(([setup, write]) => ({ ...x, setup: setup!, write: write! }));
  expect(cover(rows)).toEqual([0, 1, 2, 3]);
});
