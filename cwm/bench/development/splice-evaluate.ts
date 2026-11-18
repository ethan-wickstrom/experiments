/** The editor finishes selection and persistence before the grader sees its candidate workspaces. */
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { endpoint, ProjectSession, type Generate } from "../../project/agent.ts";
import { spliceFile, visiblePass } from "../../project/splice.ts";
import { testPath } from "../../project/workspace.ts";
import { acceptance } from "./projects-evaluate.ts";

type Fixture = {
  id: string;
  files: Record<string, string>;
  turns: { path: string; goal: string; visible: Record<string, string>; accept: string }[];
};
export async function evaluateSplices(project: Fixture, generate: Generate, feedback: boolean) {
  const files = new Map(Object.entries(project.files));
  const session = new ProjectSession({ files }, generate);
  const checks: string[] = [];
  const turns = [];
  for (const turn of project.turns) {
    for (const [name, tests] of Object.entries(turn.visible)) {
      if (!testPath(name) || name === turn.path)
        throw Error("Expected a user-supplied visible test");
      files.set(name, tests);
    }
    if ([...files.keys()].some((p) => /^independent-\d+\.test\.ts$/.test(p)))
      throw Error("Grading path collision");
    const before = new Map(files);
    const start = performance.now();
    const result = await spliceFile(session, turn.path, turn.goal, { feedback });
    const elapsedMs = Math.round(performance.now() - start);
    checks.push(turn.accept);
    const visible = await session.test(files);
    const hidden = await acceptance(files, checks);
    const pass = visiblePass(visible) && hidden.every((h) => h.pass);
    // Each candidate carries the complete spliced target, including its provisional parent if present.
    const current = files.get(turn.path)!;
    const graded = new Map([[current, hidden]]);
    const candidates = [];
    for (const t of result.trials) {
      if (t.text === undefined) {
        candidates.push({ index: t.index, hidden: null, pass: false });
        continue;
      }
      let grades = graded.get(t.text);
      if (!grades) {
        grades = await acceptance(new Map(before).set(turn.path, t.text), checks);
        graded.set(t.text, grades);
      }
      candidates.push({
        index: t.index,
        hidden: grades,
        pass: !!t.run && visiblePass(t.run) && grades.every((h) => h.pass),
      });
    }
    turns.push({
      path: turn.path,
      goal: turn.goal,
      before: Object.fromEntries(before),
      ...result,
      elapsedMs,
      candidates,
      after: Object.fromEntries(files),
      visible,
      hidden,
      pass,
    });
    console.log(
      project.id,
      turns.length,
      result.stop,
      "selected",
      result.selected,
      "pass",
      pass,
      "candidates",
      candidates.map((c) => c.pass),
    );
  }
  return { id: project.id, turns };
}

if (import.meta.main) {
  const [url, model, mode, out] = process.argv.slice(2);
  if (
    !url ||
    !model ||
    (mode !== "feedback" && mode !== "no-feedback") ||
    !out ||
    (await Bun.file(out).exists())
  )
    throw Error("Pass ENDPOINT MODEL feedback|no-feedback FRESH.json.gz");
  const fixtures: { spliceHeld: Fixture[] } = await import(
    new URL("./splice-held.ts", import.meta.url).href
  );
  const generate = endpoint(url, model);
  const runs = [];
  for (const project of fixtures.spliceHeld)
    runs.push(await evaluateSplices(project, generate, mode === "feedback"));
  await writeFile(out, gzipSync(JSON.stringify({ model, mode, runs }) + "\n"), { flag: "wx" });
}
