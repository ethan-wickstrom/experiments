import type { Program } from "../../cwm.ts";

// All renderings and interventions descended from one body stay in one split.
const train = {
  add: "A = A + B;\nreturn A;",
  sub: "B = A - B;\nreturn B;",
  mul: "A = B * A;\nreturn B;",
  less: "if (A < B) {\nreturn A;\n}\nreturn B;",
  greater: "if (A > B) {\nreturn B + A;\n}\nreturn A * B;",
  equal: "if (A === B) {\nreturn 123;\n}\nreturn B;",
  chain: "A = A - B;\nB = B + A;\nreturn A - B;",
  count: "while (A > B) {\nA = A - B;\n}\nreturn A + B;",
};
const held = {
  accumulate: "while (A > 1) {\nB = B + A * 2;\nA = A - 1;\n}\nreturn B - A;",
  euclid: "while (A > B) {\nA = A - B;\n}\nif (A === B) {\nreturn 314;\n}\nreturn (A + B) * B;",
  nested: "if (B < A) {\nwhile (A > B + 1) {\nA = A - B;\n}\n}\nreturn A * B;",
  swap: "if (A < B) {\nB = (B - A) * 2;\n} else {\nA = (A + B) * 2;\n}\nreturn B + A;",
  plusTwin: "A = A + B * 2;\nreturn B;",
  minusTwin: "A = A - B * 2;\nreturn B;",
  unknown: "A = A ^ B;\nreturn B;",
};
type Layout = "plain" | "varied" | "packed" | "wrapped";
function render(body: string, layout: Layout) {
  const [a, b] = (
    {
      plain: ["x", "y"],
      varied: ["counter", "increment"],
      packed: ["distance", "stride"],
      wrapped: ["remaining", "δ"],
    } as const
  )[layout];
  const text = body.replaceAll(/\bA\b/g, a).replaceAll(/\bB\b/g, b);
  const lines = text.split("\n");
  if (layout === "packed")
    return `export function run(${a}:number,${b}:number){ /* 🧮 */ ${lines.join(" ")} }`;
  const spaced = lines.map(
    (l) =>
      (layout === "plain" ? "" : "   ") +
      l.replaceAll("return ", layout === "plain" ? "return " : "return    "),
  );
  return `export function run(${a}:number, ${b}:number) {\n${spaced.join(layout === "wrapped" ? "\r\n\n" : "\n")}\n}`;
}
export type Split = "fixed" | "varied" | "held";
export function cases(split: Split) {
  const rows: { family: string; layout: Layout; program: Program }[] = [];
  for (const [family, body] of Object.entries(split === "held" ? held : train)) {
    const heldInputs = [
      [1, 4],
      [6, 6],
      [9, 2],
      [15, 3],
    ];
    const folds =
      split === "held"
        ? [heldInputs, heldInputs]
        : [
            [
              [1, 2],
              [3, 3],
              [5, 2],
            ],
            [
              [2, 4],
              [4, 4],
              [7, 3],
            ],
          ];
    for (const [i, argsList] of folds.entries()) {
      const layout =
        split === "held"
          ? i
            ? "wrapped"
            : "packed"
          : split === "varied" && i
            ? "varied"
            : "plain";
      const entry = `${family}-${layout}.ts`;
      for (const args of argsList)
        rows.push({
          family,
          layout,
          program: { entry, fn: "run", args, files: { [entry]: render(body, layout) } },
        });
    }
  }
  return rows;
}
