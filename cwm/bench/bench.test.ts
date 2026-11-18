import { test, expect } from "bun:test";
import { rejects } from "node:assert/strict";
import { mkdtemp, readdir, rm, copyFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { trace, transitions, type Program } from "../cwm.ts";
import { cases } from "./cases.ts";
import { cache, collect } from "./collect.ts";
import { fitSites } from "./sites.ts";

test("the split holds out inputs and whole sources, without duplicating programs", () => {
  const manifest = [...cases()];
  expect(new Set(manifest.map((c) => JSON.stringify(c.program))).size).toBe(1024);
  const source = (p: Program) => p.files[p.entry]!;
  const training = new Set(
    manifest.filter((c) => c.split === "train").map((c) => source(c.program)),
  );
  expect(training.size).toBe(24);
  const novel = new Set<string>();
  for (const c of manifest) {
    if (c.split === "new-source") novel.add(source(c.program));
    else if (!training.has(source(c.program)))
      throw new Error("Missing training family: " + c.family);
  }
  expect(novel.size).toBe(8);
  expect(novel.isDisjointFrom(training)).toBe(true);
});

test("resume validates the shard identity and never trains on failed attempts", async () => {
  const root = await mkdtemp(join(tmpdir(), "cwm-batch-"));
  try {
    const p = [...cases()][0]!.program;
    const bad = { ...p, fn: "doesNotExist" };
    const path = await cache(root);
    expect(await collect(root, 2, [p, bad])).toEqual({ collected: 1, reused: 0, failed: 1 });
    expect(await collect(root, 1, [p])).toEqual({ collected: 0, reused: 1, failed: 0 });
    expect(await Bun.file(path(bad)).exists()).toBe(false);
    expect((await readdir(dirname(path(bad)))).filter((n) => n.endsWith(".error"))).toHaveLength(1);
    await copyFile(path(p), path(bad));
    await rejects(collect(root, 1, [bad]), /Unexpected trace/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("syntax anchors transfer a return across a renamed file and shifted UTF-16 columns", async () => {
  const program = (entry: string, prefix: string) => ({
    entry,
    files: { [entry]: `export function run(x:number){\r\n${prefix}return x;\r\n}` },
    fn: "run",
    args: [7],
  });
  const train = await trace(program("original.ts", ""));
  const test = await trace(program("renamed.ts", " /* 🎲 */ "));
  const entry = [...transitions(test)].find(
    ([f, next]) => f.kind === "step" && next.kind === "return",
  )!;
  const [frame, truth] = entry;
  expect(fitSites("source", [train])(test, frame)).toBeUndefined();
  expect(fitSites("syntax", [train])(test, frame)).toBeUndefined();
  expect(fitSites("syntax+operands", [train])(test, frame)).toEqual(truth);
});
