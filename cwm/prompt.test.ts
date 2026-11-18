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

test("a follow-up receives the verified draft and distinguishes oracle evidence from intent", async () => {
  const requests: { messages: { role: string; content: string }[] }[] = [];
  const source = "export function run(x: number, y: number) { return x + y; }";
  const server = Bun.serve({
    hostname: "127.0.0.1",
    port: 0,
    async fetch(req) {
      requests.push(await req.json());
      return Response.json({ choices: [{ finish_reason: "stop", message: { content: source } }] });
    },
  });
  try {
    const cli = Bun.spawn([process.execPath, "chat.ts"], {
      cwd: import.meta.dir,
      env: { ...process.env, CWM_CHAT_URL: String(server.url) },
      stdin: new Blob([
        "Sum two integers\n/verify [7,2]\nKeep the behavior and clarify the parameter names\n",
      ]),
      stdout: "pipe",
      stderr: "pipe",
    });
    const [status, out, err] = await Promise.all([
      cli.exited,
      new Response(cli.stdout).text(),
      new Response(cli.stderr).text(),
    ]);
    assert.equal(status, 0, err);
    assert.match(out, /Structured CWM vs V8 oracle/);
    assert.equal(requests.length, 2);
    const followUp = requests[1]!.messages.find((m) => m.role === "user")!.content;
    assert.ok(followUp.includes(source));
    assert.ok(followUp.includes("Sum two integers"));
    assert.ok(followUp.includes('"source":"oracle verification"'));
    assert.ok(
      followUp.includes('"observedOutcome":{"kind":"returned","result":{"value":9,"exact":true}}'),
    );
  } finally {
    await server.stop(true);
  }
});
