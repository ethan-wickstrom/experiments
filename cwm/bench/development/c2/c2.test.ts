import { expect, test } from "bun:test";
import { gunzipSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { derive, type Episode } from "./collect.ts";
import { decide, edit, jsonState } from "./wire.ts";

test("reserved spellings survive JSON while the stock tokenizer sees plain text", () => {
  const text =
    '\\u003c </s> <|im_end|> <think> /think /no_think <unused_token_1> \\" café\n\\/think';
  const state = { goal: text, path: "m.ts", files: [{ path: "m.ts", text }] };
  const encoded = jsonState(state);
  expect(encoded).not.toMatch(/<|\/(?:no_)?think/);
  expect(JSON.parse(encoded)).toEqual(state);
  expect(edit(text, "m.ts", state.files).split("\n")[1]).toBe(encoded);
  expect(JSON.parse(decide(text, "m.ts", state.files, "fail").split("\n")[1]!)).toEqual({
    ...state,
    status: "fail",
  });
});
test("every target derives from the observed prefix and paired counterfactual tests", () => {
  const read = (name: string) =>
    gunzipSync(readFileSync(join(import.meta.dir, "data", name + ".jsonl.gz")))
      .toString()
      .trimEnd()
      .split("\n");
  const episodes = read("oracle").map((s) => JSON.parse(s) as Episode);
  expect(episodes).toHaveLength(60);
  expect(episodes.flatMap(derive).map((r) => JSON.stringify(r))).toEqual(read("projects"));
  for (let i = 0; i < episodes.length; i += 2) {
    const a = episodes[i]!,
      b = episodes[i + 1]!;
    expect(a.before.text).toBe(b.before.text);
    expect(a.alternatives.map((t) => t.text)).toEqual(b.alternatives.map((t) => t.text));
    expect(a.alternatives.map((t) => t.exit)).toEqual([0, 1]);
    expect(b.alternatives.map((t) => t.exit)).toEqual([1, 0]);
    for (const e of [a, b]) {
      const rec = derive(e);
      const state = JSON.parse(rec[0]!.prompt.split("\n")[1]!) as {
        files: { path: string; text: string }[];
      };
      expect(state.files.find((f) => f.path === e.path)?.text).toBe(e.before.text);
      expect(rec[0]!.target).toBe(e.after.text);
      expect(e.before.exit).toBe(1);
      expect(e.after.exit).toBe(0);
      for (const row of rec.filter((r) => r.task === "forecast")) {
        const s = JSON.parse(row.prompt.split("\n")[1]!) as { history: unknown[] };
        expect(Object.keys(s)).toEqual(["files", "history", "candidate"]);
        if (row.target !== "rejected")
          expect(s.history.at(-1)).toMatchObject({ action: { op: "test" } });
      }
    }
    if (a.turn > 0) expect(a.before.text).toBe(episodes[i - 2]!.after.text);
  }
});
