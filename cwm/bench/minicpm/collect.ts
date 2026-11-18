import { writeFile } from "node:fs/promises";
import { trace } from "../../cwm.ts";

if (!process.argv[2]) throw Error("Pass a fresh held-out JSONL output path");
const bodies = [
  "x = x + y;\nreturn x - y;",
  "if (y > x) {\ny = y - 1;\n}\nreturn y;",
  "while (y > 1) {\ny = y - 1;\n}\nreturn x + y;",
  "y = x * y;\nx = y - x;\nreturn y;",
];
const rows = [];
for (const body of bodies) {
  for (const args of [
    [2, 3],
    [4, 2],
    [3, 1],
  ]) {
    const entry = "unit.ts";
    const files = { [entry]: `export function run(x:number, y:number) {\n${body}\n}` };
    const program = { entry, files, args, fn: "run" };
    rows.push(JSON.stringify({ ...program, ...(await trace(program)) }));
  }
}
await writeFile(process.argv[2], rows.join("\n") + "\n", { flag: "wx" });
