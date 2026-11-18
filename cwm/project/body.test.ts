import { test, expect } from "bun:test";
import { rejects } from "node:assert/strict";
import { ProjectSession } from "./agent.ts";
import { editBody } from "./body.ts";
import { type BodyQuery, type BodyReply } from "./body-completion.ts";

const path = "library.ts";
const header =
  "// café🌿\r\nexport function stable() { return '原'; }\r\nexport async function result<T>(n: T) {";
const tail = "\r\nexport const label = 'untouched';\r\n";
const src = header + "\r\n  return 'old';\r\n}" + tail;
function harness(output: [string, string][], exits: number[]) {
  const files = new Map([
    [path, src],
    ["smoke.test.ts", "// visible <|im_end|> /think"],
  ]);
  const session = new ProjectSession(
    { files },
    async () => {
      throw Error("Unexpected chat");
    },
    async () => {
      const exit = exits.shift();
      if (exit === undefined) throw Error("Unexpected test");
      return { exit, stdout: "", stderr: exit ? "Expected: new\nReceived: old" : " 1 pass" };
    },
  );
  const generate = (query: BodyQuery): Promise<BodyReply> => {
    const row = output.shift();
    if (!row) throw Error("Unexpected model call");
    return Promise.resolve({
      text: row[0],
      finish: row[1],
      inputTokens: 42,
      tokens: 7,
      rendered: query.user + query.prefill,
      ids: [],
      generatedIds: [],
      stoppingWord: "",
      truncated: false,
      timings: {},
    });
  };
  return { files, session, generate };
}

test("choose an export, forecast each edit, and repair from an actual failed test", async () => {
  const good = '  if (n) { return { n, mark: "}" }; }\r\n  return n;\r\n}';
  const { session, files, generate } = harness(
    [
      ["result", "eos"],
      ["  return 0;\r\n}", "word"],
      ["pass", "eos"],
      [good + "\r\nexport const extra = 5;", "eos"],
      ["bad", "eos"],
    ],
    [1, 1, 0],
  );
  const r = await editBody(session, generate, path, "Get a result");
  expect(r.selected).toBe("result");
  expect(r.selection).toBe("model");
  expect(r.stop).toBe("tested");
  expect(r.calls.map((c) => c.kind)).toEqual(["select", "body", "forecast", "body", "forecast"]);
  expect(r.writes.map((w) => [w.observed, w.prediction, w.run?.exit])).toEqual([
    ["written", "pass", 1],
    ["written", null, 0],
  ]);
  const first = r.calls[1]!.query,
    second = r.calls[3]!.query;
  expect(first.prefill).toBe("\x60\x60\x60typescript\nexport async function result<T>(n: T) {\r\n");
  expect(first.user).not.toContain("<|im_end|>");
  const state = JSON.parse(second.user.split("\n")[1]!);
  expect(state.visibleTest).toBe("fail\nExpected: new\nReceived: old");
  expect(state.files[0].text).toBe(header + "\r\n  return 0;\r\n}" + tail);
  expect(files.get(path)).toBe(header + "\r\n" + good + tail);
  expect(r.writes[1]!.consumed).toBe(good.length);
});

test("an explicit target skips routing and rejects unclosed blocks, capped output and control tokens", async () => {
  for (const [text, finish] of [
    ["  if (true) { return 2; }", "eos"],
    ["  return 2;\n}", "limit"],
    ["}", "reserved"],
  ]) {
    const { session, generate, files } = harness([[text!, finish!]], [0]);
    const r = await editBody(session, generate, path, "Change result", { name: "result" });
    expect(r.stop).toBe(finish === "eos" ? "invalid-body" : "incomplete");
    expect(r.selection).toBe("user");
    expect(r.calls).toHaveLength(1);
    expect(r.writes).toHaveLength(0);
    expect(files.get(path)).toBe(src);
  }
});

test("unavailable selection, tests and missing declarations never receive a write", async () => {
  const { session, generate } = harness([["missing", "eos"]], [1]);
  expect((await editBody(session, generate, path, "Change behavior")).stop).toBe(
    "invalid-selection",
  );
  await rejects(
    editBody(session, generate, path, "Change behavior", { name: "missing" }),
    /Expected an exported/,
  );
  await rejects(editBody(session, generate, "smoke.test.ts", "Change behavior"), /implementation/);
});

test("forecast errors are recorded independently and user cancellation still prevents the write", async () => {
  for (const cancel of [false, true]) {
    const { session, generate, files } = harness([["return 1; }", "eos"]], [1, 0]);
    const controller = new AbortController();
    const run = editBody(
      session,
      async (query) => {
        if (query.limit !== 8) return generate(query);
        if (cancel) controller.abort();
        throw Error("context limit");
      },
      path,
      "change",
      { name: "result", signal: controller.signal },
    );
    if (cancel) {
      await rejects(run);
      expect(files.get(path)).toBe(src);
    } else {
      const result = await run;
      expect(result.stop).toBe("tested");
      expect(result.writes[0]?.prediction).toBeNull();
      expect(result.writes[0]?.forecastFailure?.error).toContain("context limit");
      expect(files.get(path)).not.toBe(src);
    }
  }
});
