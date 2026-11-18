/** Development-only problems for exercising the editor before the independent fixture reveal. */
import { gzipSync } from "node:zlib";
import { writeFile } from "node:fs/promises";
import { endpoint, ProjectSession } from "../../project/agent.ts";
import { spliceFile } from "../../project/splice.ts";

const problems = [
  {
    path: "freight.ts",
    goal: "Charge the unit rate for each parcel. The shipment total is the number of parcels multiplied by the unit rate.",
    source:
      "export function total(parcels: number, rate: number) {\n  const cost = parcels + rate;\n  return cost;\n}\n",
    check:
      'import {expect,test} from "bun:test"; import {total} from "./freight"; test("shipment total",()=>expect(total(3,4)).toBe(12));',
  },
  {
    path: "badge.ts",
    goal: "Print staff badge names in uppercase. Keep stripping surrounding spaces.",
    source:
      "export function badge(name: string) {\n  const label = name.trim().toLowerCase();\n  return label;\n}\n",
    check:
      'import {expect,test} from "bun:test"; import {badge} from "./badge"; test("staff badge",()=>expect(badge(" Ada ")).toBe("ADA"));',
  },
];

if (import.meta.main) {
  const [url, model, out] = process.argv.slice(2);
  if (!url || !model || !out || (await Bun.file(out).exists()))
    throw Error("Pass ENDPOINT MODEL FRESH.json.gz");
  const results = [];
  for (const p of problems) {
    const files = new Map([
      [p.path, p.source],
      ["visible.test.ts", p.check],
    ]);
    const result = await spliceFile(
      new ProjectSession({ files }, endpoint(url, model)),
      p.path,
      p.goal,
    );
    results.push({ ...p, ...result, final: files.get(p.path) });
    console.log(
      p.path,
      result.stop,
      result.trials.map((t) => [t.status, t.replacement, t.run?.exit]),
    );
  }
  await writeFile(out, gzipSync(JSON.stringify(results) + "\n"), { flag: "wx" });
}
