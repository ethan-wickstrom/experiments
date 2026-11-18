import assert from "node:assert/strict";
import { isDeepStrictEqual } from "node:util";
import { trace, transitions, type Program } from "../cwm.ts";
import { actionCases } from "./action-cases.ts";
import { fitActions } from "./action.ts";
import { empty, score, readout } from "./score.ts";
import { fitSites } from "./sites.ts";

async function labels(inputs: Program[]) {
  const runs = [];
  for (let i = 0; i < inputs.length; i += 4)
    runs.push(...(await Promise.all(inputs.slice(i, i + 4).map((p) => trace(p)))));
  return runs;
}
const train = await labels(actionCases.train);
const models = [
  ...(["source", "filename-blind", "syntax", "syntax+operands"] as const).map(
    (name) => [name, fitSites(name, train)] as const,
  ),
  ["readout", readout],
  ["action", fitActions(train)],
] as const;
const report = [];
for (const split of ["control", "fresh"] as const) {
  const test = await labels(actionCases[split]);
  for (const [name, predict] of models) {
    const counts = empty();
    for (const t of test) {
      score(predict, t, counts);
      if (split === "control" && name === "action") {
        const edge = [...transitions(t)].find(([f, n]) => f.kind === "step" && n.kind === "return");
        assert(edge);
        const { files, entry, fn } = t;
        assert(
          isDeepStrictEqual(predict({ files, entry, fn, args: [] }, edge[0]), edge[1]),
          t.entry,
        );
      }
    }
    report.push({ split, name, ...counts });
  }
}
console.log(JSON.stringify(report, null, 2));
