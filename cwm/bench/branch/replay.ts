import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { isDeepStrictEqual as equal } from "node:util";
import { readTraces, trace, type Snapshot, type Trace } from "../../cwm.ts";
import { scalar } from "../composition/plan.ts";
import { held, training, programs } from "./cases.ts";
import { graph, path, train, type Demo, type Mode, type State } from "./predict.ts";

function integer(s: Snapshot | undefined) {
  if (!s?.exact || !scalar(s.value)) throw Error("Missing exact observed scalar");
  return s.value;
}
function project(t: Trace): Demo {
  const g = graph(t.entry, t.files[t.entry]!);
  const raw = t.frames
    .filter((f) => f.stack[0]?.fn === t.fn && f.stack[0].file === t.entry)
    .map((f) => ({
      kind: f.kind,
      site: f.stack[0]!,
      store: g.names.map((name) => integer(f.locals[name])),
    }));
  const states: State[] = [];
  for (const r of raw) {
    const n = g.byLine.get(r.site.line);
    if (!n) {
      if (!/^\s*}\s*;?\s*$/.test(t.files[t.entry]!.split("\n")[r.site.line - 1] ?? ""))
        throw Error("Unmapped source line");
    } else if (states.at(-1)?.pc !== n.id) states.push({ pc: n.id, store: r.store });
  }
  assert.deepEqual(states[0], { pc: g.entry, store: t.args });
  for (const [i, s] of states.entries()) {
    const n = g.nodes.get(s.pc)!,
      to = states[i + 1]?.pc;
    assert(
      n.kind === "return"
        ? to === undefined
        : n.kind === "set"
          ? n.next === to
          : n.yes === to || n.no === to,
      "Skipped semantic boundary",
    );
  }
  assert.equal(t.outcome.kind, "returned");
  return { g, raw, states, end: { returned: integer(t.outcome.result) } };
}
async function load(file: string, split: typeof training) {
  const ts = await Array.fromAsync(readTraces(file)),
    expected = programs(split);
  assert.equal(ts.length, expected.length);
  return ts.map(({ frames, outcome, ...input }, i) => {
    assert.deepEqual(input, expected[i]);
    return project({ ...input, frames, outcome });
  });
}

const hits = () => ({ exact: 0, wrong: 0, abstain: 0 });
const tally = () => ({ semantic: hits(), rawSite: hits(), paths: { exact: 0, total: 0 } });
type Tally = ReturnType<typeof tally>;
function mark(t: ReturnType<typeof hits>, pred: unknown, truth: unknown) {
  t[pred === undefined ? "abstain" : equal(pred, truth) ? "exact" : "wrong"]++;
}
function score(model: ReturnType<typeof train>, runs: Demo[], mode: Mode) {
  const total = tally(),
    families: Record<string, Tally> = {},
    sites: Record<string, Tally> = {};
  for (const { g, raw, states, end } of runs) {
    const family = (families[g.file] ??= tally());
    const targets = (pc: string) => [total, family, (sites[g.file + ":" + pc] ??= tally())];
    const complete = equal(path(model, g, states[0]!.store, mode), [...states.slice(1), end]);
    for (const t of [total, family]) {
      t.paths.total++;
      if (complete) t.paths.exact++;
    }
    states.forEach((s, i) => {
      const guess = model.next(g, s, mode);
      for (const t of targets(s.pc)) mark(t.semantic, guess, states[i + 1] ?? end);
    });
    raw.slice(0, -1).forEach((r, i) => {
      const guess = model.rawSite(g, r, mode);
      for (const t of targets(g.byLine.get(r.site.line)?.id ?? "unmapped"))
        mark(t.rawSite, guess, raw[i + 1]!.site);
    });
  }
  return {
    total,
    families,
    sites: Object.fromEntries(
      Object.entries(sites).map(([k, { semantic, rawSite }]) => [k, { semantic, rawSite }]),
    ),
  };
}

function verify(runs: Demo[]) {
  const m = train(runs);
  assert.deepEqual(m.predicates["<"], ["lt"]);
  assert.deepEqual(m.predicates[">"], ["gt"]);
  assert((m.predicates["==="]?.length ?? 0) > 1);
  for (const d of runs)
    assert.deepEqual(path(m, d.g, d.states[0]!.store, "learned"), [...d.states.slice(1), d.end]);
  const original = runs.find((d) => d.g.file === "test0.ts")!.g;
  const s = { pc: original.entry, store: [2, 9] };
  const n = original.nodes.get(s.pc)!;
  assert(n.kind === "if");
  assert.deepEqual(m.next(original, s, "learned"), { pc: n.yes, store: s.store });
  assert.equal(m.next(original, s, "untrained"), undefined);
  const swapped = structuredClone(runs);
  for (const d of swapped)
    for (const node of d.g.nodes.values()) {
      if (node.kind === "if" && "op" in node.expr) {
        if (node.expr.op === "<") node.expr.op = ">";
        else if (node.expr.op === ">") node.expr.op = "<";
      }
    }
  assert.deepEqual(train(swapped).next(original, s, "learned"), { pc: n.no, store: s.store });
}

if (import.meta.main) {
  const [mode, a, b] = process.argv.slice(2);
  if (mode === "collect" && (a === "train" || a === "held") && b) {
    assert.equal(Bun.version, "1.4.4");
    assert.equal(Bun.spawnSync(["node", "--version"]).stdout.toString().trim(), "v24.19.0");
    const lines = [];
    for (const p of programs(a === "train" ? training : held))
      lines.push(JSON.stringify(await trace(p)));
    await writeFile(b, lines.join("\n") + "\n", { flag: "wx" });
  } else if (mode === "verify" && a) {
    verify(await load(a, training));
    console.log("Training paths, partial identifiability and swapped-label checks passed");
  } else if (mode === "score" && a && b) {
    const model = train(await load(a, training));
    const test = await load(b, held);
    const modes: Mode[] = ["learned", "majority", "flipped", "untrained"];
    console.log(
      JSON.stringify(
        {
          predicates: model.predicates,
          scalars: model.scalars,
          scores: Object.fromEntries(modes.map((k) => [k, score(model, test, k)])),
        },
        null,
        2,
      ),
    );
  } else
    throw Error(
      "Usage: collect train|held NEW.jsonl; verify TRAIN.jsonl; score TRAIN.jsonl HELD.jsonl",
    );
}
