import { createHash, randomUUID } from "node:crypto";
import { mkdir, rename, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { readTraces, trace, type Program } from "../cwm.ts";
import { isDeepStrictEqual } from "node:util";
import { cases } from "./cases.ts";

const hash = (s: string) => createHash("sha256").update(s).digest("hex");
export async function cache(root: string) {
  const node = Bun.spawnSync(["node", "-v"]);
  if (!node.success) throw new Error("Node is required on PATH");
  const version = hash(
    JSON.stringify([
      Bun.version,
      node.stdout.toString().trim(),
      process.platform,
      process.arch,
      await Bun.file(new URL("../cwm.ts", import.meta.url)).text(),
      await Bun.file(new URL("../bun.lock", import.meta.url)).text(),
    ]),
  );
  const dir = join(root, version);
  await mkdir(dir, { recursive: true });
  return (program: Program) => join(dir, hash(JSON.stringify(program)) + ".jsonl");
}

async function publish(path: string, data: unknown) {
  const tmp = path + "." + randomUUID() + ".tmp";
  try {
    await writeFile(tmp, JSON.stringify(data) + "\n");
    await rename(tmp, path);
  } finally {
    await rm(tmp, { force: true });
  }
}

export async function load(path: string, program: Program) {
  const rows = await Array.fromAsync(readTraces(path));
  const row = rows[0];
  if (rows.length !== 1 || !row) throw new Error("Expected one trace: " + path);
  const { frames, outcome: _outcome, ...input } = row;
  if (!isDeepStrictEqual(input, program) || !frames.length)
    throw new Error("Unexpected trace: " + path);
  return row;
}

export async function collect(root: string, jobs: number, inputs: Iterable<Program>) {
  if (!Number.isSafeInteger(jobs) || jobs < 1 || jobs > 32) throw new Error("jobs must be 1..32");
  const pathFor = await cache(root);
  const queue = inputs[Symbol.iterator]();
  let stopped = false;
  let collected = 0,
    reused = 0,
    failed = 0;
  async function worker() {
    while (!stopped) {
      const item = queue.next();
      if (item.done) return;
      const program = item.value,
        path = pathFor(program);
      if (await Bun.file(path).exists()) {
        await load(path, program);
        reused++;
        continue;
      }
      let run;
      try {
        run = await trace(program);
      } catch (error) {
        await publish(path + "." + randomUUID() + ".error", { program, error: String(error) });
        failed++;
        continue;
      }
      await publish(path, run);
      collected++;
    }
  }
  const workers = Array.from({ length: jobs }, worker);
  try {
    await Promise.all(workers);
  } catch (error) {
    stopped = true;
    await Promise.allSettled(workers);
    throw error;
  }
  return { collected, reused, failed };
}

if (import.meta.main) {
  const [root, jobs = "4"] = process.argv.slice(2);
  if (!root) throw new Error("Usage: bun bench/collect.ts CACHE [JOBS]");
  const result = await collect(
    root,
    Number(jobs),
    Array.from(cases(), (c) => c.program),
  );
  console.log(JSON.stringify(result));
  if (result.failed) process.exitCode = 1;
}
