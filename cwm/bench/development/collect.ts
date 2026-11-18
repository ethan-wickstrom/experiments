/** Only run the six trusted authored fixtures. No model or user input executes here. */
import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import { projects } from "./cases.ts";
import { wire, type Action, type Event } from "../../project/protocol.ts";

type Check = { exit: number; stdout: string; stderr: string };
async function check(dir: string, signal: AbortSignal): Promise<Check> {
  const p = Bun.spawn([process.execPath, "test", "checks.test.ts"], {
    cwd: dir,
    signal,
    stdout: "pipe",
    stderr: "pipe",
    env: { ...process.env, NO_COLOR: "1", FORCE_COLOR: "0" },
  });
  const [exit, stdout, stderr] = await Promise.all([
    p.exited,
    new Response(p.stdout).text(),
    new Response(p.stderr).text(),
  ]);
  assert(
    exit === 0 || (exit === 1 && stderr.includes("(fail)")),
    "Bun test failed outside an assertion",
  );
  return { exit, stdout, stderr };
}
function observed(check: Check) {
  if (!check.exit) return "pass";
  const diagnostic = (check.stdout + "\n" + check.stderr)
    .split("\n")
    .filter((s) => /^(Expected|Received):/.test(s));
  const failure = check.stderr.split("\n").find((s) => s.includes("(fail)"));
  assert(failure);
  return "fail\n" + (diagnostic.join("\n") || failure.replace(/ \[[\d.]+m?s\]$/, "")).slice(0, 240);
}
type Project = (typeof projects)[number];
function fixture(p: Project, expr: string) {
  return `export function ${p.fn}(${p.signature}) {\n  return ${expr};\n}\n`;
}
function tests(p: Project, extended: boolean) {
  const assertions = [...p.checks, ...(extended ? p.extra : [])].map((pair) => {
    const i = pair.lastIndexOf("), ");
    assert(i >= 0);
    return "  expect(" + pair.slice(0, i + 1) + ").toEqual(" + pair.slice(i + 3) + ");";
  });
  return [
    'import {test, expect} from "bun:test";',
    `import {${p.fn} as f} from "./${p.name}";`,
    'test("library behavior", () => {',
    ...assertions,
    "});",
    "",
  ].join("\n");
}

async function collect(root: string, out: string, signal: AbortSignal) {
  const records: object[] = [],
    evidence: object[] = [];
  for (const [index, p] of projects.entries()) {
    const dir = join(root, p.name);
    await mkdir(dir);
    const source = p.name + ".ts",
      checks = "checks.test.ts",
      files = [source, checks].sort();
    const history: Event[] = [];
    const raw = (record: object) => evidence.push({ family: p.name, ...record });
    const write = (text: string): Action => ({ op: "write", path: source, text });
    const initial = fixture(p, p.initial);
    await writeFile(join(dir, source), initial);
    raw({ type: "initial", files: { [source]: initial } });
    const policy = (action: Action, result?: string, oracle?: Check) => {
      records.push({
        family: p.name,
        task: "policy",
        prompt: wire(files, history),
        target: JSON.stringify(action),
      });
      raw({ type: "action", action, observed: result, oracle });
      if (result !== undefined) history.push({ action, observed: result });
    };
    const forecast = (candidate: Action, target: string, oracle?: Check) => {
      records.push({
        family: p.name,
        task: "forecast",
        prompt: wire(files, history, candidate),
        target,
      });
      raw({ type: "candidate", candidate, label: target, oracle });
    };
    const read = async (path: string) =>
      policy({ op: "read", path }, await readFile(join(dir, path), "utf8"));
    for (const phase of [0, 1]) {
      const testText = tests(p, Boolean(phase));
      await writeFile(join(dir, checks), testText);
      const user = phase ? p.follow : p.request;
      raw({ type: "request", user, supplied: { [checks]: testText } });
      history.push({ user });
      if (!phase) {
        const candidate = write(initial);
        // Replacing an existing unread file is rejected by the action contract.
        assert(
          !history.some((e) => "action" in e && e.action.op === "read" && e.action.path === source),
        );
        forecast(candidate, "rejected");
      }
      if ((index + phase) % 2 === 0) await read(checks);
      await read(source);
      const test = { op: "test" } as const;
      const before = await check(dir, signal);
      assert.equal(before.exit, 1);
      forecast(test, "fail", before);
      policy(test, observed(before), before);
      const saved = await readFile(join(dir, source), "utf8");
      const good = fixture(p, phase ? p.final : p.first);
      for (const text of [good, fixture(p, p.wrong), saved]) {
        await writeFile(join(dir, source), text);
        try {
          const oracle = await check(dir, signal);
          forecast(write(text), oracle.exit ? "fail" : "pass", oracle);
        } finally {
          await writeFile(join(dir, source), saved);
        }
      }
      await writeFile(join(dir, source), good);
      policy(write(good), "written");
      const after = await check(dir, signal);
      assert.equal(after.exit, 0);
      forecast(test, "pass", after);
      policy(test, observed(after), after);
      policy({ op: "done" });
    }
  }
  for (const [name, rows] of [
    ["projects", records],
    ["oracle", evidence],
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
  await Effect.runPromise(
    Effect.acquireUseRelease(
      Effect.tryPromise(() => mkdtemp(join(tmpdir(), "cwm-lib-"))),
      (dir) => Effect.tryPromise((signal) => collect(dir, out, signal)),
      (dir) => Effect.promise(() => rm(dir, { recursive: true, force: true })),
    ),
  );
}
