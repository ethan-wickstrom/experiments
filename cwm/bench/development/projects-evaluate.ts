/** Execute independent acceptance checks only after the policy turn has stopped. */
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import { ProjectSession, endpoint, type Generate } from "../../project/agent.ts";
import { wire, type Action, type Event } from "../../project/protocol.ts";
import { runTests } from "../../project/sandbox.ts";
import { held } from "./held.ts";
import { directedHeld } from "./directed-held.ts";
import { editFile } from "../../project/directed.ts";
import { workFile } from "../../project/work.ts";

async function acceptance(files: Map<string, string>, tests: string[]) {
  const grades = [];
  for (const [i, source] of tests.entries()) {
    const copy = new Map(files);
    const path = "independent-" + i + ".test.ts";
    copy.set(path, source);
    const run = await Effect.runPromise(runTests(copy, path));
    grades.push({ pass: run.exit === 0 && /^\s*[1-9]\d* pass$/m.test(run.stderr), run });
  }
  return grades;
}

async function policy(
  project: (typeof held)[number] | (typeof directedHeld)[number],
  generate: Generate,
  mode: string,
) {
  const files = new Map(Object.entries(project.files));
  const session = new ProjectSession({ files }, generate);
  const turns = [];
  const checks: string[] = [];
  for (const { goal, accept } of project.turns) {
    checks.push(accept);
    const start = performance.now();
    const result =
      "path" in project
        ? await editFile(session, project.path, goal)
        : mode === "work" || mode === "source"
          ? await workFile(session, project.alternatives[0]!.path, goal, {
              sourceOnly: mode === "source",
            })
          : await session.turn(goal);
    const elapsedMs = Math.round(performance.now() - start);
    const grades = await acceptance(files, checks);
    turns.push({
      goal,
      ...result,
      elapsedMs,
      grades,
      pass: grades.every((g) => g.pass),
      files: Object.fromEntries(files),
    });
    console.log(
      project.id,
      "turn",
      turns.length,
      result.stop,
      grades.map((g) => g.pass),
    );
  }
  return turns;
}

async function counterfactuals(project: (typeof held)[number], generate: Generate) {
  const names = Object.keys(project.files).sort();
  const goal = project.turns[0]!.goal;
  const history: Event[] = [
    { user: goal },
    ...names.map((path) => ({
      action: { op: "read" as const, path },
      observed: project.files[path]!,
    })),
  ];
  const rows: {
    candidate: Action;
    preferencePrompt: string;
    preference: Awaited<ReturnType<Generate>>;
    forecastPrompt: string;
    forecast: Awaited<ReturnType<Generate>>;
    observed: import("../../project/sandbox.ts").ToolRun;
    expected: string;
  }[] = [];
  for (const replacement of project.alternatives) {
    const candidate: Action = { op: "write", ...replacement };
    const forecastPrompt = wire(names, history, candidate);
    const state = forecastPrompt.slice(forecastPrompt.indexOf("\n") + 1);
    const preferencePrompt =
      "Would you apply this candidate to fulfill the user request? Reply with one word: yes or no.\n" +
      state;
    const preference = await generate(preferencePrompt, 8);
    const forecast = await generate(forecastPrompt, 8);
    const files = new Map(Object.entries(project.files));
    files.set(candidate.path, candidate.text);
    const observed = await Effect.runPromise(runTests(files));
    rows.push({
      candidate,
      preferencePrompt,
      preference,
      forecastPrompt,
      forecast,
      observed,
      expected: observed.exit === 0 ? "pass" : "fail",
    });
  }
  // A tie or out-of-domain answer leaves the pair unresolved.
  function selection(field: "preference" | "forecast", positive: string, negative: string) {
    if (
      rows.some((r) => r[field].finish !== "stop" || ![positive, negative].includes(r[field].text))
    )
      return null;
    const choices = rows.filter((r) => r[field].text === positive);
    return choices.length === 1 ? choices[0]!.expected === "pass" : null;
  }
  return {
    rows,
    forecastSelectedPass: selection("forecast", "pass", "fail"),
    preferenceSelectedPass: selection("preference", "yes", "no"),
  };
}
if (import.meta.main) {
  const [url, model, out, mode = "policy"] = process.argv.slice(2);
  if (!url || !model || !out)
    throw Error(
      "Usage: bun projects-evaluate.ts CHAT_ENDPOINT MODEL FRESH_SCORES.json.gz [directed|policy|work|source]",
    );
  if (!["directed", "policy", "work", "source"].includes(mode) || (await Bun.file(out).exists()))
    throw Error("Expected a valid mode and fresh output path");
  const generate = endpoint(url, model);
  const results = [];
  for (const project of mode === "directed" ? directedHeld : held) {
    results.push({
      id: project.id,
      turns: await policy(project, generate, mode),
      ...(mode === "policy" && "alternatives" in project
        ? { alternatives: await counterfactuals(project, generate) }
        : {}),
    });
  }
  await writeFile(out, gzipSync(JSON.stringify({ model, mode, results }) + "\n"), { flag: "wx" });
}
