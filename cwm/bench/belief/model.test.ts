import { expect, test } from "bun:test";
import { fit } from "./model.ts";
import type { Example, Input } from "./types.ts";

const choose = "const b = flag ? a : a.slice()";
const invert = "const b = flag ? a.slice() : a";
const inc = "a[i]++";
const dec = "a[1-i] -= 3";
const nop = "a[i] += 0";

function input(
  setup: string,
  write: string,
  signal: boolean | null,
  first: number[],
  index = 0,
): Input {
  return { setup, write, signal, index, before: [first, [...first]] };
}

const evidence: Example[] = [
  {
    input: input(choose, inc, true, [3, 4]),
    after: [
      [4, 4],
      [4, 4],
    ],
  },
  {
    input: input(choose, inc, false, [3, 4]),
    after: [
      [4, 4],
      [3, 4],
    ],
  },
  {
    input: input(invert, dec, true, [-1, 2]),
    after: [
      [-1, -1],
      [-1, 2],
    ],
  },
  {
    input: input(invert, dec, false, [-1, 2]),
    after: [
      [-1, -1],
      [-1, -1],
    ],
  },
  {
    input: input(invert, dec, false, [-1, 2], 1),
    after: [
      [-4, 2],
      [-4, 2],
    ],
  },
];

test("recombines a learned write with a different setup and new cell values", () => {
  const predict = fit(evidence);
  for (const [index, first] of [
    [0, [7, -7]],
    [1, [4, -4]],
  ] as const) {
    const observed = input(choose, dec, true, [7, -4], index);
    expect(predict(observed)).toEqual([{ state: [first, first], prob: 1 }]);
    expect(predict({ ...observed, signal: false })).toEqual([{ state: [first, [7, -4]], prob: 1 }]);
    expect(observed.before).toEqual([
      [7, -4],
      [7, -4],
    ]);
  }
});

test("marginalizes a masked signal using training frequencies", () => {
  const repeated = {
    input: input(choose, inc, false, [0, 6]),
    after: [
      [1, 6],
      [0, 6],
    ],
  };
  const predict = fit([...evidence, repeated, repeated]);
  const atoms = predict(input(choose, dec, null, [7, -4]));
  expect(atoms).toHaveLength(2);
  expect(atoms).toContainEqual({
    state: [
      [7, -7],
      [7, -7],
    ],
    prob: 0.25,
  });
  expect(atoms).toContainEqual({
    state: [
      [7, -7],
      [7, -4],
    ],
    prob: 0.75,
  });
});

test("retains contradictory observations of both the patch and the visible history", () => {
  const observed = input(choose, "a[i] += step", true, [0]);
  const predict = fit([
    { input: observed, after: [[2], [0]] },
    { input: observed, after: [[-1], [-1]] },
  ]);
  const atoms = predict({ ...observed, before: [[9], [9]] });
  expect(atoms).toHaveLength(4);
  for (const value of [11, 8]) {
    for (const second of [9, value]) {
      expect(atoms).toContainEqual({ state: [[value], [second]], prob: 0.25 });
    }
  }
});

test("a no-op labels the write but provides no evidence that the second slot stayed independent", () => {
  const unchanged = {
    input: input(choose, nop, true, [3, 4]),
    after: [
      [3, 4],
      [3, 4],
    ],
  };
  const train = [evidence[2]!, unchanged];
  expect(fit(train)(input(choose, dec, true, [7, -4]))).toEqual([]);
  const predict = fit([...train, evidence[0]!]);
  expect(predict(input(choose, dec, true, [7, -4]))).toEqual([
    {
      state: [
        [7, -7],
        [7, -7],
      ],
      prob: 1,
    },
  ]);
  expect(predict(input(choose, nop, true, [7, -4]))).toEqual([
    {
      state: [
        [7, -4],
        [7, -4],
      ],
      prob: 1,
    },
  ]);
});

test("abstains on empty training and unseen write/index, setup, or visible signal", () => {
  const observed = input(choose, inc, true, [7, -4]);
  expect(fit([])(observed)).toEqual([]);
  const predict = fit([evidence[0]!]);
  for (const change of [{ write: dec }, { index: 1 }, { setup: invert }, { signal: false }]) {
    expect(predict({ ...observed, ...change })).toEqual([]);
  }
});
