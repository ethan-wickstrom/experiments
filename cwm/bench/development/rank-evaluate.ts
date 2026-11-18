/** Freeze all decisions before executing any candidate. Arithmetic on pairs is post hoc. */
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import { rankPairs, type Pair } from "../../project/plan.ts";
import { runTests } from "../../project/sandbox.ts";
import { queries } from "./reversals.ts";
import { held } from "./held.ts";

function pairs() {
  const entries: { id: string; input: Pair }[] = [];
  const examples = queries();
  for (let i = 0; i < examples.length; i += 2) {
    const a = examples[i]!,
      b = examples[i + 1]!;
    entries.push({
      id: a.name + "-" + a.spec,
      input: {
        goal: a.goal,
        path: a.action.path,
        files: [...a.files].map(([path, text]) => ({ path, text })),
        candidates: [a.action, b.action],
      },
    });
  }
  for (const p of held) {
    const [a, b] = p.alternatives;
    assert(a && b && a.path === b.path);
    entries.push({
      id: p.id,
      input: {
        goal: p.turns[0]!.goal,
        path: a.path,
        files: Object.entries(p.files).map(([path, text]) => ({ path, text })),
        candidates: [
          { op: "write", ...a },
          { op: "write", ...b },
        ],
      },
    });
  }
  return entries;
}

if (import.meta.main) {
  const [arm, out] = process.argv.slice(2);
  if (!arm || !out || (await Bun.file(out).exists())) throw Error("Pass ARM FRESH.json.gz");
  const entries = pairs();
  const inputs = entries.flatMap(({ input }) => [
    input,
    { ...input, candidates: [input.candidates[1], input.candidates[0]] as Pair["candidates"] },
  ]);
  const start = performance.now();
  const scores = await rankPairs(inputs, arm);
  const elapsedMs = Math.round(performance.now() - start);
  const rows = [];
  for (const [i, { id, input }] of entries.entries()) {
    const score = scores[2 * i]!,
      swapped = scores[2 * i + 1]!;
    const actual = [];
    for (const candidate of input.candidates) {
      const files = new Map(input.files.map((f) => [f.path, f.text])).set(
        candidate.path,
        candidate.text,
      );
      const run = await Effect.runPromise(runTests(files));
      actual.push(run);
    }
    assert.equal(actual.filter((r) => r.exit === 0).length, 1);
    const choice = "choice" in score ? score.choice : null;
    const consistent = choice !== null && "choice" in swapped && swapped.choice === 1 - choice;
    rows.push({
      id,
      input,
      score,
      swapped,
      actual,
      consistent,
      selectedPass: consistent && choice !== null ? actual[choice]!.exit === 0 : null,
    });
  }
  await writeFile(out, gzipSync(JSON.stringify({ arm, elapsedMs, rows }) + "\n"), { flag: "wx" });
}
