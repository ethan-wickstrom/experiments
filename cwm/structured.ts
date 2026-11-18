import { isDeepStrictEqual } from "node:util";
import {
  evaluate,
  readTraces,
  rollForward,
  type Frame,
  type Observation,
  type Program,
  type Trace,
} from "./cwm.ts";
import { compile, type Graph, type Instruction } from "./structured/graph.ts";
import { fitGuards, type GuardRows } from "./structured/guards.ts";
import { fitLandings, type Example } from "./structured/landing.ts";
import { fitValues, scalar, type Atom } from "./structured/scalar.ts";

type Modes = { offsets?: boolean; mappedReturns?: boolean; permuted?: boolean };
function decode(g: Graph, frame: Frame) {
  const site = frame.stack[0];
  if (
    !site ||
    frame.stack.length !== 1 ||
    frame.kind === "exception" ||
    Object.keys(frame.locals).length !== g.names.length
  )
    return;
  const store: number[] = [];
  for (const name of g.names) {
    const s = Object.hasOwn(frame.locals, name) ? frame.locals[name] : undefined;
    if (!s?.exact || !scalar(s.value)) return;
    store.push(s.value);
  }
  const pos = g.position(site);
  if (pos === undefined) return;
  const node = g.at(pos);
  if (
    !node ||
    (frame.kind === "return" &&
      (node.kind !== "return" || !frame.value?.exact || !scalar(frame.value.value)))
  )
    return;
  return { node, store, pos, event: frame.kind, value: frame.value };
}

// Train on complete accepted root invocations. Fail closed when source, cadence or projections
// fall outside this supervision contract. A failed trace cannot silently become a missing edge.
export function fitStructured(
  runs: Iterable<Trace>,
  { mappedReturns = false, offsets = false, permuted = false }: Modes = {},
) {
  const landings: Example[] = [],
    atoms: Atom[] = [],
    guards: GuardRows = new Map();
  for (const t of runs) {
    if (Object.keys(t.files).length !== 1 || !Object.hasOwn(t.files, t.entry))
      throw Error("Structured training requires a single source");
    const g = compile(t.entry, t.fn, t.files[t.entry]!, mappedReturns);
    const start = t.frames.findIndex((f) => f.stack[0]?.fn === t.fn && f.stack[0].file === t.entry);
    if (start < 0) throw Error("No observed function entry");
    const states = t.frames.slice(start).map((f) => {
      const state = decode(g, f);
      if (!state) throw Error("Unsupported training frame in " + t.entry);
      return state;
    });
    const last = states.at(-1)!;
    if (
      states[0]!.node.id !== g.entry ||
      last.event !== "return" ||
      t.outcome.kind !== "returned" ||
      !isDeepStrictEqual(last.value, t.outcome.result)
    )
      throw Error("Incomplete function trajectory in " + t.entry);
    for (const [i, s] of states.entries()) {
      const n = s.node,
        t1 = states[i + 1];
      if (t1) {
        const dest = t1.node;
        const within = n.id === dest.id;
        const edge =
          n.kind === "return"
            ? within && t1.event === "return"
            : n.kind === "set"
              ? n.next === dest.id
              : n.yes === dest.id || n.no === dest.id;
        if (
          !edge ||
          s.event !== "step" ||
          s.store.some((v, j) => (n.kind !== "set" || j !== n.slot) && t1.store[j] !== v)
        )
          throw Error("Unsupported observed transition in " + t.entry);
        landings.push({ origin: n, dest, within, event: t1.event, position: t1.pos });
      }
      const e = n.expr;
      if (!("op" in e) || "op" in e.l || "op" in e.r) continue;
      const x = "slot" in e.l ? s.store[e.l.slot]! : e.l.literal;
      const y = "slot" in e.r ? s.store[e.r.slot]! : e.r.literal;
      if (n.kind === "return" && s.event === "return" && scalar(s.value?.value))
        atoms.push({ expr: e, x, y, z: s.value.value });
      else if (n.kind === "set" && t1) atoms.push({ expr: e, x, y, z: t1.store[n.slot]! });
      else if ((n.kind === "if" || n.kind === "while") && n.yes !== n.no && t1) {
        const rows = guards.get(e.op) ?? [];
        rows.push({ x, y, arm: n.yes === t1.node.id });
        guards.set(e.op, rows);
      }
    }
  }
  const values = fitValues(atoms, permuted ? "permuted" : "compose"),
    predicates = fitGuards(guards),
    land = fitLandings(landings, offsets, mappedReturns);

  // Bounded cache, keyed by source contents so edits and renamed exports invalidate it.
  let cached: { file: string; fn: string; source: string; graph?: Graph } | undefined;
  function predict(files: Program["files"], f: Frame): Observation | undefined {
    const site = f.stack[0];
    if (
      !site?.fn ||
      f.stack.length !== 1 ||
      Object.keys(files).length !== 1 ||
      !Object.hasOwn(files, site.file)
    )
      return;
    const source = files[site.file]!;
    if (!cached || cached.file !== site.file || cached.fn !== site.fn || cached.source !== source) {
      cached = { file: site.file, fn: site.fn, source };
      try {
        cached.graph = compile(site.file, site.fn, source, mappedReturns);
      } catch {
        return;
      }
    }
    const g = cached.graph;
    if (!g) return;
    const s = decode(g, f);
    if (!s) return;
    if (s.event === "return") return { kind: "returned", result: structuredClone(s.value!) };
    const n = s.node,
      store = s.store;
    let dest: Instruction | undefined;
    if (n.kind === "set") {
      const v = values.evaluate(n.expr, store);
      if (v === undefined) return;
      store[n.slot] = v;
      dest = g.nodes[n.next];
    } else if (n.kind === "return") dest = n;
    else {
      const e = n.expr;
      if (!("op" in e)) return;
      const a = values.evaluate(e.l, store),
        b = values.evaluate(e.r, store);
      if (a === undefined || b === undefined) return;
      const arm = predicates.decide(e.op, a, b);
      if (arm === undefined) return;
      dest = g.nodes[arm ? n.yes : n.no];
    }
    if (!dest) return;
    const landing = land(n, dest, n.kind === "return");
    if (!landing) return;
    const next: Frame = {
      kind: landing.event,
      stack: [g.site(landing.position)],
      locals: Object.fromEntries(
        g.names.map((name, i) => [name, { value: store[i]!, exact: true }]),
      ),
    };
    if (next.kind === "return") {
      if (dest.kind !== "return") return;
      const value = values.evaluate(dest.expr, store);
      if (value === undefined) return;
      next.value = { exact: true, value };
    }
    return next;
  }
  return {
    predict,
    rollout: (files: Program["files"], start: Frame, budget: number) =>
      rollForward(predict, files, start, budget),
  };
}

if (import.meta.main) {
  const [mode, training, held] = process.argv.slice(2);
  if (mode !== "score" || !training || !held)
    throw Error("Usage: bun structured.ts score TRAIN.jsonl HELD.jsonl");
  const model = fitStructured(await Array.fromAsync(readTraces(training)));
  let score = evaluate(model, []);
  for await (const t of readTraces(held)) score = evaluate(model, [t], score);
  console.log(JSON.stringify(score));
}
