import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { gzipSync, gunzipSync } from "node:zlib";
import { testObservation } from "../../../project/sandbox.ts";
import { grade, passed, reference, splice, syntax } from "./checks.ts";
import type { Transcript } from "./evaluate.ts";
import projects from "./projects.json";
import { validate } from "./reply.ts";

const [results, output] = process.argv.slice(2);
if (!results || !output)
  throw Error("Usage: bun diagnose.ts RESULTS_WITH_THREE_ARMS FRESH_OUTPUT_DIR");
await mkdir(output);
const rows = [];
for (const arm of ["base", "trained", "edit-only"]) {
  for (const project of projects) {
    const files = new Map(Object.entries(project.files) as [string, string][]);
    let gold = files.get(project.path)!;
    const checks: string[] = [];
    for (const [i, turn] of project.turns.entries()) {
      checks.push(turn.hidden);
      files.set("visible-" + (i + 1) + ".test.ts", turn.visible);
      const path = arm + "/" + project.id + "-" + (i + 1) + ".json.gz";
      const bytes: Buffer = await readFile(join(results, path));
      const r: Transcript = JSON.parse(gunzipSync(bytes).toString());
      assert.equal(r.arm, arm);
      assert.equal(r.turn, i + 1);
      assert.equal(r.project, project.id);
      assert.equal(r.request.goal, turn.goal);
      assert.equal(r.request.path, project.path);
      assert.equal(r.request.observed, testObservation(r.preEdit));
      assert.deepEqual(
        r.request.files,
        [...files.keys()].sort().map((path) => ({ path, text: files.get(path)! })),
      );
      const before = files.get(project.path)!;
      const result = validate(r.raw, project.path, before);
      assert.deepEqual(result, r.result);
      assert.equal(r.grades.visiblePass, passed(r.grades.visible));
      assert.equal(r.grades.hidden.length, i + 1);
      for (const h of r.grades.hidden) assert.equal(h.pass, passed(h.run));
      assert.equal(
        r.grades.hiddenPass,
        r.grades.hidden.every((h) => h.pass),
      );
      assert.equal(
        r.solved,
        result.accepted && result.text !== before && r.grades.visiblePass && r.grades.hiddenPass,
      );
      const ref = reference(gold, turn);
      const matches = before === gold;
      const edit = result.edit;
      const eligible = matches && edit !== null;
      const reason = !matches
        ? "divergent predecessor"
        : edit
          ? "eligible"
          : result.span
            ? "span only"
            : "no usable edit";
      async function hybrid(start: number, end: number, replacement: string) {
        const text = splice(before, start, end, replacement);
        const errors = syntax(project.path, text);
        const snapshot = new Map(files);
        snapshot.set(project.path, text);
        const grades = errors.length ? null : await grade(snapshot, checks);
        return {
          start,
          end,
          replacement,
          text,
          errors,
          grades,
          pass: Boolean(grades?.visiblePass && grades.hiddenPass),
        };
      }
      const modelSpan =
        matches && result.span
          ? await hybrid(result.span[0], result.span[1], ref.replacement)
          : null;
      const modelReplacement = eligible ? await hybrid(ref.start, ref.end, edit.replacement) : null;
      const diagnostics = arm + "-" + project.id + "-" + (i + 1) + ".json.gz";
      await writeFile(
        join(output, diagnostics),
        gzipSync(
          JSON.stringify({
            arm,
            project: project.id,
            turn: i + 1,
            reason,
            before,
            gold,
            ref,
            modelSpan,
            modelReplacement,
          }) + "\n",
        ),
        { flag: "wx" },
      );
      rows.push({
        arm,
        project: project.id,
        turn: i + 1,
        path: project.path,
        goal: turn.goal,
        observed: r.request.observed,
        transcript: path,
        transcriptSha256: createHash("sha256").update(bytes).digest("hex"),
        beforeSha256: createHash("sha256").update(before).digest("hex"),
        requestSha256: createHash("sha256").update(JSON.stringify(r.request)).digest("hex"),
        elapsedMs: r.elapsedMs,
        edit,
        accepted: result.accepted,
        reason: result.reason,
        changed: result.text !== before,
        visiblePass: r.grades.visiblePass,
        hidden: r.grades.hidden.map((h: { pass: boolean }) => h.pass),
        hiddenPass: r.grades.hiddenPass,
        solved: r.solved,
        diagnostics,
        hybridEligibility: reason,
        samePredecessor: matches,
        span: result.span,
        exactSpan:
          matches && result.span
            ? result.span[0] === ref.start && result.span[1] === ref.end
            : null,
        exactReplacement: eligible ? edit.replacement === ref.replacement : null,
        modelSpanPass: modelSpan?.pass ?? null,
        modelReplacementPass: modelReplacement?.pass ?? null,
      });
      gold = ref.text;
      files.set(project.path, result.text);
    }
  }
}
await writeFile(join(output, "turns.jsonl"), rows.map((r) => JSON.stringify(r)).join("\n") + "\n", {
  flag: "wx",
});
