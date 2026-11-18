import type { Program } from "../../cwm.ts";
import { cases } from "./cases.ts";

const probes = [
  [3, 8],
  [8, 3],
  [7, 7],
];
function examples(bodies: Record<string, string>, pairs: number[][]): Program[] {
  return Object.entries(bodies).flatMap(([id, body]) => {
    const entry = id + ".ts";
    return pairs.map((args) => ({
      entry,
      fn: "advance",
      args,
      files: { [entry]: `export function advance(left:number,right:number) {\n${body}\n}` },
    }));
  });
}
export const targeted = examples(
  {
    oneArm: "if (left < right) { left = left + right; } return left;",
    twoArms:
      "if (left > right) { right = left - right; } else { left = right + left; } return right;",
  },
  probes,
);
const training = cases("fixed");
export const repeated = ["add", "sub"].flatMap((id) => {
  const p = training.find((r) => r.family === id)!.program;
  return probes.map((args) => ({ ...p, args }));
});
export const junctionTest = examples(
  {
    // A direct return inside one arm and a join after the other arm.
    early:
      "if (left > right) { left = (left - right) * 2; return left; } if (left < right) { right = left + right; } return right;",
    cascade:
      "if (left < right) { left = left * right; } if (left > right) { right = left - right; } else { right = right + left; } return right;",
    loopArm:
      "if (left > right) { while (left > right) { left = left - right; } right = right + left; } return right;",
  },
  [
    [2, 11],
    [11, 2],
    [5, 5],
    [17, 4],
  ],
);
