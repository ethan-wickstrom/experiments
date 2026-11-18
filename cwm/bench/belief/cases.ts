import type { Program } from "../../cwm.ts";

// Preselected before collecting labels. Each row and column occurs twice in each split.
const setups = [
  "flag ? a : [...a]",
  "!flag ? a.slice() : a",
  "flag ? [...a] : a",
  "!flag ? a : a.slice()",
];
const writes = ["a[index]++", "a[1 - index] -= 2", "a[1 - index] += 3", "a[index]--"];

export function cases(): { split: "train" | "test"; program: Program }[] {
  const runs: ReturnType<typeof cases> = [];
  const entry = "probe.ts",
    fn = "run";
  for (const [row, setup] of setups.entries()) {
    for (const [column, write] of writes.entries()) {
      const source = `export function run(flag: boolean, index: number) {
  const a = [2, 5];
  const b = ${setup};
  flag = false;
  ${write};
  return 7;
}`;
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
