import assert from "node:assert/strict";
import { test } from "bun:test";
import { trace, type Trace } from "../../cwm.ts";
import { cases, example } from "./cases.ts";

test("checkerboard balances source atoms and never splits a source's four inputs", () => {
  const runs = cases();
  assert.equal(runs.length, 64);
  const cells = Map.groupBy(runs, ({ program: p }) => p.files[p.entry]!);
  assert.equal(cells.size, 16);
  const counts = new Map<string, number>();
  for (const [source, cell] of cells) {
    assert.deepEqual(
      cell.map((c) => c.program.args),
      [
        [false, 0],
        [false, 1],
        [true, 0],
        [true, 1],
      ],
    );
    const split = cell[0]!.split;
    assert(cell.every((c) => c.split === split));
    for (const line of [source.split("\n")[2], source.split("\n")[4]]) {
      const key = split + ":" + line;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }
  assert.equal(counts.size, 16);
  assert([...counts.values()].every((n) => n === 2));
});

test("V8 twin frames coincide at the write; full successor pairs distinguish both alias polarities", async () => {
  // One cell per setup and write, spanning both splits, both flags and both indices.
  const fixtures = [
    { row: 0, col: 1, aliasFlag: true, reverse: true, delta: -2 },
    { row: 1, col: 0, aliasFlag: true, reverse: false, delta: 1 },
    { row: 2, col: 2, aliasFlag: false, reverse: true, delta: 3 },
    { row: 3, col: 3, aliasFlag: false, reverse: false, delta: -1 },
  ];
  for (const { row, col, aliasFlag, reverse, delta } of fixtures) {
    const start = (4 * row + col) * 4;
    const twins = await Promise.all(
      cases()
        .slice(start, start + 4)
        .map(async ({ program: p }) => {
          const t = await trace(p);
          const e = example({ ...t, args: [] }); // The signal must come from the observed prefix.
          const [flag, k] = p.args;
          assert(typeof flag === "boolean" && typeof k === "number");
          const a = [2, 5];
          const slot = reverse ? 1 - k : k;
          a[slot] = a[slot]! + delta;
          assert.deepEqual(e.input.before, [
            [2, 5],
            [2, 5],
          ]);
          assert.deepEqual(e.after, [a, flag === aliasFlag ? a : [2, 5]]);
          assert.equal(e.input.signal, flag);
          assert.equal(e.input.index, k);
          const pre = t.frames.findLast((f) => f.stack[0]?.line === 5);
          assert(pre);
          return { pre, masked: { ...e.input, signal: null } };
        }),
    );
    assert.deepEqual(twins[0], twins[2]);
    assert.deepEqual(twins[1], twins[3]);
  }
}, 60_000);

test("source spans survive file and whitespace shifts; missing, ambiguous and corrupt labels fail closed", async () => {
  const p = cases()[0]!.program,
    source = p.files[p.entry]!;
  const t = await trace(p),
    e = example(t);
  const file = "renamed.ts";
  const formatted =
    "\n" +
    source.replaceAll("  ", "    ").replace("a[index]++", "a[ index ] ++").replaceAll("\n", "\r\n");
  assert.deepEqual(example(await trace({ ...p, entry: file, files: { [file]: formatted } })), e);
  const bad = (edit: (t: Trace) => void) => {
    const clone = structuredClone(t);
    edit(clone);
    assert.throws(() => example(clone));
  };
  const i = t.frames.findIndex((f) => f.stack[0]?.line === 5);
  assert(i >= 0);
  bad((x) => {
    x.frames.splice(i, 1);
  });
  bad((x) => {
    x.frames.splice(i + 2, 0, x.frames[i]!);
  });
  bad((x) => {
    x.frames[i]!.stack[0]!.column = source.split("\n")[4]!.length;
  });
  bad((x) => {
    x.frames[i]!.locals.a!.exact = false;
  });
  bad((x) => {
    x.frames[i + 1]!.locals.surprise = { exact: true, value: 42 };
  });
  bad((x) => {
    x.frames[i + 1]!.locals.b!.value = [2, 7];
  });
  bad((x) => {
    x.frames.splice(i, 0, {
      ...x.frames[i]!,
      locals: { ...x.frames[i]!.locals, a: { exact: true, value: [1, 5] } },
    });
  });
  bad((x) => {
    x.files[p.entry] = source.replace("a[index]++", "a[index] *= 9");
  });
});
