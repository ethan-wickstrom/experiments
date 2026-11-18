import type { Program } from "../cwm.ts";

// Fixed before inspecting scores. Each pair varies only the chosen action at equal inputs.
const actions = [
  "return x+y;",
  "return x-y;",
  "return y-x;",
  "return x<y;",
  "return x>y;",
  "return x+2;",
  "return x+5;",
  "const z=x-y;\nreturn z+2;",
  "const z=x+y;\nreturn z-5;",
];
const fresh = [
  "const z=x-y;\nreturn z-5;",
  "const z=x+y;\nreturn z+2;",
  "return x+(y-2);",
  "return (x+y)>5;",
];
const trainInputs = [
  [7, 3],
  [2, 8],
  [-3, 4],
  [9, -2],
  [0, 0],
];

function fixture(
  body: string,
  id: number,
  split: "train" | "control" | "fresh",
  args: number[],
): Program {
  const entry = `${split}-${id}.ts`;
  const source = "export function run(x:number,y:number){\n" + body + "\n}";
  const names: Record<string, string> = { x: "left", y: "right", z: "mid" };
  const renamed = source
    .replace(/\b[xyz]\b/g, (k) => names[k]!)
    .replaceAll("return ", "  return   ");
  return {
    files: { [entry]: split === "train" ? source : "\n" + renamed },
    entry,
    fn: "run",
    args,
  };
}
export const actionCases = {
  train: actions.flatMap((s, i) => trainInputs.map((args) => fixture(s, i, "train", args))),
  control: actions.map((s, i) => fixture(s, i, "control", [7, 3])),
  fresh: fresh.flatMap((s, i) =>
    [
      [7, 3],
      [4, 1],
    ].map((args) => fixture(s, i, "fresh", args)),
  ),
};
