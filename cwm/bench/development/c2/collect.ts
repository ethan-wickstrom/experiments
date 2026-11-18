/** Only trusted hand-authored sources in libraries.json are executable here. */
import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import libraries from "./libraries.json";
import { FORECAST, type Event, type Action } from "../contract.ts";
import { edit, decide, jsonState, type Source } from "./wire.ts";

type Project = (typeof libraries)[number];
type Trial = { text: string; exit: number; stdout: string; stderr: string };
export type Episode = {
  family: string;
  turn: number;
  fork: number;
  goal: string;
  path: string;
  prefix: Event[];
  files: Source[];
  before: Trial;
  alternatives: Trial[];
  after: Trial;
};
function file(p: Project, body: string, index: number) {
  const lines = body
    .split("\n")
    .map((s) => "  " + s)
    .join("\n");
  const fn = p.fn + "(" + p.args + ")";
  switch (index % 4) {
    case 0:
      return `export function ${fn} {\n${lines}\n}\n`;
    case 1:
      return `export const ${p.fn} = (${p.args}) => {\n${lines}\n};\n`;
    case 2:
      return `function ${fn} {\n${lines}\n}\n\nexport { ${p.fn} };\n`;
    default:
      return `import { edition } from "./meta";\nexport { edition };\n\nexport function ${fn} {\n${lines}\n}\n`;
  }
}
export function observation(t: Trial) {
  if (!t.exit) return "pass";
  const diag = t.stderr
    .split("\n")
    .filter((s) => /^(Expected|Received):/.test(s))
    .join("\n");
  return "fail\n" + (diag || "behavior check failed").slice(0, 240);
}
export function history(ep: Episode) {
  const events: Event[] = [...ep.prefix, { user: ep.goal }];
  for (const { path, text } of ep.files)
    events.push({ action: { op: "read", path }, observed: text });
  events.push({ action: { op: "test" }, observed: observation(ep.before) });
  return events;
}
export function derive(ep: Episode) {
  const { family, goal, path, files } = ep;
  const passing = ep.alternatives.filter((t) => t.exit === 0);
  assert.equal(passing.length, 1);
  const text = passing[0]!.text;
  const after = files.map((s) => (s.path === path ? { path, text } : s));
  const names = files.map((f) => f.path);
  const rows = [
    { family, task: "source", prompt: edit(goal, path, files), target: text },
    ...(
      [
        ["unread", [], "read"],
        ["read", files, "test"],
        ["fail", files, "edit"],
        ["written", after, "test"],
        ["pass", after, "done"],
      ] as const
    ).map(([status, visible, target]) => ({
      family,
      task: "decision",
      prompt: decide(goal, path, visible, status),
      target,
    })),
  ];
  const h = history(ep);
  const forecast = (prefix: Event[], candidate: Action, target: string) =>
    rows.push({
      family,
      task: "forecast",
      prompt: FORECAST + "\n" + jsonState({ files: names, history: prefix, candidate }),
      target,
    });
  for (const t of ep.alternatives)
    forecast(h, { op: "write", path, text: t.text }, t.exit ? "fail" : "pass");
  // At initial entry no source was read. The host rejects replacing it.
  if (ep.turn === 0) forecast([{ user: goal }], { op: "write", path, text }, "rejected");
  return rows;
}
async function run(dir: string, path: string, signal: AbortSignal): Promise<Trial> {
  const p = Bun.spawn([process.execPath, "test", "checks.test.ts"], {
    cwd: dir,
    signal,
    env: { ...process.env, NO_COLOR: "1", FORCE_COLOR: "0" },
    stdout: "pipe",
    stderr: "pipe",
  });
  const [exit, stdout, stderr, text] = await Promise.all([
    p.exited,
    new Response(p.stdout).text(),
    new Response(p.stderr).text(),
    readFile(join(dir, path), "utf8"),
  ]);
  assert(
    exit === 0 || (exit === 1 && stderr.includes("(fail)") && stderr.includes("expect(")),
    stderr,
  );
  return { text, exit, stdout, stderr };
}
async function collect(root: string, out: string, signal: AbortSignal) {
  const episodes: Episode[] = [];
  for (const [i, p] of libraries.entries()) {
    const prefix: Event[] = [];
    const dir = join(root, p.name),
      path = p.name + ".ts";
    await mkdir(dir);
    const meta = i % 4 === 3 ? [{ path: "meta.ts", text: "export const edition = 1;\n" }] : [];
    for (const f of meta) await writeFile(join(dir, f.path), f.text);
    let current = file(p, p.initial, i);
    for (const [turn, spec] of p.turns.entries()) {
      let next: Episode | undefined;
      const bodies = spec.bodies.map((body) => file(p, body, i));
      for (const [fork, goal] of spec.goals.entries()) {
        const checks =
          'import { expect, test } from "bun:test";\n' +
          `import { ${p.fn} } from "./${p.name}";\n\n` +
          `test("visible behavior", () => {\n  expect(${p.fn}(${spec.call})).toEqual(${JSON.stringify(spec.expected[fork])});\n});\n`;
        await writeFile(join(dir, "checks.test.ts"), checks);
        await writeFile(join(dir, path), current);
        const names = ["checks.test.ts", path, ...meta.map((f) => f.path)].sort();
        const files = await Promise.all(
          names.map(async (n) => ({ path: n, text: await readFile(join(dir, n), "utf8") })),
        );
        const before = await run(dir, path, signal);
        assert.equal(before.exit, 1, p.name + " " + turn + " " + goal);
        const alternatives: Trial[] = [];
        for (const body of bodies) {
          try {
            await writeFile(join(dir, path), body);
            alternatives.push(await run(dir, path, signal));
          } finally {
            await writeFile(join(dir, path), current);
          }
        }
        assert.deepEqual(
          alternatives.map((t) => t.exit),
          fork === 0 ? [0, 1] : [1, 0],
        );
        await writeFile(join(dir, path), bodies[fork]!);
        const after = await run(dir, path, signal);
        assert.equal(after.exit, 0);
        const ep = {
          family: p.name,
          turn,
          fork,
          goal,
          path,
          files,
          prefix: [...prefix],
          before,
          alternatives,
          after,
        };
        episodes.push(ep);
        if (fork === 0) next = ep;
      }
      assert(next);
      current = next.after.text;
      prefix.splice(
        0,
        prefix.length,
        ...history(next),
        { action: { op: "write", path, text: current }, observed: "written" },
        { action: { op: "test" }, observed: observation(next.after) },
      );
    }
  }
  for (const [name, rows] of [
    ["oracle", episodes],
    ["projects", episodes.flatMap(derive)],
  ] as const)
    await writeFile(
      join(out, name + ".jsonl.gz"),
      gzipSync(rows.map((r) => JSON.stringify(r)).join("\n") + "\n"),
      { flag: "wx" },
    );
}
if (import.meta.main) {
  const out = process.argv[2];
  if (!out) throw Error("Pass a fresh output directory");
  await mkdir(out);
  const controller = new AbortController();
  process.once("SIGINT", () => controller.abort());
  process.once("SIGTERM", () => controller.abort());
  await Effect.runPromise(
    Effect.acquireUseRelease(
      Effect.tryPromise(() => mkdtemp(join(tmpdir(), "cwm-c2-"))),
      (dir) => Effect.tryPromise((signal) => collect(dir, out, signal)),
      (dir) => Effect.promise(() => rm(dir, { recursive: true, force: true })),
    ),
    { signal: controller.signal },
  );
}
