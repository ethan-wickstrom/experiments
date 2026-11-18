import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { ProjectSession, endpoint } from "../../project/agent.ts";
import { planFile } from "../../project/plan.ts";
import { completeSource } from "../../project/work.ts";
import { acceptance } from "./projects-evaluate.ts";
import { held } from "./held.ts";

const [url, model, out] = process.argv.slice(2);
if (!url || !model || !out || (await Bun.file(out).exists()))
  throw Error("Pass C2 endpoint, model, fresh output");
const projects = [];
for (const project of held) {
  const path = project.alternatives[0]!.path;
  const files = new Map(Object.entries(project.files));
  const session = new ProjectSession({ files }, endpoint(url, model), undefined, "c2");
  const turns = [];
  const checks: string[] = [];
  for (const { goal, accept } of project.turns) {
    const before = new Map(files);
    const start = performance.now();
    const turn = await planFile(session, path, goal);
    const elapsedMs = Math.round(performance.now() - start);
    checks.push(accept);
    const grades = await acceptance(files, checks);
    // Independent post-turn grading on snapshots cannot affect the real follow-up workspace.
    const proposals = [];
    for (const { reply } of turn.events) {
      const valid = reply.finish === "stop" && completeSource(path, reply.text);
      const grades = valid ? await acceptance(new Map(before).set(path, reply.text), checks) : null;
      proposals.push({ valid, grades, pass: grades?.every((g) => g.pass) ?? null });
    }
    turns.push({
      goal,
      path,
      ...turn,
      elapsedMs,
      proposals,
      grades,
      pass: grades.every((g) => g.pass),
      files: Object.fromEntries(files),
    });
    console.log(project.id, turn.stop, turns.at(-1)!.pass);
  }
  projects.push({ id: project.id, turns });
}
await writeFile(out, gzipSync(JSON.stringify({ model, projects }) + "\n"), { flag: "wx" });
