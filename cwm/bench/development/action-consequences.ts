/** Cross the read boundary with the same two proposed edits on every held project. */
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { endpoint, ProjectSession, type Generate } from "../../project/agent.ts";
import { type Action } from "../../project/protocol.ts";
import { held } from "./held.ts";

export async function evaluate(generate: Generate) {
  const rows = [];
  for (const project of held) {
    for (const [alternative, replacement] of project.alternatives.entries()) {
      for (const read of [false, true]) {
        const session = new ProjectSession(
          { files: new Map(Object.entries(project.files)) },
          generate,
        );
        await session.begin(project.turns[0]!.goal);
        for (const path of session.state().files) {
          if (read || path !== replacement.path) await session.act({ op: "read", path });
        }
        const action: Action = { op: "write", ...replacement };
        const before = session.state();
        const forecast = await session.predict(action);
        const write = await session.act(action);
        // Test after an accepted write. This distinct query has access to the actual write
        // acknowledgment and never to the subsequent test result.
        const test = { op: "test" } as const;
        const after = session.state();
        const next = write.observed === "written" ? await session.predict(test) : null;
        const actual = next ? await session.act(test) : null;
        const expected = actual ? (actual.run!.exit === 0 ? "pass" : "fail") : "rejected";
        const key = { id: project.id, alternative, read };
        rows.push({ ...key, before, action, forecast, write, actual, expected });
        if (next)
          rows.push({ ...key, before: after, action: test, forecast: next, actual, expected });
      }
    }
  }
  return rows;
}

if (import.meta.main) {
  const [url, model, out] = process.argv.slice(2);
  if (!url || !model || !out || (await Bun.file(out).exists()))
    throw Error("Pass URL MODEL FRESH.json.gz");
  const rows = await evaluate(endpoint(url, model));
  await writeFile(out, gzipSync(JSON.stringify({ model, rows }) + "\n"), { flag: "wx" });
}
