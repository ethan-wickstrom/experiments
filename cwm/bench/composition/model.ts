import { scalar, type Expr, type Plan } from "./plan.ts";

export interface Atom {
  expr: Extract<Expr, { op: string }>;
  x: number;
  y: number;
  z: number;
}
type Rule = readonly [bigint, bigint, bigint, bigint];
const basis: Rule[] = [];
const weights = [-1n, 0n, 1n];
for (const a of weights)
  for (const b of weights)
    for (const c of weights) for (const d of weights) basis.push([a, b, c, d]);

const apply = ([a, b, c, d]: Rule, x: bigint, y: bigint) => a + b * x + c * y + d * x * y;
export type Mode = "compose" | "whole" | "permuted";
export type State = { pc: number; store: number[] };
export type Boundary = State | { returned: number };

export function fit(rows: readonly Atom[], mode: Mode = "compose") {
  const rules = new Map<string, Rule[]>();
  const seen = new Set<string>();
  for (const { expr, x, y, z } of rows) {
    if (![x, y, z].every(scalar)) throw new Error("Inexact atomic label");
    seen.add(JSON.stringify(expr));
    const candidates = rules.get(expr.op) ?? basis;
    rules.set(
      expr.op,
      candidates.filter((r) => apply(r, BigInt(x), BigInt(y)) === BigInt(z)),
    );
  }
  const tokens = [...rules.keys()].sort();
  function infer(e: Expr, slots: readonly number[]): number | undefined {
    if (!("op" in e)) {
      const value = "slot" in e ? slots[e.slot] : e.literal;
      return scalar(value) ? value : undefined;
    }
    if (mode === "whole" && !seen.has(JSON.stringify(e))) return;
    const x = infer(e.l, slots),
      y = infer(e.r, slots);
    // Zero operands can produce signed zero in JS, absent from this integer algebra.
    if (!scalar(x) || !scalar(y) || x === 0 || y === 0) return;
    if (!rules.has(e.op)) return;
    const key = mode === "permuted" ? tokens[(tokens.indexOf(e.op) + 1) % tokens.length]! : e.op;
    let value: number | undefined;
    for (const r of rules.get(key)!) {
      const n = Number(apply(r, BigInt(x), BigInt(y)));
      if (!scalar(n) || (value !== undefined && n !== value)) return;
      value = n;
    }
    return value;
  }
  return {
    evaluate: infer,
    survivors: Object.fromEntries([...rules].map(([op, rs]) => [op, rs.map((r) => r.map(Number))])),
    next(p: Plan, state: State): Boundary | undefined {
      const s = p.code[state.pc];
      if (!s || state.store.length !== p.params + state.pc || !state.store.every(scalar)) return;
      const n = infer(s.expr, state.store);
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
