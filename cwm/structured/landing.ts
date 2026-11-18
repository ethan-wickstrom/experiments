import type { Instruction } from "./graph.ts";

export type Event = "step" | "return";
export type Landing = { event: Event; position: number };
export type Example = Landing & {
  origin: Instruction | undefined;
  dest: Instruction;
  within: boolean;
};

function context(origin: Instruction | undefined, dest: Instruction) {
  return [
    origin?.kind ?? "call",
    "slot" in dest.expr ? "slot" : "op" in dest.expr ? "op" : "literal",
    String(origin?.kind === "set" && "slot" in dest.expr && origin.slot === dest.expr.slot),
  ];
}

function keys(row: Example, offsets: boolean, mappedReturns: boolean) {
  const { dest, event, position } = row;
  const anchors = offsets
    ? [String(position - dest.start)]
    : (mappedReturns && event === "return" ? ["mappedReturn"] : Object.keys(dest.anchors)).filter(
        (k) => dest.anchors[k] === position,
      );
  return new Set(anchors.map((k) => event + ":" + k));
}
const bucket = (n: Instruction, within: boolean) => n.kind + (within ? "/within" : "/enter");
const cell = (features: string[], mask: number) =>
  JSON.stringify(features.filter((_, i) => mask & (1 << i)));

// Intersect (event kind, position expression) hypotheses within each context. Retain all
// maximally covered partitions using the fewest features. Conflicted cells stay empty.
export function fitLandings(rows: Example[], offsets: boolean, mappedReturns: boolean) {
  const tables = new Map<string, { mask: number; groups: Map<string, Set<string>> }[]>();
  for (const [key, samples] of Map.groupBy(rows, (r) => bucket(r.dest, r.within))) {
    const options = [];
    const width = context(samples[0]!.origin, samples[0]!.dest).length;
    let bestCoverage = 0,
      minFeatures = Infinity;
    for (let mask = 0; mask < 1 << width; mask++) {
      const size = mask.toString(2).replaceAll("0", "").length;
      const counts = new Map<string, number>();
      const groups = new Map<string, Set<string>>();
      for (const r of samples) {
        const group = cell(context(r.origin, r.dest), mask),
          prev = groups.get(group);
        counts.set(group, (counts.get(group) ?? 0) + 1);
        const labels = keys(r, offsets, mappedReturns);
        groups.set(group, prev ? prev.intersection(labels) : labels);
      }
      const coverage = [...groups].reduce(
        (n, [k, labels]) => n + (labels.size ? counts.get(k)! : 0),
        0,
      );
      if (coverage < bestCoverage || (coverage === bestCoverage && size > minFeatures)) continue;
      if (coverage > bestCoverage || size < minFeatures) options.length = 0;
      bestCoverage = coverage;
      minFeatures = size;
      options.push({ mask, groups });
    }
    tables.set(key, options);
  }
  return function land(
    origin: Instruction | undefined,
    dest: Instruction,
    within: boolean,
  ): Landing | undefined {
    let result: Landing | undefined;
    for (const table of tables.get(bucket(dest, within)) ?? []) {
      const group = table.groups.get(cell(context(origin, dest), table.mask));
      if (!group?.size) return;
      for (const key of group) {
        const [event, rule] = key.split(":") as [Event, string];
        const position = offsets ? dest.start + Number(rule) : dest.anchors[rule];
        if (position === undefined || position < dest.start || position >= dest.end) return;
        if (result && (result.event !== event || result.position !== position)) return;
        result = { event, position };
      }
    }
    return result;
  };
}
