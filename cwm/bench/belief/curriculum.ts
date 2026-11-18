import type { Input } from "./types.ts";

/** Minimum edge cover: extend a maximum bipartite matching to uncovered vertices. */
export function cover(inputs: Input[]): number[] {
  const edges = inputs.map(
    (x) => [JSON.stringify([x.setup, x.signal]), JSON.stringify([x.write, x.index])] as const,
  );
  const ix = edges.map((_, i) => i);
  const left = Map.groupBy(ix, (i) => edges[i]![0]),
    right = Map.groupBy(ix, (i) => edges[i]![1]);
  const matched = new Map<string, number>();
  function augment(l: string, seen: Set<string>): boolean {
    for (const i of left.get(l)!) {
      const r = edges[i]![1];
      if (seen.has(r)) continue;
      seen.add(r);
      const prev = matched.get(r);
      if (prev === undefined || augment(edges[prev]![0], seen)) {
        matched.set(r, i);
        return true;
      }
    }
    return false;
  }
  for (const l of left.keys()) augment(l, new Set());
  const chosen = new Set(matched.values());
  for (const adj of [left, right])
    for (const group of adj.values()) if (!group.some((i) => chosen.has(i))) chosen.add(group[0]!);
  return [...chosen].sort((a, b) => a - b);
}

export function uniform(n: number, k: number, seed: number) {
  return Array.from({ length: n }, (_, i) => ({
    i,
    key: new Bun.CryptoHasher("sha256").update(JSON.stringify([seed, i])).digest("hex"),
  }))
    .sort((a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : a.i - b.i))
    .slice(0, k)
    .map((x) => x.i);
}
