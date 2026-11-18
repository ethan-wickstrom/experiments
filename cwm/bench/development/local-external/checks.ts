import { Effect } from "effect";
import { parseSync } from "oxc-parser";
import { runTests, type ToolRun } from "../../../project/sandbox.ts";
import { acceptance } from "../projects-evaluate.ts";

export function passed(run: ToolRun) {
  return run.exit === 0 && /^\s*[1-9]\d* pass$/m.test(run.stderr);
}
export const visible = (files: ReadonlyMap<string, string>) => Effect.runPromise(runTests(files));
export async function grade(files: Map<string, string>, checks: string[]) {
  const run = await visible(files);
  const hidden = await acceptance(files, checks);
  return {
    visible: run,
    visiblePass: passed(run),
    hidden,
    hiddenPass: hidden.every((h) => h.pass),
  };
}
// Preserve line terminators and a final unterminated line; never append a phantom empty line.
export function lines(text: string) {
  return text.match(/[^\n]*\n|[^\n]+$/g) ?? [];
}
export function splice(source: string, start: number, end: number, replacement: string) {
  const old = lines(source);
  if (!legalSpan(start, end, old.length)) throw Error("Out-of-bounds line span");
  return old.slice(0, start).join("") + replacement + old.slice(end).join("");
}
export function legalSpan(start: number, end: number, count: number) {
  return (
    Number.isSafeInteger(start) &&
    Number.isSafeInteger(end) &&
    start >= 0 &&
    end >= start &&
    end <= count
  );
}
export function reference(source: string, turn: { old: string; replacement: string }) {
  const index = source.indexOf(turn.old);
  if (
    index < 0 ||
    source.indexOf(turn.old, index + 1) >= 0 ||
    (index > 0 && source[index - 1] !== "\n")
  )
    throw Error("Ambiguous reference");
  const start = lines(source.slice(0, index)).length,
    end = start + lines(turn.old).length;
  const text = splice(source, start, end, turn.replacement);
  if (text !== source.slice(0, index) + turn.replacement + source.slice(index + turn.old.length))
    throw Error("Partial reference line");
  return { start, end, replacement: turn.replacement, text };
}
export function syntax(path: string, text: string) {
  return parseSync(path, text).errors.map((e) => e.message);
}
