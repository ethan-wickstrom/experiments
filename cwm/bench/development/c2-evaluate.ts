/** Frozen two-turn, cumulatively graded project benchmark for the production workFile interface. */
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import { ProjectSession, endpoint } from "../../project/agent.ts";
import { runTests, type ToolRun } from "../../project/sandbox.ts";
import { workFile } from "../../project/work.ts";
import { c2Held } from "./c2-held.ts";

function passed(run: ToolRun) {
  return run.exit === 0 && /^\s*[1-9]\d* pass$/m.test(run.stderr);
}

async function evaluate(url: string, model: string, sourceOnly: boolean) {
  const runs = [];
  const generate = endpoint(url, model);
  for (const p of c2Held) {
    const files = new Map(Object.entries(p.files));
    const session = new ProjectSession({ files }, generate);
    const turns = [];
    for (const [i, { goal }] of p.turns.entries()) {
      const start = performance.now();
      const result = await workFile(session, p.path, goal, { sourceOnly });
      const elapsedMs = Math.round(performance.now() - start);
      const visible = await Effect.runPromise(runTests(files));
      const hidden = [];
      for (const [n, { accept }] of p.turns.slice(0, i + 1).entries()) {
        const snapshot = new Map(files);
        const path = "independent-" + n + ".test.ts";
        snapshot.set(path, accept);
        const run = await Effect.runPromise(runTests(snapshot, path));
        hidden.push({ pass: passed(run), run });
      }
      turns.push({
        goal,
        ...result,
        elapsedMs,
        visible,
        visiblePass: passed(visible),
        hidden,
        pass: hidden.every((h) => h.pass),
        files: Object.fromEntries(files),
        history: [...session.history],
      });
    }
    runs.push({ id: p.id, turns });
  }
  return runs;
}

if (import.meta.main) {
  const [url, model, arm, mode, out] = process.argv.slice(2);
  if (
    !url ||
    !model ||
    !["A", "B2", "C2"].includes(arm ?? "") ||
    (mode !== "policy" && mode !== "source") ||
    !out
  )
    throw Error("Usage: bun c2-evaluate.ts ENDPOINT MODEL A|B2|C2 policy|source FRESH.json.gz");
  if (await Bun.file(out).exists()) throw Error("Output exists");
  const runs = await evaluate(url, model, mode === "source");
  await writeFile(out, gzipSync(JSON.stringify({ arm, mode, model, runs }, null, 2) + "\n"), {
    flag: "wx",
  });
  console.log(
    arm,
    mode,
    runs.map(({ id, turns }) => [id, turns.map((t) => ({ stop: t.stop, pass: t.pass }))]),
  );
}
