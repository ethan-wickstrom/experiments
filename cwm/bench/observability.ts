import { readTraces, type Observation, type Trace } from "../cwm.ts";

const visibleSite = (f: Observation) => ("stack" in f ? [f.kind, f.stack] : [f.kind]);
const key = (value: unknown) =>
  JSON.stringify(value, (_key, v: unknown) =>
    v !== null && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)))
      : v,
  );

/** Empirical ambiguity of equally *observable* inputs, not out-of-sample error. */
export function ambiguity(
  traces: Iterable<Trace>,
  history: "site" | "frame" | "prefix",
  target: "site" | "state",
) {
  const groups = new Map<string, Map<string, number>>();
  const prefixIds = new Map<string, number>();
  let rows = 0;
  for (const t of traces) {
    const source = key([t.files, t.entry, t.fn]);
    let prefix = 0;
    for (const [i, f] of t.frames.entries()) {
      const next = t.frames[i + 1] ?? t.outcome;
      const extension = key([prefix, f]);
      if (!prefixIds.has(extension)) prefixIds.set(extension, prefixIds.size + 1);
      prefix = prefixIds.get(extension)!;
      if (!f.stack[0]?.fn) continue;
      const input = key([
        source,
        history === "site" ? visibleSite(f) : history === "frame" ? f : prefix,
      ]);
      const y = key(target === "site" ? visibleSite(next) : next);
      let counts = groups.get(input);
      if (!counts) {
        counts = new Map();
        groups.set(input, counts);
      }
      counts.set(y, (counts.get(y) ?? 0) + 1);
      rows++;
    }
  }
  let singleton = 0,
    conflictingGroups = 0,
    conflictingRows = 0,
    unavoidableMisses = 0,
    bits = 0;
  for (const counts of groups.values()) {
    const freq = [...counts.values()],
      n = freq.reduce((a, b) => a + b, 0);
    if (n === 1) singleton++;
    if (freq.length === 1) continue;
    conflictingGroups++;
    conflictingRows += n;
    unavoidableMisses += n - Math.max(...freq);
    for (const c of freq) bits -= c * Math.log2(c / n);
  }
  return {
    rows,
    groups: groups.size,
    singleton,
    conflictingGroups,
    conflictingRows,
    unavoidableMisses,
    bitsPerStep: rows ? bits / rows : 0,
  };
}

if (import.meta.main) {
  const path = process.argv[2];
  if (!path) throw new Error("Usage: bun bench/observability.ts TRACES.jsonl");
  const traces = await Array.fromAsync(readTraces(path));
  const profiles = [];
  for (const history of ["site", "frame", "prefix"] as const)
    for (const target of ["site", "state"] as const)
      profiles.push({ history, target, ...ambiguity(traces, history, target) });
  console.log(JSON.stringify({ traces: traces.length, profiles }, null, 2));
}
