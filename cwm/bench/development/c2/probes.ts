/** Local diagnostic projects authored here, independent of the live suite. */
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import projects from "./probe-projects.json";
import { collect } from "./collect.ts";
import { trace } from "../../../cwm.ts";

const out = process.argv[2];
if (!out) throw Error("Pass fresh directory");
await mkdir(out);
await Effect.runPromise(
  Effect.acquireUseRelease(
    Effect.tryPromise(() => mkdtemp(join(tmpdir(), "cwm-local-probe-"))),
    (dir) => Effect.tryPromise((signal) => collect(dir, out, signal, projects)),
    (dir) => Effect.promise(() => rm(dir, { recursive: true, force: true })),
  ),
);
const runs = [];
for (const body of [
  "y = y + 2;\nreturn x * y;",
  "if (y < x) {\nx = x - 2;\n} else {\ny = x + y;\n}\nreturn y;",
])
  for (const args of [
    [1, 3],
    [4, 2],
  ]) {
    const entry = "sample.ts",
      files = { [entry]: `export function run(x:number, y:number) {\n${body}\n}` };
    const program = { entry, files, args, fn: "run" };
    runs.push({ ...program, ...(await trace(program)) });
  }
await writeFile(
  join(out, "pauses.jsonl.gz"),
  gzipSync(runs.map((r) => JSON.stringify(r)).join("\n") + "\n"),
  { flag: "wx" },
);
