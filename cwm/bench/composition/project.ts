import type { Frame, Snapshot, Trace } from "../../cwm.ts";
import type { Atom, State } from "./model.ts";
import { plan, scalar } from "./plan.ts";

function observed(s: Snapshot | undefined) {
  if (!s?.exact || !scalar(s.value)) throw new Error("Expected an observed exact safe integer");
  return s.value;
}

// Labels only. Select the first function pause on each statement line by site, not by value.
export function project(t: Trace) {
  const p = plan(t.files[t.entry]!);
  const stops: Frame[] = [];
  for (const f of t.frames) {
    const site = f.stack[0];
    if (site?.fn !== t.fn || site.file !== t.entry) continue;
    if (f.kind === "exception") throw new Error("Unexpected guest exception");
    const pc = p.code.findIndex((s) => s.line === site.line);
    if (pc === stops.length) stops.push(f);
    else if (pc < 0 || pc !== stops.length - 1) throw new Error("Unmapped or skipped boundary");
  }
  if (stops.length !== p.code.length || t.outcome.kind !== "returned")
    throw new Error("Incomplete straight-line trace");
  const states: State[] = stops.map((f, pc) => {
    const live = p.names.slice(0, p.params + pc);
    for (const [name, s] of Object.entries(f.locals))
      if (
        !live.includes(name) &&
        (!p.names.includes(name) || s.exact || s.value !== "<unavailable>")
      )
        throw new Error("Unexpected visible binding: " + name);
    return { pc, store: live.map((n) => observed(f.locals[n])) };
  });
  return { p, states, end: { returned: observed(t.outcome.result) } };
}
export type Sample = ReturnType<typeof project>;

export function example({ p, states }: Sample): Atom {
  const expr = p.code[0]?.expr;
  if (
    p.code.length !== 2 ||
    p.code[0]!.returns ||
    !expr ||
    !("op" in expr) ||
    !("slot" in expr.l) ||
    !("slot" in expr.r)
  )
    throw new Error("Training requires atomic stores");
  const before = states[0]!.store,
    after = states[1]!.store;
  if (!before.every((v, i) => after[i] === v)) throw new Error("Unexpected additional change");
  return { expr, x: before[expr.l.slot]!, y: before[expr.r.slot]!, z: after[p.params]! };
}
