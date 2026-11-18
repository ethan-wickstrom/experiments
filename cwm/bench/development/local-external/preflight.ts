import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import projects from "./projects.json";
import { grade, reference, syntax } from "./checks.ts";

const [out] = process.argv.slice(2);
if (!out || (await Bun.file(out).exists())) throw Error("Usage: bun preflight.ts FRESH.json.gz");
const evidence = [];
for (const p of projects) {
  const files = new Map(Object.entries(p.files) as [string, string][]);
  const checks: string[] = [];
  for (const [i, turn] of p.turns.entries()) {
    files.set("visible-" + (i + 1) + ".test.ts", turn.visible);
    checks.push(turn.hidden);
    const before = files.get(p.path)!;
    const ref = reference(before, turn);
    assert.deepEqual(syntax(p.path, before), []);
    assert.deepEqual(syntax(p.path, ref.text), []);
    const predecessor = await grade(files, checks);
    assert.equal(predecessor.visible.exit, 1);
    assert.match(predecessor.visible.stderr, /\(fail\)/);
    assert.ok(predecessor.hidden.slice(0, -1).every((h) => h.pass));
    assert.equal(predecessor.hidden.at(-1)!.run.exit, 1);
    assert.match(predecessor.hidden.at(-1)!.run.stderr, /\(fail\)/);
    files.set(p.path, ref.text);
    const fixed = await grade(files, checks);
    assert.ok(fixed.visiblePass && fixed.hiddenPass);
    evidence.push({ id: p.id, turn: i + 1, before, reference: ref, predecessor, fixed });
    console.log(p.id, i + 1, "verified");
  }
}
await writeFile(out, gzipSync(JSON.stringify(evidence) + "\n"), { flag: "wx" });
