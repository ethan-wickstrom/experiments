import { readTraces, type Frame } from "../../../cwm.ts";
import { fitStructured } from "../../../structured.ts";
import { loadSplit } from "../../recurrent/dataset.ts";

// The Python grader supplies the verified tape. Use only the source and the
// current function frame for a prediction, including on each self-fed step.
const train = await loadSplit(
  new URL("../../recurrent/data/fixed.jsonl.gz", import.meta.url).pathname,
  "fixed",
);
const model = fitStructured(
  train.map((row) => row.trace),
  { entryEvidence: false },
);
const [mode, tape] = process.argv.slice(2);
if ((mode !== "first" && mode !== "trajectory") || !tape)
  throw Error("Usage: bun structured.ts first|trajectory TAPE");
for await (const trace of readTraces(tape)) {
  const frames = trace.frames.slice(1);
  const currents = mode === "first" ? frames.slice(0, 1) : frames.slice(0, -1);
  const next = currents.map((frame) => model.predict(trace.files, frame) ?? null);
  const rollout: Frame[] = [];
  if (mode === "trajectory") {
    for (const step of model.rollout(trace.files, frames[0]!, 16)) {
      if (!("stack" in step)) break;
      rollout.push(step);
      if (step.kind === "return") break;
    }
  }
  console.log(
    JSON.stringify({
      entry: trace.entry,
      source: trace.files[trace.entry],
      args: trace.args,
      next,
      rollout,
    }),
  );
}
