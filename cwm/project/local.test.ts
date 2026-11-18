import { rejects } from "node:assert/strict";
import { expect, test } from "bun:test";
import { ProjectSession } from "./agent.ts";
import { wire } from "./protocol.ts";
import { editLocal, localSplice } from "./local.ts";
import { modelProcess } from "./model-process.ts";

test("local line boundaries preserve CRLF, Unicode, unterminated lines and insertions at EOF", () => {
  expect(localSplice("", 0, 0, "//\n")).toBe("//\n");
  expect(localSplice("雪\r\nold\r\n😀", 1, 2, "new\r\n")).toBe("雪\r\nnew\r\n😀");
  expect(localSplice("a\n", 1, 1, "b")).toBe("a\nb");
  expect(localSplice("a\n", 0, 1, "")).toBe("");
  expect(() => localSplice("", 0, 1, "")).toThrow();
});

test("only an independently reconstructed and parsed replacement reaches the workspace", async () => {
  const path = "src/main.ts";
  const before = "// 雪\r\nexport const x = 0;";
  const replacement = "export const x = 1;";
  const text = "// 雪\r\n" + replacement;
  const files = new Map([[path, before]]);
  const session = new ProjectSession(
    { files },
    async () => {
      throw Error("unexpected chat");
    },
    async (files) => ({
      exit: files.get(path) === text ? 0 : 1,
      stdout: "",
      stderr: "Expected: 1\nReceived: 0",
    }),
  );
  const valid = { stopped: true, start: 1, end: 2, replacement, text };
  for (const proposal of [
    { ...valid, text: text.replace("雪", "x") },
    { ...valid, replacement: "export const = ", text: "// 雪\r\nexport const = " },
  ]) {
    expect((await editLocal(session, async () => proposal, path, "update the value")).stop).toBe(
      "invalid",
    );
    expect(files.get(path)).toBe(before);
  }
  const result = await editLocal(
    session,
    async (input) => {
      expect(input.observed).toBe("fail\nExpected: 1\nReceived: 0");
      expect(input.files).toEqual([{ path, text: before }]);
      return valid;
    },
    path,
    "update the value",
  );
  expect(result.stop).toBe("tested");
  expect(files.get(path)).toBe(text);
  expect(result.after?.run?.exit).toBe(0);
});

test("a capped local fill retains its chosen span and a follow-up forecast uses the supplied generator", async () => {
  const path = "counter.ts";
  const original = "export const count = 0;\n";
  const files = new Map([[path, original]]);
  let tests = 0;
  const session = new ProjectSession(
    { files },
    async () => {
      throw Error("unexpected generation on the default model");
    },
    async () => {
      tests++;
      return { exit: 1, stdout: "", stderr: "Expected: 1\nReceived: 0" };
    },
  );
  const cap = { stopped: false as const, error: "replacement token cap", start: 0, end: 1 };
  const result = await editLocal(session, async () => cap, path, "Increase count");
  expect(result.reply).toEqual(cap);
  const history = session.history.slice();
  const action = { op: "test" } as const;
  const answer = await session.predict(action, undefined, {
    includeSources: true,
    generate: async (prompt, limit) => {
      expect(prompt).toBe(wire([path], history, action));
      expect(limit).toBe(8);
      return { text: "fail", finish: "stop", tokens: 2, inputTokens: 24 };
    },
  });
  expect(answer.prediction).toBe("fail");
  expect(files.get(path)).toBe(original);
  expect(session.history).toEqual(history);
  expect(tests).toBe(1);
});

test("a serial model process reuses weights and drops interrupted or malformed replies before reuse", async () => {
  const server = modelProcess(process.execPath, [
    "-e",
    `
    let count = 0;
    for await (const line of require('node:readline').createInterface({input: process.stdin})) {
      const value = JSON.parse(line);
      if (value === "wait") await Bun.sleep(60000);
      console.log(value === "bad" ? "invalid" : JSON.stringify({count: ++count, value}));
    }`,
  ]);
  try {
    expect(await Promise.all([server.request("a"), server.request("b")])).toEqual([
      { count: 1, value: "a" },
      { count: 2, value: "b" },
    ]);
    await rejects(server.request("bad"));
    expect(await server.request("c")).toEqual({ count: 1, value: "c" });
    await rejects(server.request("wait", AbortSignal.timeout(50)));
    expect(await server.request("d")).toEqual({ count: 1, value: "d" });
  } finally {
    await server.close();
  }
  await rejects(server.request("e"));
});

test("a fresh local forecast sees current source without granting a read or executing a tool", async () => {
  const path = "price.ts";
  const original = "export const price = 1;";
  const files = new Map([[path, original]]);
  const session = new ProjectSession({ files }, async () => {
    throw Error("unexpected default model");
  });
  const prompts: string[] = [];
  for (const text of [original, "export const price = 2;"]) {
    files.set(path, text);
    await session.predict({ op: "test" }, undefined, {
      includeSources: true,
      generate: async (prompt) => {
        prompts.push(prompt);
        return { text: "pass", finish: "stop", tokens: 2, inputTokens: 24 };
      },
    });
    expect(JSON.parse(prompts.at(-1)!.split("\n")[1]!).visibleSources).toEqual([{ path, text }]);
  }
  expect(prompts[0]).not.toBe(prompts[1]);
  expect(session.history).toEqual([]);
  expect((await session.act({ op: "write", path, text: original })).observed).toBe("rejected");
});

test("a local forecast reuses earlier observed bytes across turns and reports refreshed files", async () => {
  const path = "data.ts";
  const text = "//" + "x".repeat(9000);
  const other = "extra.ts";
  const files = new Map([
    [path, text],
    [other, text + "more"],
  ]);
  const prompts: string[] = [];
  const session = new ProjectSession({ files }, async (prompt) => {
    prompts.push(prompt);
    return { text: "fail", finish: "stop", inputTokens: 10, tokens: 2 };
  });
  await session.begin("inspect");
  await session.act({ op: "read", path });
  await session.act({ op: "read", path: other });
  await session.begin("follow-up");
  await session.predict({ op: "test" }, undefined, { includeSources: true });
  expect(JSON.parse(prompts[0]!.split("\n")[1]!).visibleSources).toBeUndefined();
  files.set(path, "export const updated = true;");
  await session.predict({ op: "test" }, undefined, { includeSources: true });
  expect(JSON.parse(prompts[1]!.split("\n")[1]!).visibleSources).toEqual([
    { path, text: files.get(path) },
  ]);
});
