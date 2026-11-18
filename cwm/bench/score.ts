import { isDeepStrictEqual } from "node:util";
import { transitions, type Frame, type Observation, type Program, type Trace } from "../cwm.ts";
import { cases } from "./cases.ts";
import { cache, load } from "./collect.ts";
import { fitSites } from "./sites.ts";

type Predict = (p: Program, f: Frame) => Observation | undefined;
const empty = () => ({
  runs: 0,
  transitions: 0,
  correct: 0,
  wrong: 0,
  abstained: 0,
  correctNonterminal: 0,
  exactRollouts: 0,
});
type Counts = ReturnType<typeof empty>;

export function score(predict: Predict, t: Trace, c: Counts) {
  c.runs++;
  // Predictors get only the source and the current observations, never truth or entry arguments.
  const p = { entry: t.entry, files: t.files, fn: t.fn, args: [] };
  for (const [f, next] of transitions(t)) {
    const guess = predict(p, f);
    c.transitions++;
    if (!guess) c.abstained++;
    else if (isDeepStrictEqual(guess, next)) {
      c.correct++;
      if ("stack" in next) c.correctNonterminal++;
    } else c.wrong++;
  }
  const start = t.frames.findIndex((f) => f.stack[0]?.file === t.entry && f.stack[0]?.fn === t.fn);
  if (start < 0) throw new Error("Entry not observed: " + t.entry);
  let frame = t.frames[start]!;
  for (let i = start; i < t.frames.length; i++) {
    const guess = predict(p, frame);
    if (!guess || !isDeepStrictEqual(guess, t.frames[i + 1] ?? t.outcome)) return;
    if (!("stack" in guess)) {
      c.exactRollouts++;
      return;
    }
    frame = guess;
  }
}

if (import.meta.main) {
  const [root] = process.argv.slice(2);
  if (!root) throw new Error("Usage: bun bench/score.ts CACHE");
  const path = await cache(root);
  const train: Trace[] = [],
    test = [];
  for (const { family, split, program } of cases()) {
    const t = await load(path(program), program);
    if (split === "train") train.push(t);
    else test.push({ family, split, t });
  }
  const result = [];
  for (const name of [
    "source",
    "filename-blind",
    "syntax",
    "syntax+operands",
    "readout",
  ] as const) {
    const predict: Predict =
      name === "readout"
        ? (p, f) =>
            f.kind === "return" && f.stack.length === 1 && f.stack[0]?.fn === p.fn && f.value?.exact
              ? { kind: "returned", result: f.value }
              : undefined
        : fitSites(name, train);
    for (const [family, rows] of Map.groupBy(test, (r) => r.family)) {
      const counts = empty();
      for (const { t } of rows) score(predict, t, counts);
      result.push({ model: name, family, split: rows[0]!.split, ...counts });
    }
  }
  console.log(JSON.stringify({ trainRuns: train.length, rows: result }, null, 2));
}
