export const trainInputs = [
  [1, 1], [1, 2], [2, 1], [2, 2], [-3, 4], [5, -2],
] as const;

export const freshInputs = [
  [-7, 3], [3, -5], [11, 2], [4, 9],
] as const;

export interface Spec {
  id: string;
  body: string[];
}

export const atomic: Spec[] = ["+", "-", "*"].map((token, i) => ({
  id: "atom" + i,
  body: [`const m = x ${token} y;`, "return m;"],
}));

export const compositions: Spec[] = [
  { id: "right-depth2", body: ["const t = x + y * x;", "return t;"] },
  { id: "balanced-depth2", body: ["const t = (x - y) * (y + x);", "return t;"] },
  { id: "left-depth4", body: ["const t = (((x * y) - 3) + x) * 2;", "return t;"] },
  { id: "chain", body: ["const p = x + y;", "const q = y - p;", "return q + p;"] },
  { id: "contrast-forward", body: ["const p = x - y;", "const q = p * p;", "return q;"] },
  { id: "contrast-reverse", body: ["const p = y - x;", "const q = p * p;", "return q;"] },
];

export const negative: Spec = { id: "unseen", body: ["const t = x % y;", "return t;"] };

export function sourceOf({ body }: Spec) {
  return ["export function run(x: number, y: number) {", ...body, "}"].join("\n");
}
