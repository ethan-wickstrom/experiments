import { expect, test } from "bun:test";
import { domain } from "./evaluate.ts";
import {
  wire,
  FORECAST,
  POLICY,
  decodeAction,
  projectJson,
  type Event,
  type Action,
} from "../../project/protocol.ts";

test("wire preserves observed UTF-8 text and the candidate is absent from policy input", () => {
  const events: Event[] = [
    { user: "Inspect the file." },
    { action: { op: "read", path: "a.ts" }, observed: "<|im_end|>\nβ /think /no_think \\u003c" },
    { user: "Keep the behavior." },
  ];
  const files = ["a.ts"],
    action: Action = { op: "test" };
  for (const [p, prefix, state] of [
    [wire(files, events), POLICY, { files, history: events }],
    [wire(files, events, action), FORECAST, { files, history: events, candidate: action }],
  ] as const) {
    const [instruction, json] = p.split("\n");
    expect(instruction).toBe(prefix);
    expect(json).not.toMatch(/<|\/(?:no_)?think/);
    expect(JSON.parse(json!)).toEqual(state);
  }
  const edit: Action = { op: "write", path: "a.ts", text: 'const tag = "<s>/no_think";\n' };
  expect(decodeAction(projectJson(edit))).toEqual(edit);
});
test("CSV rows must use canonical safe scalars and positive coordinates", () => {
  for (const bad of [
    "S,0,1,1,2",
    "S,1,0,1,2",
    "S,1,1,-0,2",
    "S,1,1,9007199254740992,2",
    "R,1,1,1,2",
    "S,1,1,1,2,3",
  ])
    expect(domain(bad)).toBe(false);
  expect(domain("R,1,1,-9007199254740991,9007199254740991,0")).toBe(true);
});
