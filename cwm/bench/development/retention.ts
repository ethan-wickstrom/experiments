import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { trace } from "../../cwm.ts";

const bodies = [
  "y = x + y;\nx = y * x;\nreturn x;",
  "if (y === 0) {\nx = x - 1;\n} else {\ny = y + x;\n}\nreturn x + y;",
  "while (x > 1) {\ny = y + 2;\nx = x - 1;\n}\nreturn y;",
];
if (import.meta.main) {
  const out = process.argv[2];
  if (!out) throw Error("Pass a fresh retention tape path");
  const rows = [];
  for (const body of bodies) {
    for (const args of [
      [2, 0],
      [3, 1],
    ]) {
      const entry = "probe.ts",
        files = { [entry]: `export function run(x:number, y:number) {\n${body}\n}` };
      const program = { entry, files, args, fn: "run" };
      rows.push(JSON.stringify({ ...program, ...(await trace(program)) }));
    }
  }
  await writeFile(out, gzipSync(rows.join("\n") + "\n"), { flag: "wx" });
}
