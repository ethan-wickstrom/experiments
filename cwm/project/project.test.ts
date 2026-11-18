import { expect, test } from "bun:test";
import { mkdtemp, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { ProjectSession, type Completion } from "./agent.ts";
import { type ToolRun } from "./sandbox.ts";
import { decodeAction, type Action } from "./protocol.ts";
import { openProject } from "./workspace.ts";
import { editFile } from "./directed.ts";
import { workFile } from "./work.ts";

const answer = (text: string, finish = "stop"): Completion => ({
  text,
  finish,
  inputTokens: 0,
  tokens: 0,
});
function rows<T>(name: string) {
  return readFile(new URL("../bench/development/data/" + name + ".jsonl.gz", import.meta.url)).then(
    (bytes) =>
      gunzipSync(bytes)
        .toString()
        .trimEnd()
        .split("\n")
        .map((line) => JSON.parse(line) as T),
  );
}

test("all 66 taught actions pass the production grammar with byte-identical observed prefixes", async () => {
  type Record =
    | { type: "initial"; files: { [name: string]: string } }
    | { type: "request"; user: string; supplied: { [name: string]: string } }
    | { type: "action"; action: Action; oracle?: ToolRun }
    | { type: "candidate" };
  const records = await rows<Record>("oracle");
  const policy = (await rows<{ task: string; prompt: string; target: string }>("projects")).filter(
    (r) => r.task === "policy",
  );
  let cursor = 0,
    tests = 0;
  let session: ProjectSession | undefined;
  let goal = "";
  const outputs: ToolRun[] = [];
  for (const record of records) {
    if (record.type === "initial") {
      session = new ProjectSession(
        { files: new Map(Object.entries(record.files)) },
        async (prompt) => {
          const row = policy[cursor++]!;
          expect(prompt).toBe(row.prompt);
          return answer(row.target);
        },
        async () => {
          tests++;
          const run = outputs.shift();
          if (!run) throw Error("Unexpected test dispatch");
          return run;
        },
      );
    } else if (record.type === "request") {
      goal = record.user;
      for (const [p, s] of Object.entries(record.supplied)) session!.project.files.set(p, s);
    } else if (record.type === "action") {
      if (record.oracle) outputs.push(record.oracle);
      if (record.action.op === "done") expect((await session!.turn(goal)).stop).toBe("done");
    }
  }
  expect(cursor).toBe(66);
  expect(tests).toBe(24);
  expect(outputs).toHaveLength(0);
});

test("prediction never applies the proposed write or impersonates real tests", async () => {
  const files = new Map([["a.ts", "initial"]]);
  const session = new ProjectSession(
    { files },
    async () => answer("pass", "length"),
    async () => {
      throw Error("unexpected execution");
    },
  );
  expect(await session.predict({ op: "write", path: "a.ts", text: "replacement" })).toMatchObject({
    text: "pass",
    prediction: null,
  });
  expect(session.history).toEqual([]);
  expect(files.get("a.ts")).toBe("initial");
  expect(session.predict({ op: "read", path: "a.ts" })).rejects.toThrow();
  expect(() => decodeAction('{"op":"done","observed":"pass"}')).toThrow();
});

test("refreshes external edits and rejects stale, unread, and symlink writes", async () => {
  const dir = await mkdtemp(join(tmpdir(), "cwm-files-"));
  try {
    const source = join(dir, "a.ts");
    await writeFile(source, "old");
    const project = await openProject(dir);
    const session = new ProjectSession(project, async () => answer('{"op":"done"}'));
    await writeFile(source, "external");
    await session.begin("revise");
    expect((await session.act({ op: "write", path: "a.ts", text: "bad" })).observed).toBe(
      "rejected",
    );
    expect((await session.act({ op: "read", path: "a.ts" })).observed).toBe("external");
    await writeFile(source, "newer");
    expect(session.act({ op: "write", path: "a.ts", text: "stale" })).rejects.toThrow();
    await symlink(dir, join(dir, "link"));
    expect(project.persist("link/nested.ts", "bad")).rejects.toThrow();
    expect((await session.act({ op: "write", path: "new/ok.ts", text: "ok" })).observed).toBe(
      "written",
    );
    expect(await readFile(join(dir, "new/ok.ts"), "utf8")).toBe("ok");
    expect(await readFile(source, "utf8")).toBe("newer");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("truncated directed source and multiple fenced files leave the workspace intact", async () => {
  for (const reply of [
    answer("export const ok = 1", "length"),
    answer(
      "\x60\x60\x60ts\nexport const x=1;\n\x60\x60\x60\n\x60\x60\x60ts\nexport const x=2;\n\x60\x60\x60",
    ),
  ]) {
    const session = new ProjectSession({ files: new Map() }, async () => reply);
    const result = await editFile(session, "a.ts", "create it");
    expect(["invalid", "incomplete"]).toContain(result.stop);
    expect(session.project.files.size).toBe(0);
  }
});

test("directed edits disclose Bun-discovered underscore tests alongside dot tests", async () => {
  const tests = { "rate_test.ts": "one", "nested/rate_SPEC.mts": "two", "base.test.tsx": "three" };
  const files = new Map(Object.entries({ "rate.ts": "", "rate-test.ts": "helper", ...tests }));
  const session = new ProjectSession({ files }, async (prompt) => {
    expect(JSON.parse(prompt.split("\n")[1]!).tests).toEqual(tests);
    return answer("", "length");
  });
  expect((await editFile(session, "rate.ts", "Revise the rate")).stop).toBe("incomplete");
});

test("forecast observes edits on disk without authorizing a replacement", async () => {
  const dir = await mkdtemp(join(tmpdir(), "cwm-forecast-"));
  try {
    const file = join(dir, "a.test.ts");
    await writeFile(file, "before");
    const project = await openProject(dir);
    await writeFile(file, "changed");
    const session = new ProjectSession(project, async (prompt) => {
      expect(JSON.parse(prompt.slice(prompt.indexOf("\n") + 1)).externalChanges).toEqual([
        { path: "a.test.ts", text: "changed" },
      ]);
      return answer("fail");
    });
    expect((await session.predict({ op: "test" })).prediction).toBe("fail");
    expect(session.history).toEqual([]);
    expect(
      (await session.act({ op: "write", path: "a.test.ts", text: "overwritten" })).observed,
    ).toBe("rejected");
    expect(await readFile(file, "utf8")).toBe("changed");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("reading after a factorized edit preserves the pending test across turns", async () => {
  const raw = " export const rate = 2;\n";
  const replies = ["read", "edit", raw, "read", "done", "done", "test", "done"];
  const session = new ProjectSession(
    { files: new Map([["a.ts", "export const rate = 1;"]]) },
    async (_prompt, limit, _signal, _grammar, verbatim) => {
      const next = replies.shift();
      if (next === undefined) throw Error("Unexpected model request");
      if (next === raw) {
        expect(verbatim).toBe(true);
        expect(limit).toBe(384);
      }
      return answer(next);
    },
    async () => ({ exit: 0, stdout: "", stderr: "1 pass" }),
  );
  expect((await workFile(session, "a.ts", "double the rate")).stop).toBe("untested");
  expect(session.project.files.get("a.ts")).toBe(raw);
  expect((await workFile(session, "a.ts", "keep that change")).stop).toBe("untested");
  expect((await workFile(session, "a.ts", "check it")).stop).toBe("done");
  expect(session.untestedChanges).toBe(false);
  expect(replies).toEqual([]);
});

test("C2 forecast prefixes replay the training diagnostic for array diffs", async () => {
  const session = new ProjectSession(
    { files: new Map() },
    async (prompt) => {
      expect(JSON.parse(prompt.slice(prompt.indexOf("\n") + 1)).history.at(-1).observed).toBe(
        "fail\nbehavior check failed",
      );
      return answer("fail");
    },
    async () => ({ exit: 1, stdout: "", stderr: "- [1]\n+ [2]\n(fail) visible behavior [1.2ms]" }),
    "c2",
  );
  const actual = await session.act({ op: "test" });
  expect(actual.run?.stderr).toContain("(fail) visible behavior");
  expect((await session.predict({ op: "test" })).prediction).toBe("fail");
});

test("Markdown inside valid source survives raw and single-block editing", async () => {
  const text = "/* docs\n```ts\nconst x = 1;\n```\n*/\nexport const fence = '```';\n";
  for (const wrapped of [true, false]) {
    const files = new Map<string, string>();
    const session = new ProjectSession(
      { files },
      async () => answer(wrapped ? "```ts\n" + text + "```" : text),
      async () => ({ exit: 0, stdout: "", stderr: "1 pass" }),
    );
    const turn = wrapped
      ? await editFile(session, "a.ts", "document it")
      : await workFile(session, "a.ts", "document it", { sourceOnly: true });
    expect(turn.stop).toBe("tested");
    expect(files.get("a.ts")).toBe(text);
  }
});

test("aligned work keeps unread files private after a test and rejects unread replacement before generation", async () => {
  const files = new Map([
    ["a.ts", "rejected"],
    ["a.test.ts", "test file bytes"],
  ]);
  const replies = ["read", "done", "test", "edit"];
  const session = new ProjectSession(
    { files },
    async () => answer(replies.shift()!),
    async () => ({ exit: 1, stderr: "stack dump", stdout: "Expected: misleading stdout" }),
  );
  expect((await workFile(session, "a.ts", "read this")).stop).toBe("done");
  const second = await workFile(session, "a.ts", "revise it");
  expect(second.stop).toBe("rejected");
  expect(second.events).toHaveLength(2);
  for (const event of second.events)
    expect(JSON.parse(event.request.split("\n")[1]!).files).toEqual([]);
  expect(second.events[0]).toMatchObject({
    observed: "fail\nbehavior check failed",
    run: { stderr: "stack dump", stdout: "Expected: misleading stdout" },
  });
  expect(second.events[1]!.observed).toBe("rejected");
  expect(files.get("a.ts")).toBe("rejected");
  expect(replies).toHaveLength(0);
});

test("the historical full-context policy still sees the project at unread and requests rejected source", async () => {
  const text = "export const value=1;";
  const files = new Map([["a.ts", text]]);
  const replies = ["edit", "export const value=2;"];
  const session = new ProjectSession({ files }, async () => answer(replies.shift()!));
  const result = await workFile(session, "a.ts", "revise", { visibility: "full-context" });
  expect(result.stop).toBe("rejected");
  expect(result.events).toHaveLength(2);
  expect(JSON.parse(result.events[0]!.request.split("\n")[1]!)).toMatchObject({
    status: "unread",
    files: [{ path: "a.ts", text }],
  });
  expect(files.get("a.ts")).toBe(text);
});
