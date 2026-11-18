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
