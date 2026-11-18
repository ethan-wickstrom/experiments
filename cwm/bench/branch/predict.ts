import { fitGuards, unique } from "../../structured/guards.ts";
import type { Statement } from "oxc-parser";
import type { Site } from "../../cwm.ts";
import { fit, type Atom } from "../composition/model.ts";
import { entryFunction, expressions, scalar, type Expr } from "../composition/plan.ts";

type Op =
  | { kind: "if"; yes: string; no: string }
  | { kind: "set"; slot: number; next: string }
  | { kind: "return" };
type Node = Op & { id: string; line: number; col: number; width: number; expr: Expr };
export function graph(file: string, source: string) {
  const { names, statements } = entryFunction(file, source),
    read = expressions(names);
  const nodes = new Map<string, Node>(),
    byLine = new Map<number, Node>();
  function block(stmts: Statement[], path: string, after: string): string {
    let next = after;
    for (let i = stmts.length - 1; i >= 0; i--) {
      const s = stmts[i]!,
        id = path + "." + i;
      let op: Op, expr: Expr;
      if (
        s.type === "IfStatement" &&
        s.consequent.type === "BlockStatement" &&
        (!s.alternate || s.alternate.type === "BlockStatement")
      ) {
        op = {
          kind: "if",
          yes: block(s.consequent.body, id + "T", next),
          no: s.alternate ? block(s.alternate.body, id + "F", next) : next,
        };
        expr = read(s.test);
      } else if (s.type === "ReturnStatement" && s.argument) {
        op = { kind: "return" };
        expr = read(s.argument);
      } else if (
        s.type === "ExpressionStatement" &&
        s.expression.type === "AssignmentExpression" &&
        s.expression.operator === "=" &&
        s.expression.left.type === "Identifier" &&
        names.includes(s.expression.left.name)
      ) {
        op = { kind: "set", slot: names.indexOf(s.expression.left.name), next };
        expr = read(s.expression.right);
      } else throw Error("Unsupported statement " + s.type);
      const prefix = source.slice(0, s.start),
        line = prefix.split("\n").length,
        col = s.start - prefix.lastIndexOf("\n");
      const n = {
        ...op,
        expr,
        id,
        line,
        col,
        width: source.slice(s.start).split("\n", 1)[0]!.length,
      };
      if (byLine.has(line)) throw Error("Require one executable statement per line");
      nodes.set(id, n);
      byLine.set(line, n);
      next = id;
    }
    return next;
  }
  const entry = block(statements, "b", "");
  return { file, names, nodes, byLine, entry };
}
export type Graph = ReturnType<typeof graph>;
export type State = { pc: string; store: number[] };
export type Boundary = State | { returned: number };
export type Mode = "learned" | "majority" | "flipped" | "untrained";
export type Pause = { site: Site; kind: string; store: number[] };
export type Demo = { g: Graph; states: State[]; raw: Pause[]; end: { returned: number } };

const phaseKey = (n: Node, raw: Pause) => [n.kind, raw.kind, raw.site.column - n.col].join("/");
export function train(demos: Demo[]) {
  const atoms: Atom[] = [],
    guards = new Map<string, { x: number; y: number; arm: boolean }[]>();
  const phases = new Map<string, string[]>(),
    landings = new Map<string, number[]>();
  function add<T>(m: Map<string, T[]>, k: string, v: T) {
    const vs = m.get(k) ?? [];
    vs.push(v);
    m.set(k, vs);
  }
  for (const { g, states, raw } of demos) {
    for (const [i, s] of states.entries()) {
      const n = g.nodes.get(s.pc)!,
        e = n.expr,
        t = states[i + 1];
      if (n.kind === "return") continue;
      if (!t || !("op" in e) || !("slot" in e.l) || !("slot" in e.r))
        throw Error("Training requires atomic transitions");
      const x = s.store[e.l.slot]!,
        y = s.store[e.r.slot]!;
      if (n.kind === "set") atoms.push({ expr: e, x, y, z: t.store[n.slot]! });
      else {
        if (n.yes === n.no || (t.pc !== n.yes && t.pc !== n.no))
          throw Error("Unidentifiable training arm");
        const rows = guards.get(e.op) ?? [];
        rows.push({ x, y, arm: t.pc === n.yes });
        guards.set(e.op, rows);
      }
    }
    for (const [i, r] of raw.entries()) {
      const n = g.byLine.get(r.site.line),
        prev = raw[i - 1],
        prevNode = prev && g.byLine.get(prev.site.line);
      if (!n) continue;
      if (prevNode !== n) {
        const off = r.site.column - n.col;
        add(landings, (prevNode?.kind ?? "entry") + "/" + n.kind, off);
        add(landings, "*/" + n.kind, off);
      }
      const t = raw[i + 1],
        dest = t && g.byLine.get(t.site.line);
      add(
        phases,
        phaseKey(n, r),
        !dest ? "end" : dest === n ? "same:" + String(t!.site.column - n.col) : "successor",
      );
    }
  }
  const values = fit(atoms),
    { rules, decide } = fitGuards(guards);
  function next(g: Graph, s: State, mode: Mode): Boundary | undefined {
    const n = g.nodes.get(s.pc);
    if (!n || s.store.length !== g.names.length || !s.store.every(scalar)) return;
    if (n.kind === "if") {
      const e = n.expr;
      if (!("op" in e)) return;
      const rows = guards.get(e.op);
      if (!rows || mode === "untrained") return;
      let arm: boolean | undefined;
      if (mode === "majority") arm = rows.filter((r) => r.arm).length * 2 > rows.length;
      else {
        const x = values.evaluate(e.l, s.store),
          y = values.evaluate(e.r, s.store);
        if (x === undefined || y === undefined) return;
        arm = decide(e.op, x, y);
        if (arm === undefined) return;
        if (mode === "flipped") arm = !arm;
      }
      const pc = arm ? n.yes : n.no;
      return pc ? { pc, store: [...s.store] } : undefined;
    }
    const v = values.evaluate(n.expr, s.store);
    if (v === undefined) return;
    if (n.kind === "return") return { returned: v };
    const store = [...s.store];
    store[n.slot] = v;
    return n.next ? { pc: n.next, store } : undefined;
  }
  function rawSite(g: Graph, r: Pause, mode: Mode): Site | undefined {
    const n = g.byLine.get(r.site.line);
    if (!n) return;
    const phase = unique(phases.get(phaseKey(n, r)) ?? []);
    if (!phase || phase === "end") return;
    let dest = n,
      off: number | undefined;
    if (phase === "successor") {
      const step = next(g, { pc: n.id, store: r.store }, mode);
      if (!step || !("pc" in step)) return;
      dest = g.nodes.get(step.pc)!;
      off = unique(landings.get(n.kind + "/" + dest.kind) ?? landings.get("*/" + dest.kind) ?? []);
    } else off = Number(phase.slice(5));
    if (off === undefined || off < 0 || off >= dest.width) return;
    return { file: g.file, fn: "run", line: dest.line, column: dest.col + off };
  }
  return { next, rawSite, predicates: Object.fromEntries(rules), scalars: values.survivors };
}

export function path(model: ReturnType<typeof train>, g: Graph, parameters: number[], mode: Mode) {
  let s: Boundary = { pc: g.entry, store: parameters };
  const out: Boundary[] = [];
  for (let i = 0; i < g.nodes.size && "pc" in s; i++) {
    const t = model.next(g, s, mode);
    if (!t) break;
    out.push(t);
    s = t;
  }
  return out;
}
