import { fileURLToPath } from "node:url";
import { isDeepStrictEqual as equal } from "node:util";
import * as Schema from "effect/Schema";
import {
  applyEdit,
  mutations,
  trace,
  type Edit,
  type Frame,
  type Json,
  type Program,
  type Execution,
} from "./cwm.ts";
import { loadSplit } from "./bench/recurrent/dataset.ts";
import { fitStructured } from "./structured.ts";

export async function trainingModel() {
  const training = await Promise.all(
    (["varied", "targeted"] as const).map((split) =>
      loadSplit(
        fileURLToPath(new URL("./bench/recurrent/data/" + split + ".jsonl.gz", import.meta.url)),
        split,
      ),
    ),
  );
  return fitStructured(training.flat().map((row) => row.trace));
}
type Model = ReturnType<typeof fitStructured>;
export type Draft = Omit<Program, "args">;
export type Forecast =
  | { frames: Frame[]; stop: "unseen" | "limit" }
  | { frames: Frame[]; stop: "terminal"; outcome: Execution["outcome"] };
export function forecast(model: Model, draft: Draft, args: Json[], budget = 128): Forecast {
  const start = model.start({ ...draft, args });
  if (!start) return { frames: [], stop: "unseen" };
  const frames = [start];
  const rollout = model.rollout(draft.files, start, budget);
  let r = rollout.next();
  while (!r.done) {
    if (!("stack" in r.value)) return { frames, stop: "terminal", outcome: r.value };
    frames.push(r.value);
    r = rollout.next();
  }
  return { frames, stop: r.value === "limit" ? "limit" : "unseen" };
}

/** Explicit oracle action on trusted source. Finish prediction before collecting any observations. */
export async function verify(model: Model, draft: Draft, args: Json[]) {
  const prediction = forecast(model, draft, args);
  const observed = await trace({ ...draft, args });
  const first = observed.frames.findIndex(
    (f) => f.stack.length === 1 && f.stack[0]?.file === draft.entry && f.stack[0].fn === draft.fn,
  );
  const frames = first < 0 ? [] : observed.frames.slice(first);
  let exactPrefix = 0;
  while (
    exactPrefix < frames.length &&
    exactPrefix < prediction.frames.length &&
    equal(frames[exactPrefix], prediction.frames[exactPrefix])
  )
    exactPrefix++;
  const outcomeMatch =
    prediction.stop === "terminal" ? equal(prediction.outcome, observed.outcome) : null;
  return {
    prediction,
    observed: { frames: observed.frames, outcome: observed.outcome },
    comparison: {
      predictor: "fitStructured",
      start: "predicted-entry",
      observedFrom: first < 0 ? null : first,
      observedCallFrames: frames.length,
      exactPrefix,
      outcomeMatch,
      complete:
        first >= 0 &&
        exactPrefix === frames.length &&
        exactPrefix === prediction.frames.length &&
        outcomeMatch === true,
    },
  };
}

const argsSchema = Schema.mutable(Schema.Array(Schema.MutableJson));
const caseSchema = Schema.Struct({
  args: argsSchema,
  returns: Schema.MutableJson,
  visits: Schema.optional(
    Schema.Array(Schema.Record(Schema.String, Schema.MutableJson).check(Schema.isMinProperties(1))),
  ),
});
export type Example = typeof caseSchema.Type;
export const parseArgs = Schema.decodeUnknownSync(Schema.fromJsonString(argsSchema));
export const parseExample = Schema.decodeUnknownSync(Schema.fromJsonString(caseSchema), {
  onExcessProperty: "error",
});

export function assess(model: Model, draft: Draft, examples: readonly Example[]) {
  return examples.map(({ args, returns, visits = [] }) => {
    // Only source and call cross the predictor boundary. Expectations are scored afterwards.
    const prediction = forecast(model, draft, args);
    if (prediction.stop !== "terminal") return { args, status: prediction.stop };
    let i = 0;
    for (const frame of prediction.frames) {
      const pattern = visits[i];
      if (
        pattern &&
        Object.entries(pattern).every(
          ([name, value]) =>
            Object.hasOwn(frame.locals, name) &&
            frame.locals[name]!.exact &&
            equal(frame.locals[name]!.value, value),
        )
      )
        i++;
    }
    const { outcome } = prediction;
    const matches =
      outcome.kind === "returned" &&
      outcome.result.exact &&
      equal(outcome.result.value, returns) &&
      i === visits.length;
    return { args, status: matches ? "match" : "mismatch", outcome, visitsMatched: i };
  });
}

// Use learned transitions to search a one-edit neighborhood. Only a unique, completely
// predicted candidate can replace the proposal. Preserve the original on ambiguity.
export async function plan(model: Model, draft: Draft, examples: readonly Example[]) {
  const assessment = assess(model, draft, examples);
  const initial = { draft, assessment };
  if (!examples.length) return { ...initial, status: "unconstrained" as const };
  if (assessment.every((c) => c.status === "match"))
    return { ...initial, status: "match" as const };
  const program = { ...draft, args: [] };
  const candidates = await mutations(program);
  let solution: { draft: Draft; assessment: typeof assessment; edit: Edit } | undefined;
  for (const edit of candidates) {
    const { args: _args, ...next } = applyEdit(program, edit);
    const scores = assess(model, next, examples);
    if (scores.every((c) => c.status === "match")) {
      if (solution && !equal(solution.draft.files, next.files))
        return { ...initial, status: "ambiguous" as const };
      solution = { draft: next, assessment: scores, edit };
    }
  }
  return solution
    ? { ...solution, originalAssessment: assessment, status: "repaired" as const }
    : { ...initial, status: "unresolved" as const };
}
