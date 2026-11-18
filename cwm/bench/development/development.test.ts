import { expect, test } from "bun:test";
import { domain } from "./evaluate.ts";
import { wire, FORECAST, POLICY, type Event, type Action } from "./contract.ts";

test("wire preserves observed UTF-8 text and the candidate is absent from policy input", () => {
  const events: Event[] = [
    { user: "Inspect the file." },
    { action: { op: "read", path: "a.ts" }, observed: "<x>\nβ\n" },
    { user: "Keep the behavior." },
  ];
  const files = ["a.ts"],
    action: Action = { op: "test" };
  expect(wire(files, events)).toBe(POLICY + "\n" + JSON.stringify({ files, history: events }));
  expect(wire(files, events, action)).toBe(
    FORECAST + "\n" + JSON.stringify({ files, history: events, candidate: action }),
  );
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
