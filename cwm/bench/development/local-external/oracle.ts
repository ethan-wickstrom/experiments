import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { gzipSync, gunzipSync } from "node:zlib";
import { testObservation, type ToolRun } from "../../../project/sandbox.ts";
import { grade, reference } from "./checks.ts";
import projects from "./projects.json";
import { validate } from "./reply.ts";

const [checkout, arm, out] = process.argv.slice(2);
if (!checkout || !out || !arm || !["trained", "edit-only"].includes(arm))
  throw Error("Usage: bun oracle.ts EDITOR_CHECKOUT trained|edit-only FRESH_OUTPUT_DIR");
const seal = await readFile(join(import.meta.dir, "preflight.json.gz"));
assert.equal(
  createHash("sha256").update(seal).digest("hex"),
  "fda0cb2f1968a899bf336a22d2093d83a1f04f6670dab603f5d54f2a9109f057",
);
type Canonical = {
  id: string;
  turn: number;
  before: string;
  reference: ReturnType<typeof reference>;
  predecessor: { visible: ToolRun };
};
const stored: Canonical[] = JSON.parse(gunzipSync(seal).toString());
const cases = [];
for (const project of projects) {
  const files = new Map(Object.entries(project.files) as [string, string][]);
  const checks: string[] = [];
  for (const [i, turn] of project.turns.entries()) {
    const canonical = stored.find((r) => r.id === project.id && r.turn === i + 1)!;
    assert.equal(canonical.before, files.get(project.path));
    const ref = reference(canonical.before, turn);
    assert.deepEqual(ref, canonical.reference);
    files.set("visible-" + (i + 1) + ".test.ts", turn.visible);
    const req = {
      goal: turn.goal,
      path: project.path,
      files: [...files.keys()].sort().map((path) => ({ path, text: files.get(path)! })),
      observed: testObservation(canonical.predecessor.visible),
    };
    checks.push(turn.hidden);
    cases.push({
      id: project.id,
      turn: i + 1,
      canonical,
      ref,
      checks: [...checks],
      input: { request: req, span: [ref.start, ref.end] },
    });
    files.set(project.path, ref.text);
  }
}
await mkdir(out);
const proc = Bun.spawn(
  [process.env.PYTHON || "python", join(import.meta.dir, "oracle-fill.py"), resolve(checkout), arm],
  {
    cwd: resolve(checkout),
    stdin: Buffer.from(cases.map((c) => JSON.stringify(c.input) + "\n").join("")),
    stdout: "pipe",
    stderr: "inherit",
  },
);
const [output, exit] = await Promise.all([new Response(proc.stdout).text(), proc.exited]);
assert.equal(exit, 0);
const replies = output.trimEnd().split("\n");
assert.equal(replies.length, cases.length);
const rows = [];
for (const [i, c] of cases.entries()) {
  const reply = JSON.parse(replies[i]!);
  const raw = JSON.stringify(reply.response);
  const req = c.input.request;
  const result = validate(raw, req.path, c.canonical.before);
  const files = new Map(req.files.map((f) => [f.path, f.text]));
  files.set(req.path, result.text);
  const grades = await grade(files, c.checks);
  const solved =
    result.accepted &&
    result.text !== c.canonical.before &&
    grades.visiblePass &&
    grades.hiddenPass;
  const transcript = c.id + "-" + c.turn + ".json.gz";
  const record = {
    arm,
    project: c.id,
    turn: c.turn,
    input: c.input,
    preEdit: c.canonical.predecessor.visible,
    prompt: reply.prompt,
    raw,
    elapsedMs: reply.elapsedMs,
    result,
    grades,
    solved,
  };
  const bytes = gzipSync(JSON.stringify(record) + "\n");
  await writeFile(join(out, transcript), bytes, { flag: "wx" });
  rows.push({
    arm,
    project: c.id,
    turn: c.turn,
    transcript,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    sourceSha256: createHash("sha256").update(c.canonical.before).digest("hex"),
    span: c.input.span,
    stopped: reply.response.stopped,
    accepted: result.accepted,
    changed: result.text !== c.canonical.before,
    reason: result.reason,
    exactReplacement: reply.response.stopped && reply.response.replacement === c.ref.replacement,
    visiblePass: grades.visiblePass,
    hidden: grades.hidden.map((h) => h.pass),
    hiddenPass: grades.hiddenPass,
    solved,
    elapsedMs: reply.elapsedMs,
  });
  console.log(arm, c.id, c.turn, result.reason, grades.visiblePass, grades.hiddenPass, solved);
}
await writeFile(join(out, "turns.jsonl"), rows.map((r) => JSON.stringify(r)).join("\n") + "\n", {
  flag: "wx",
});
