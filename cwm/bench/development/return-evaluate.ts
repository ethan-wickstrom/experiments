import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { endpoint, ProjectSession, type Generate } from "../../project/agent.ts";
import { editReturn } from "../../project/return.ts";
import { returnHeld } from "./return-held.ts";
import { acceptance } from "./projects-evaluate.ts";

export async function evaluateReturns(generate: Generate) {
  const projects = [];
  for (const project of returnHeld) {
    const files = new Map([[project.path, project.source]]);
    const session = new ProjectSession({ files }, generate);
    const checks: string[] = [];
    const turns = [];
    for (const [index, turn] of project.turns.entries()) {
      files.set("visible-" + index + ".test.ts", turn.visible);
      const before = files.get(project.path)!;
      const result = await editReturn(session, project.path, project.name, turn.request);
      const visible = result.events[0]?.run ?? (await session.act({ op: "test" })).run!;
      checks.push(turn.hidden);
      const grades = await acceptance(files, checks);
      const hiddenPass = grades.every((g) => g.pass);
      turns.push({
        request: turn.request,
        before,
        after: files.get(project.path)!,
        ...result,
        visible,
        grades,
        hiddenPass,
        solved: result.stop === "tested" && hiddenPass,
      });
    }
    projects.push({ id: project.id, turns });
  }
  return projects;
}

if (import.meta.main) {
  const [url, model, out] = process.argv.slice(2);
  if (!url || !model || !out || (await Bun.file(out).exists()))
    throw Error("Usage: bun return-evaluate.ts CHAT_ENDPOINT MODEL FRESH.json.gz");
  const projects = await evaluateReturns(endpoint(url, model));
  await writeFile(out, gzipSync(JSON.stringify({ model, maxTokens: 96, projects }) + "\n"), {
    flag: "wx",
  });
}
