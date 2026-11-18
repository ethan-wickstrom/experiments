import { expect, test } from "bun:test";
import { rejects } from "node:assert/strict";
import { ProjectSession } from "./agent.ts";
import { editReturn } from "./return.ts";

const path = "metrics.ts";
const source =
  '// 雪🦊\r\nexport const title = "Index";\r\nexport function last(n: number) { return /* slot */ (0); }\r\nexport const defaultSize = 3;\r\n';

test("a single verbatim model response changes only the return argument and runs the visible suite", async () => {
  const files = new Map([
    [path, source],
    ["metrics.test.ts", "// visible"],
  ]);
  let calls = 0;
  const session = new ProjectSession(
    { files },
    async (prompt, limit, _signal, grammar, verbatim) => {
      calls++;
      expect(limit).toBe(96);
      expect(verbatim).toBe(true);
      expect(grammar).toBeUndefined();
      const wire = JSON.parse(prompt.slice(prompt.indexOf("\n") + 1));
      expect(wire).toEqual({
        path,
        signature: "function last(n: number)",
        body: "{ return /* slot */ (0); }",
        tests: { "metrics.test.ts": "// visible" },
        requests: ["Get the last index"],
      });
      return { text: " \nn - 1\n", finish: "stop", inputTokens: 16, tokens: 4 };
    },
    async (project) => {
      expect(project.get(path)).toBe(source.replace("(0)", "n - 1"));
      return { exit: 0, stdout: "", stderr: " 1 pass" };
    },
  );
  const result = await editReturn(session, path, "last", "Get the last index");
  expect(calls).toBe(1);
  expect(result.stop).toBe("tested");
  expect(result.events[0]?.reply.text).toBe(" \nn - 1\n");
  expect(session.history.at(-1)).toEqual({ action: { op: "test" }, observed: "pass" });
});

test("incomplete or non-expression replies never edit the file or retry", async () => {
  for (const [text, finish] of [
    ["n", "length"],
    ["return n - 1;", "stop"],
    ["n - 1; unrelated();", "stop"],
    ["\x60\x60\x60ts\nn - 1\n\x60\x60\x60", "stop"],
    ["n - 1 // because indices start at zero", "stop"],
    ["", "stop"],
  ] as const) {
    const files = new Map([[path, source]]);
    const session = new ProjectSession(
      { files },
      async () => ({
        text,
        finish,
        tokens: 8,
        inputTokens: 24,
      }),
      async () => {
        throw Error("Unexpected execution");
      },
    );
    const result = await editReturn(session, path, "last", "Revise");
    expect(result.stop).toBe(finish === "length" ? "incomplete" : "invalid");
    expect(result.events).toHaveLength(1);
    expect(files.get(path)).toBe(source);
  }
});

test("rejects a missing export or a function with extra statements before inference", async () => {
  const session = new ProjectSession(
    { files: new Map([[path, "export function measure(n: number) { const k = n; return k; }"]]) },
    async () => {
      throw Error("Unexpected model query");
    },
  );
  for (const name of ["last", "measure"])
    await rejects(editReturn(session, path, name, "Revise"), /one return expression/);
});
