/** Both candidates remain byte-identical across the two incompatible specifications. */
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { Effect } from "effect";
import { wire, type Action, type Event } from "../../project/protocol.ts";
import { runTests } from "../../project/sandbox.ts";

const cases = [
  {
    name: "take",
    args: "items: string[]",
    bodies: ["items[0]", "items.at(-1)"],
    input: '["red","teal"]',
    results: ['"red"', '"teal"'],
    goals: [
      "Return the oldest entry in insertion order.",
      "Return the newest entry in insertion order.",
    ],
  },
  {
    name: "wrap",
    args: "index: number, size: number",
    bodies: ["(index + 1) % size", "(index + size - 1) % size"],
    input: "0, 5",
    results: ["1", "4"],
    goals: ["Move one position forward cyclically.", "Move one position backward cyclically."],
  },
  {
    name: "due",
    args: "clock: number, deadline: number",
    bodies: ["clock > deadline", "clock >= deadline"],
    input: "18, 18",
    results: ["false", "true"],
    goals: [
      "An item becomes due strictly after its deadline.",
      "An item is due starting at its deadline.",
    ],
  },
  {
    name: "compress",
    args: "samples: number[]",
    bodies: ["Math.min(...samples)", "Math.max(...samples)"],
    input: "[4, -2, 9]",
    results: ["-2", "9"],
    goals: ["Keep the lowest sample.", "Keep the highest sample."],
  },
  {
    name: "joinKey",
    args: "namespace: string, id: string",
    bodies: ['namespace + ":" + id', 'id + ":" + namespace'],
    input: '"apac","k8"',
    results: ['"apac:k8"', '"k8:apac"'],
    goals: ["Put the namespace before the identifier.", "Put the identifier before the namespace."],
  },
  {
    name: "occupied",
    args: "cells: boolean[]",
    bodies: ["cells.some(Boolean)", "cells.every(Boolean)"],
    input: "[true,false,true]",
    results: ["true", "false"],
    goals: ["Report whether any cell is occupied.", "Report whether the whole row is occupied."],
  },
] as const;

function queries() {
  return cases.flatMap((c) =>
    c.goals.flatMap((goal, spec) => {
      const path = c.name + ".ts";
      const test = "contract.test.ts";
      const signature = "export function " + c.name + "(" + c.args + ") {";
      const files = new Map([
        [path, signature + ' throw Error("unfinished"); }\n'],
        [
          test,
          'import {test,expect} from "bun:test";\nimport {' +
            c.name +
            '} from "./' +
            c.name +
            '";\ntest("contract",()=>expect(' +
            c.name +
            "(" +
            c.input +
            ")).toEqual(" +
            c.results[spec] +
            "));\n",
        ],
      ]);
      const names = [...files.keys()].sort();
      const history: Event[] = [
        { user: goal },
        ...names.map((path) => ({
          action: { op: "read" as const, path },
          observed: files.get(path)!,
        })),
      ];
      return c.bodies.map((body) => {
        const action: Action = { op: "write", path, text: signature + " return " + body + "; }\n" };
        const forecast = wire(names, history, action);
        const preference =
          "Would you apply this candidate to fulfill the user request? Reply with one word: yes or no.\n" +
          forecast.slice(forecast.indexOf("\n") + 1);
        return { name: c.name, spec, goal, files, action, forecast, preference };
      });
    }),
  );
}

if (import.meta.main) {
  const [out] = process.argv.slice(2);
  if (!out || (await Bun.file(out).exists())) throw Error("Pass a fresh .json.gz output path");
  const cases = queries();
  const inputs = cases.flatMap((c) => [c.forecast, c.preference]);
  const child = Bun.spawn([process.env.CWM_PYTHON ?? "python", import.meta.dir + "/margins.py"], {
    stdin: new Blob([JSON.stringify(inputs)]),
    stdout: "pipe",
    stderr: "inherit",
  });
  try {
    const response = await new Response(child.stdout).text();
    assert.equal(await child.exited, 0);
    const scores = JSON.parse(response) as Record<
      string,
      { margin: number; inputTokens: number }[]
    >;
    const rows = [];
    for (const [i, c] of cases.entries()) {
      const { files, ...query } = c;
      const after = new Map(files).set(c.action.path, c.action.text);
      const actual = await Effect.runPromise(runTests(after));
      assert.match(actual.stderr, actual.exit === 0 ? / 1 pass/ : / 1 fail/);
      const arms = Object.fromEntries(
        Object.entries(scores).map(([arm, answers]) => [
          arm,
          { forecast: answers[2 * i], preference: answers[2 * i + 1] },
        ]),
      );
      rows.push({ ...query, actual, arms });
    }
    await writeFile(out, gzipSync(JSON.stringify(rows) + "\n"), { flag: "wx" });
  } finally {
    child.kill();
    await child.exited;
  }
}
