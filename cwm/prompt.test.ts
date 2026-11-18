import assert from "node:assert/strict";
import { test } from "bun:test";
import { assess, forecast, parseExample, plan, trainingModel, verify } from "./prompt.ts";
import { applyEdit } from "./cwm.ts";

const fitted = trainingModel();
function draft(body: string) {
  return {
    entry: "inventory.ts",
    fn: "update",
    files: {
      "inventory.ts": "export function update(stock: number, ordered: number) { " + body + " }",
    },
  };
}

test("an observed local write distinguishes two candidates with the same return value", async () => {
  const model = await fitted;
  const initial = draft("stock = stock + ordered; return ordered;");
  const args = [7, 2];
  const [returnsOnly] = assess(model, initial, [{ args, returns: 2 }]);
  assert.equal(returnsOnly?.status, "match");
  const example = parseExample('{"args":[7,2],"returns":2,"visits":[{"stock":7},{"stock":5}]}');
  const result = await plan(model, initial, [example]);
  assert.equal(result.status, "repaired");
  assert.equal(result.originalAssessment[0]?.status, "mismatch");
  assert.equal(result.assessment[0]?.status, "match");
  assert.deepEqual(applyEdit({ ...initial, args }, result.edit).files, result.draft.files);
  const report = await verify(model, result.draft, args);
  assert.equal(report.comparison.complete, true);
  assert.ok(report.comparison.exactPrefix >= 2);
});

test("ambiguous single edits preserve source and partial forecasts retain their stop reason", async () => {
  const model = await fitted,
    initial = draft("stock = stock + 2; ordered = ordered + 2; return stock + ordered;");
  const result = await plan(model, initial, [{ args: [5, 2], returns: 12 }]);
  assert.equal(result.status, "ambiguous");
  assert.equal(result.draft, initial);
  assert.equal(forecast(model, initial, [5, 2], 1).stop, "limit");
  const unsupported = draft("return [stock, ordered];");
  const report = await verify(model, unsupported, [7, 2]);
  assert.equal(report.prediction.stop, "unseen");
  assert.deepEqual(report.observed.outcome.result.value, [7, 2]);
  assert.equal(report.comparison.outcomeMatch, null);
  assert.equal(report.comparison.complete, false);
  assert.throws(() => parseExample('{"args":[2,3],"return":5}'));
});
