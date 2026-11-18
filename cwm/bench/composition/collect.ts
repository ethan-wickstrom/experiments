import { writeFile } from "node:fs/promises";
import { trace } from "../../cwm.ts";
import { manifest } from "./manifest.ts";

if (import.meta.main) {
  const out = process.argv[2];
  if (!out) throw new Error("Usage: bun collect.ts FRESH-OUTPUT.jsonl");
  const node = Bun.spawnSync(["node", "--version"]).stdout.toString().trim();
  if (Bun.version !== "1.4.4" || node !== "v24.19.0")
    throw new Error("Recollect with Bun 1.4.4 + Node 24.19.0");
  const lines: string[] = [];
  for (const { program } of manifest()) lines.push(JSON.stringify(await trace(program)));
  await writeFile(out, lines.join("\n") + "\n", { flag: "wx" });
}
