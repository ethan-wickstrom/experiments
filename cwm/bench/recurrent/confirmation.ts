import type { Program } from "../../cwm.ts";

const bodies = {
  repeat:
    "while (limit > unit) { limit = limit - unit; } if (unit > limit) { unit = unit + limit; } return unit;",
  twice:
    "if (limit < unit) { limit = unit - limit; } if (limit === unit) { return unit + 41; } return (limit * unit) - 1;",
  returnFirst: "return (limit + unit) * (unit + 2);",
  outside: "for (let i = 0; i < unit; i++) { limit += i; } return limit;",
};
export const confirmation: Program[] = Object.entries(bodies).flatMap(([key, body]) => {
  const entry = key + ".ts";
  return [
    [3, 8],
    [10, 2],
    [7, 7],
    [23, 4],
    [11, 3],
  ].map((args) => ({
    files: { [entry]: `export function compute(limit:number, unit:number) {\n  ${body}\n}` },
    entry,
    fn: "compute",
    args,
  }));
});
