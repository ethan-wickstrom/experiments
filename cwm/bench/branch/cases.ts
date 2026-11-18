type Pair = readonly [number, number];
type Spec = { id: string; body: string; pairs: Pair[] };
const full: Pair[] = [
  [1, 1],
  [1, 2],
  [2, 1],
  [2, 2],
  [-3, 4],
  [5, -2],
];
const fresh: Pair[] = [
  [8, 3],
  [5, 4],
  [3, 7],
  [6, 6],
];
export const training: Spec[] = [
  ...["+", "-", "*"].map((op, i) => ({
    id: "scalar" + i,
    body: `x = x ${op} y;\nreturn x;`,
    pairs: full,
  })),
  ...["<", ">", "==="].map((op, i) => ({
    id: "test" + i,
    body: `if (x ${op} y) {\n  return x;\n}\nreturn y;`,
    pairs:
      i === 2
        ? ([
            [2, 4],
            [1, 3],
          ] as Pair[])
        : full,
  })),
];
export const held: Spec[] = [
  {
    id: "join",
    body: "if (y < x) {\n  x = (x - y) * 2;\n} else {\n  x = x + y;\n}\nreturn x - y;",
    pairs: fresh,
  },
  {
    id: "nested",
    body: "if (x > y) {\n  if (x - y > y) {\n    return x * y;\n  }\n  return x + y;\n}\nreturn y - x;",
    pairs: fresh,
  },
  { id: "fallthrough", body: "if (x < y + 1) {\n  y = x + y;\n}\nreturn y * x;", pairs: fresh },
  { id: "partial", body: "if (y === x) {\n  return y * x;\n}\nreturn x - y;", pairs: fresh },
  { id: "unseen", body: "if (x <= y) {\n  x = y - x;\n}\nreturn y + x;", pairs: fresh },
];
export function programs(specs: Spec[]) {
  return specs.flatMap(({ id, body, pairs }) =>
    pairs.map((pair) => ({
      fn: "run",
      entry: id + ".ts",
      files: { [id + ".ts"]: `export function run(x: number, y: number) {\n${body}\n}` },
      args: [...pair],
    })),
  );
}
