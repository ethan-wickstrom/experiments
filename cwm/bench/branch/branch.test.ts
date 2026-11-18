import { expect, test } from "bun:test";
import { fingerprintInput } from "../composition/fingerprint.ts";
import { graph, path, train, type Demo } from "./predict.ts";

test("a bounded class fingerprint separates every coefficient vector, not only the arithmetic tokens", () => {
  for (const [arity, k] of [
    [1, 3],
    [2, 2],
    [3, 1],
  ] as const) {
    const query = fingerprintInput(arity, k)!;
    let weights = [1];
    for (const arg of query) weights = weights.concat(weights.map((w) => w * arg));
    let labels = new Set([0]);
    for (const w of weights) {
      const expanded = new Set<number>();
      for (const label of labels) for (let c = -k; c <= k; c++) expanded.add(label + w * c);
      expect(expanded.size).toBe(labels.size * (2 * k + 1));
      labels = expanded;
    }
  }
  expect(fingerprintInput(6, 1)).toBeUndefined();
  expect(fingerprintInput(2, 0)).toBeUndefined();
});

test("branch decisions come from observed arms even when the token suggests the opposite", () => {
  const source =
    "export function run(left:number,right:number){\nif(left > right){\nreturn left;\n}\nreturn right;\n}";
  const g = graph("a.ts", source),
    node = g.nodes.get(g.entry)!;
  if (node.kind !== "if") throw Error("Missing decision");
  const demos: Demo[] = [
    [1, 2],
    [2, 1],
    [1, 1],
  ].map((store) => {
    const arm = store[0]! < store[1]!;
    return {
      g,
      raw: [],
      states: [
        { pc: g.entry, store },
        { pc: arm ? node.yes : node.no, store },
      ],
      end: { returned: store[arm ? 0 : 1]! },
    };
  });
  const model = train(demos);
  expect(model.predicates[">"]).toEqual(["lt"]);
  expect(path(model, g, [4, 8], "learned")).toEqual([
    { pc: node.yes, store: [4, 8] },
    { returned: 4 },
  ]);
  expect(path(model, g, [4, 8], "untrained")).toEqual([]);
  expect(model.next(g, { pc: g.entry, store: [Infinity, 1] }, "learned")).toBeUndefined();
});
