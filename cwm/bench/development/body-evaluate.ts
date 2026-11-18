/** Collect one complete original two-turn lineage. No alternative edits enter the runtime. */
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { ProjectSession } from "../../project/agent.ts";
import { bodyEndpoint } from "../../project/body-completion.ts";
import { editBody } from "../../project/body.ts";
import { held } from "./held.ts";
import { acceptance } from "./projects-evaluate.ts";

const [url, model, arm, id, directory] = process.argv.slice(2);
const project = held.find((p) => p.id === id);
if (!url || !model || !arm || !["A", "B2", "C2"].includes(arm) || !project || !directory)
  throw Error("Usage: bun body-evaluate.ts LLAMA_ORIGIN MODEL A|B2|C2 ORIGINAL_PROJECT FRESH_DIR");
const run = join(directory, arm + "-" + project.id);
await mkdir(directory, { recursive: true });
await mkdir(run); // Never replace a partial or completed collection.
const files = new Map(Object.entries(project.files));
const paths = [...files.keys()].filter((p) => p.endsWith(".ts") && !p.endsWith(".test.ts"));
if (paths.length !== 1) throw Error("Expected a single implementation file");
const path = paths[0]!;
const endpoint = bodyEndpoint(url, model);
const session = new ProjectSession({ files }, async () => {
  throw Error("Unexpected chat query");
});
const checks: string[] = [];
for (const [index, turn] of project.turns.entries()) {
  const start = performance.now();
  const number = index + 1;
  const result = await editBody(session, endpoint, path, turn.goal);
  const elapsedMs = Math.round(performance.now() - start);
  const gradeStart = performance.now();
  const finalVisible = await session.test(files);
  checks.push(turn.accept);
  const hidden = await acceptance(files, checks);
  const visiblePass = finalVisible.exit === 0 && /^\s*[1-9]\d* pass$/m.test(finalVisible.stderr);
  const hiddenPass = hidden.every((g) => g.pass);
  const solved =
    result.stop === "tested" &&
    result.writes.some((w) => w.observed === "written" && w.before !== w.after) &&
    visiblePass &&
    hiddenPass;
  const forecastFailures = result.writes.flatMap((w) => w.forecastFailure ?? []);
  const cost = {
    completedModelCalls: result.calls.length,
    failedForecastAttempts: forecastFailures.length,
    completedInputTokens: result.calls.reduce((n, c) => n + c.reply.inputTokens, 0),
    completedOutputTokens: result.calls.reduce((n, c) => n + c.reply.tokens, 0),
    modelAttemptMs: [...result.calls, ...forecastFailures].reduce((n, c) => n + c.elapsedMs, 0),
    elapsedMs,
    gradingMs: Math.round(performance.now() - gradeStart),
  };
  const record = {
    arm,
    model,
    id,
    path,
    number,
    goal: turn.goal,
    ...result,
    finalVisible,
    visiblePass,
    hidden,
    hiddenPass,
    solved,
    cost,
    files: Object.fromEntries(files),
    history: session.history,
  };
  const output = join(run, "turn-" + number + ".json.gz");
  await writeFile(output, gzipSync(JSON.stringify(record) + "\n"), { flag: "wx" });
  console.log(
    JSON.stringify({
      arm,
      id,
      number,
      selected: result.selected,
      stop: result.stop,
      visiblePass,
      hiddenPass,
      solved,
      cost,
    }),
  );
}
