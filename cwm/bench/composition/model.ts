import { fitValues, scalar, type Mode, type Atom } from "../../structured/scalar.ts";
import type { Plan } from "./plan.ts";
export type { Mode, Atom } from "../../structured/scalar.ts";

export type State = { pc: number; store: number[] };
export type Boundary = State | { returned: number };

export function fit(rows: readonly Atom[], mode: Mode = "compose") {
  const values = fitValues(rows, mode);
  return {
    ...values,
    next(p: Plan, state: State): Boundary | undefined {
      const s = p.code[state.pc];
      if (!s || state.store.length !== p.params + state.pc || !state.store.every(scalar)) return;
      const n = values.evaluate(s.expr, state.store);
      if (n === undefined) return;
      return s.returns ? { returned: n } : { pc: state.pc + 1, store: [...state.store, n] };
    },
  };
}
export type Model = ReturnType<typeof fit>;

// No trace parameter: subsequent steps can see only this model's previous prediction.
export function rollout(model: Model, p: Plan, start: State): Boundary[] {
  const result: Boundary[] = [];
  let current = start;
  for (let i = 0; i < p.code.length; i++) {
    const next = model.next(p, current);
    if (!next) break;
    result.push(next);
    if ("returned" in next) break;
    current = next;
  }
  return result;
}
