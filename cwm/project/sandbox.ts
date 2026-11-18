import { randomUUID } from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Effect } from "effect";
import { sourcePath } from "./workspace.ts";

const exec = promisify(execFile);
const image = "cwm-bun-project:1.4.4";
// The host sends only source bytes. No host paths, environment or Docker socket are mounted.
const stage = `import {mkdir,writeFile,symlink} from "node:fs/promises";
import {dirname} from "node:path";
await mkdir("/tmp/project",{recursive:true});process.chdir("/tmp/project");
for(const [name,text] of JSON.parse(await Bun.stdin.text())){
  await mkdir(dirname(name),{recursive:true});await writeFile(name,text,{flag:"wx"});
}
await symlink("/opt/cwm/node_modules","node_modules");`;

export type ToolRun = { exit: number; stdout: string; stderr: string };
export function runTests(files: ReadonlyMap<string, string>, only?: string) {
  const entries = [...files];
  if (entries.some(([p]) => !sourcePath(p)) || (only && !files.has(only)))
    throw Error("Invalid test snapshot");
  const name = "cwm-test-" + randomUUID();
  const command =
    stage +
    "const run=Bun.spawn({cmd:" +
    JSON.stringify(["bun", "test", ...(only ? ["./" + only] : [])]) +
    `,stdout:"inherit",stderr:"inherit"});
let timedOut=false;
const deadline=setTimeout(()=>{timedOut=true;run.kill("SIGKILL")},15000);
const exit=await run.exited;clearTimeout(deadline);
if(timedOut)console.error("Bun test exceeded the 15-second execution limit");
process.exit(timedOut?124:exit);`;
  return Effect.acquireUseRelease(
    Effect.succeed(name),
    () =>
      Effect.tryPromise({
        try: (signal) =>
          new Promise<ToolRun>((resolve, reject) => {
            const proc = execFile(
              "docker",
              [
                "run",
                "--rm",
                "--pull=never",
                "--name",
                name,
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--user=65534:65534",
                "--pids-limit=64",
                "--memory=512m",
                "--cpus=1",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=48m,mode=1777",
                "-i",
                image,
                "bun",
                "--eval",
                command,
              ],
              { signal, timeout: 25000, killSignal: "SIGKILL", maxBuffer: 262144 },
              (error, stdout, stderr) => {
                const code = error?.code ?? 0;
                if (error?.killed || typeof code !== "number" || code >= 125)
                  return reject(error ?? Error("Container failed"));
                resolve({ exit: code, stdout, stderr });
              },
            );
            proc.stdin?.on("error", () => {}); // execFile reports startup and cancellation failures.
            proc.stdin?.end(JSON.stringify(entries));
          }),
        catch: (error) => new Error("Bun test environment unavailable: " + String(error)),
      }),
    () =>
      Effect.promise(async () => {
        // A killed Docker client can leave its container running.
        try {
          await exec("docker", ["rm", "-f", name], { timeout: 5000 });
        } catch (error) {
          if (!String((error as { stderr?: string }).stderr).includes("No such container"))
            throw error;
        }
      }),
  );
}
export function testObservation(run: ToolRun) {
  if (run.exit === 0) return "pass";
  const lines = (run.stdout + "\n" + run.stderr).split("\n");
  const diagnostic = lines.filter((s) => /^(Expected|Received):/.test(s)).join("\n");
  const failure = lines.find((s) => s.includes("(fail)"))?.replace(/ \[[\d.]+m?s\]$/, "");
  return "fail\n" + (diagnostic || failure || run.stderr.trim() || run.stdout.trim()).slice(0, 240);
}
