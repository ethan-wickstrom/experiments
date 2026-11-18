// The oracle adapter alone sees these spellings. Both committees receive only the opaque key.
const dictionary = { k17: "^", k42: "|" } as const;
type Key = keyof typeof dictionary;
type Pair = readonly [number, number];
const keys: Key[] = ["k17", "k42"];
const train: Pair[] = [
  [1, 4],
  [1, 8],
  [2, 4],
  [2, 8],
];
const pool: Pair[] = [
  [1, 16],
  [3, 5],
  [2, 16],
  [6, 3],
  [7, 9],
];
const test: Pair[] = [
  [3, 1],
  [6, 5],
  [9, 3],
  [12, 10],
  [15, 7],
  [5, 5],
  [33, 35],
];
