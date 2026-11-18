import { spawn } from "node:child_process";
import { once } from "node:events";
import { mkdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createInterface } from "node:readline";
import { gzipSync } from "node:zlib";
import { testObservation } from "../../../project/sandbox.ts";
import { grade, visible } from "./checks.ts";
import projects from "./projects.json";
import { validate } from "./reply.ts";

export type Transcript = {
  arm: string;
  project: string;
  turn: number;
  preEdit: Awaited<ReturnType<typeof visible>>;
  request: {
    goal: string;
    path: string;
    files: { path: string; text: string }[];
    observed: string;
  };
  raw: string;
  elapsedMs: number;
  result: ReturnType<typeof validate>;
  grades: Awaited<ReturnType<typeof grade>>;
  solved: boolean;
};

const [checkout, arm, output, releasedArm = arm] = process.argv.slice(2);
if (
  !checkout ||
  !output ||
  !arm ||
  !["base", "trained", "edit-only"].includes(arm) ||
  !process.env.CWM_MODEL_PATH
)
  throw Error(
    "Usage: CWM_MODEL_PATH=SNAPSHOT bun evaluate.ts EDITOR_CHECKOUT base|trained|edit-only FRESH_OUTPUT_DIR [CLI_ARM]",
  );
await mkdir(output);
const server = spawn(
  process.env.PYTHON || "python",
  ["cwm/bench/development/local_edit/edit.py", "--serve", "--arm", releasedArm!],
  {
    cwd: resolve(checkout),
    stdio: ["pipe", "pipe", "inherit"],
  },
);
const exit = once(server, "close");
const responses = createInterface({ input: server.stdout, crlfDelay: Infinity })[
  Symbol.asyncIterator
]();
try {
  for (const project of projects) {
    const files = new Map(Object.entries(project.files) as [string, string][]);
    const checks: string[] = [];
    for (const [i, turn] of project.turns.entries()) {
      files.set("visible-" + (i + 1) + ".test.ts", turn.visible);
      checks.push(turn.hidden);
      const preEdit = await visible(files);
      const request = {
        goal: turn.goal,
        path: project.path,
        files: [...files.keys()].sort().map((path) => ({ path, text: files.get(path)! })),
        observed: testObservation(preEdit),
      };
      const started = performance.now();
      server.stdin.write(JSON.stringify(request) + "\n");
      const line = await responses.next();
      if (line.done) throw Error("Editor exited before responding");
      const elapsedMs = Math.round(performance.now() - started);
      const raw = line.value;
      const before = files.get(project.path)!;
      const result = validate(raw, project.path, before);
      files.set(project.path, result.text);
      const grades = await grade(files, checks);
      const solved =
        result.accepted && result.text !== before && grades.visiblePass && grades.hiddenPass;
      const record: Transcript = {
        arm,
        project: project.id,
        turn: i + 1,
        preEdit,
        request,
        raw,
        elapsedMs,
        result,
        grades,
        solved,
      };
      await writeFile(
        join(output, project.id + "-" + (i + 1) + ".json.gz"),
        gzipSync(JSON.stringify(record) + "\n"),
        { flag: "wx" },
      );
      console.log(
        arm,
        project.id,
        i + 1,
        result.reason,
        grades.visiblePass,
        grades.hiddenPass,
        solved,
      );
    }
  }
  server.stdin.end();
  if (!(await responses.next()).done) throw Error("Unsolicited editor output");
  const [code] = await exit;
  if (code !== 0) throw Error("Nonzero editor exit " + String(code));
} finally {
  server.kill();
}
