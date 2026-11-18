import { parseSync, type Expression } from "oxc-parser";

export type Expr = { slot: number } | { literal: number } | { op: string; l: Expr; r: Expr };
export function scalar(n: unknown): n is number {
  return typeof n === "number" && Number.isSafeInteger(n) && !Object.is(n, -0);
}

export function entryFunction(file: string, source: string, fn = "run") {
  const syntax = parseSync(file, source);
  const [top] = syntax.program.body;
  const f = top?.type === "ExportNamedDeclaration" ? top.declaration : null;
  if (
    syntax.errors.length ||
    syntax.program.body.length !== 1 ||
    f?.type !== "FunctionDeclaration" ||
    f.id?.name !== fn ||
    f.async ||
    f.generator ||
    !f.body
  )
    throw new Error("Expected a single synchronous exported function");
  const names: string[] = [];
  for (const p of f.params) {
    if (p.type !== "Identifier" || names.includes(p.name)) throw new Error("Invalid parameter");
    names.push(p.name);
  }
  return { names, statements: f.body.body };
}

export function expressions(names: readonly string[]) {
  return function read(e: Expression): Expr {
    if (e.type === "ParenthesizedExpression") return read(e.expression);
    if (e.type === "Literal" && scalar(e.value)) return { literal: e.value };
    if (e.type === "Identifier" && names.includes(e.name)) return { slot: names.indexOf(e.name) };
    if (e.type === "BinaryExpression" && e.left.type !== "PrivateIdentifier")
      return { op: e.operator, l: read(e.left), r: read(e.right) };
    throw new Error("Unsupported expression: " + e.type);
  };
}

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
export function fitValues(rows: readonly Atom[], mode: Mode = "compose") {
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
  };
}
