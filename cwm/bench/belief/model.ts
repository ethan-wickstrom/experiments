import type { Atom, Example, Forecast, Input } from "./types.ts";

type Patch = [cell: number, delta: number][];
type CountedPatch = { patch: Patch; count: number };
type Writes = { patches: Map<string, CountedPatch>; total: number };
type Follows = { followed: number; stayed: number; total: number; unsupported: boolean };
type History = Map<Input["signal"], Follows>;

const writeKey = (x: Input) => JSON.stringify([x.write, x.index]);

function pair(rows: number[][]): rows is [number[], number[]] {
  if (rows.length !== 2) return false;
  for (const row of rows) {
    if (!row) return false;
    for (const value of row) if (!Number.isFinite(value)) return false;
  }
  return true;
}

function patchBetween(before: number[], after: number[]): Patch | undefined {
  if (before.length !== after.length) return;
  const patch: Patch = [];
  for (const [cell, value] of after.entries()) {
    const old = before[cell]!;
    if (old === value) continue;
    const delta = value - old;
    if (!Number.isFinite(delta) || old + delta !== value) return;
    patch.push([cell, delta]);
  }
  return patch;
}

function apply(before: number[], patch: Patch): number[] | undefined {
  const after = [...before];
  for (const [cell, delta] of patch) {
    const old = before[cell];
    if (old === undefined || !Number.isFinite(old + delta)) return;
    after[cell] = old + delta;
  }
  return after;
}

function equal(a: number[] | undefined, b: number[]): boolean {
  return a?.length === b.length && b.every((v, i) => v === a[i]);
}

// A masked query uses directly observed masked cases when present. Otherwise
// marginalize both observed signal strata at their empirical frequencies.
function strata(history: History, signal: Input["signal"]): Follows[] {
  const matched = history.get(signal);
  if (matched) return [matched];
  const yes = history.get(true);
  const no = history.get(false);
  return signal === null && yes && no ? [yes, no] : [];
}

function followProbability(groups: Follows[]): number | undefined {
  let total = 0;
  let follows = 0;
  for (const group of groups) {
    const informative = group.followed + group.stayed;
    if (!informative) return;
    follows += group.total * (group.followed / informative);
    total += group.total;
  }
  return follows / total;
}

/**
 * Fit P(cell deltas | write, index) and P(second follows | setup, signal)
 * independently from two fixed-length observable arrays. Only distinguishable
 * follow/stay outcomes vote. A no-op still counts as a write observation.
 * Multiply the factors on the query's own values and coalesce identical states.
 * Setup and write are opaque source-derived keys supplied by the caller.
 */
export function fit(train: Example[]): Forecast {
  const writes = new Map<string, Writes>();
  const histories = new Map<string, History>();
  for (const { input, after } of train) {
    const key = writeKey(input);
    const writesHere = writes.get(key) ?? { patches: new Map<string, CountedPatch>(), total: 0 };
    const history = histories.get(input.setup) ?? new Map<Input["signal"], Follows>();
    const counts = history.get(input.signal) ?? {
      followed: 0,
      stayed: 0,
      total: 0,
      unsupported: false,
    };
    writes.set(key, writesHere);
    histories.set(input.setup, history);
    history.set(input.signal, counts);
    writesHere.total++;
    counts.total++;

    if (!pair(input.before) || !pair(after)) {
      counts.unsupported = true;
      continue;
    }
    const patch = patchBetween(input.before[0], after[0]);
    if (!patch) {
      counts.unsupported = true;
      continue;
    }
    const encoded = JSON.stringify(patch);
    const seen = writesHere.patches.get(encoded) ?? { patch, count: 0 };
    seen.count++;
    writesHere.patches.set(encoded, seen);

    const stayed = equal(input.before[1], after[1]);
    const followed = equal(apply(input.before[1], patch), after[1]);
    if (followed && !stayed) counts.followed++;
    if (stayed && !followed) counts.stayed++;
    if (!stayed && !followed) counts.unsupported = true;
  }

  return (input) => {
    const writesHere = writes.get(writeKey(input));
    const history = histories.get(input.setup);
    if (!writesHere || !history || !pair(input.before)) return [];
    const groups = strata(history, input.signal);
    if (!groups.length || groups.some((g) => g.unsupported)) return [];
    const followProb = followProbability(groups);
    const atoms = new Map<string, Atom>();
    let represented = 0;
    for (const { patch, count } of writesHere.patches.values()) {
      const first = apply(input.before[0], patch);
      if (!first) return [];
      represented += count;
      const stay = input.before[1];
      const follow = apply(stay, patch);
      const p = equal(follow, stay) ? 0 : followProb;
      if (p === undefined || (p > 0 && !follow)) return [];
      const alternatives = [
        [stay, 1 - p],
        [follow, p],
      ] as const;
      for (const [second, mass] of alternatives) {
        if (!second || mass <= 0) continue;
        const state = [first, [...second]];
        const encoded = JSON.stringify(state);
        const atom = atoms.get(encoded) ?? { state, prob: 0 };
        atom.prob += (count / writesHere.total) * mass;
        atoms.set(encoded, atom);
      }
    }
    return represented === writesHere.total ? [...atoms.values()] : [];
  };
}
