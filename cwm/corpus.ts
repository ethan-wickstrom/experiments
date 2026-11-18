import type { Program } from "./cwm.ts";

// Same source, disjoint arguments. Emit ordinary programs for the oracle, not expected answers.
const independent = [
  [0, 1],
  [2, 1],
  [1, 3],
  [4, 0],
  [-1, 2],
];
const stress = [
  [1, 0],
  [2, 1],
  [3, 2],
  [0, 3],
  [4, 1],
];
const heldOut = [
  [5, 2],
  [6, 1],
  [2, 4],
];
const families: Record<string, [string, number[][], number[][]]> = {
  affine: [
    "return 2*x-3*y+7;",
    independent,
    [
      [8, -2],
      [9, 3],
      [-4, 7],
    ],
  ],
  coupled: [
    "return 2*x+3*y+7;",
    [
      [0, 0],
      [1, 1],
      [2, 2],
      [3, 3],
      [4, 4],
    ],
    [
      [9, 9],
      [-4, -4],
      [8, 3],
    ],
  ],
  fraction: [
    "return x/2;",
    [
      [0, 0],
      [2, 0],
      [4, 0],
      [6, 0],
    ],
    [
      [3, 0],
      [9, 0],
      [-1, 0],
    ],
  ],
  tiny: [
    "return x*1e-16;",
    [
      [1, 0],
      [2, 0],
      [3, 0],
      [4, 0],
    ],
    [
      [6, 0],
      [7, 0],
      [-1, 0],
    ],
  ],
  branch: [
    "if (x < 0) {\n return y-x;\n}\nreturn y+x;",
    [
      [2, 3],
      [-1, 3],
      [5, 3],
      [-4, 3],
    ],
    [
      [-5, 3],
      [6, 3],
      [1, 3],
    ],
  ],
  array: [
    "const a=[]; for(let i=0;i<x;i++){a.push(i+y)} return a;",
    [
      [1, 0],
      [2, 0],
      [3, 0],
      [4, 0],
    ],
    [
      [5, 0],
      [6, 0],
      [2, 1],
    ],
  ],
  quadratic: ["return x*x+y*x;", stress, heldOut],
  recursion: ["return x <= 0 ? y : run(x-1,y+2);", stress, heldOut],
};

const [split, family] = process.argv.slice(2);
if (
  (split !== "train" && split !== "held-out") ||
  (family !== undefined && !Object.hasOwn(families, family))
)
  throw new Error("Usage: bun corpus.ts train|held-out [family]");
for (const [name, [body, train, test]] of Object.entries(families)) {
  if (family !== undefined && family !== name) continue;
  const entry = name + ".ts";
  const files = { [entry]: `export function run(x:number,y:number){\n${body}\n}` };
  for (const args of split === "train" ? train : test)
    console.log(JSON.stringify({ files, entry, fn: "run", args } satisfies Program));
}
