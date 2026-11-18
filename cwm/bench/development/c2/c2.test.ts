import { expect, test } from "bun:test";
import { gunzipSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { derive, type Episode } from "./collect.ts";
import { decide, edit, jsonState } from "./wire.ts";
import { ProjectSession } from "../../../project/agent.ts";
import { wire, type Action } from "../../../project/protocol.ts";
import { workFile } from "../../../project/work.ts";

const read = (name: string) =>
  gunzipSync(readFileSync(join(import.meta.dir, "data", name + ".jsonl.gz")))
    .toString()
    .trimEnd()
    .split("\n");

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

test("production work replays every frozen C2 policy and source row and observed forecast prefix", async () => {
  type Row = { task: string; prompt: string; target: string };
  const rows = read("projects").map((line) => JSON.parse(line) as Row);
  const policy = rows.filter((row) => row.task !== "forecast");
  const forecasts = new Set(rows.filter((row) => row.task === "forecast").map((row) => row.prompt));
  let checked = 0;
  for (const line of read("oracle")) {
    const ep = JSON.parse(line) as Episode;
    const [source, unread, seen, failed, written, passed] = policy.splice(0, 6);
    const expected = [unread!, seen!, failed!, source!, written!, passed!];
    const files = new Map(ep.files.map((f) => [f.path, f.text]));
    const oracle = [ep.before, ep.after];
    function checkForecasts(actions: Action[]) {
      const state = session.state();
      for (const candidate of actions)
        expect(forecasts.delete(wire(state.files, state.history, candidate))).toBe(true);
    }
    const session = new ProjectSession(
      { files },
      async (prompt, limit, _signal, _grammar, verbatim) => {
        const row = expected.shift()!;
        expect(prompt).toBe(row.prompt);
        const payload = row.task === "source";
        expect(limit).toBe(payload ? 384 : 8);
        expect(verbatim).toBe(payload);
        if (row === unread && ep.turn === 0)
          checkForecasts([{ op: "write", path: ep.path, text: ep.after.text }]);
        if (row === failed)
          checkForecasts(ep.alternatives.map(({ text }) => ({ op: "write", path: ep.path, text })));
        checked++;
        return { text: row.target, finish: "stop", tokens: 0, inputTokens: 0 };
      },
      async (snapshot) => {
        const run = oracle.shift()!;
        expect(snapshot.get(ep.path)).toBe(run.text);
        return run;
      },
    );
    session.history.push(...ep.prefix);
    expect((await workFile(session, ep.path, ep.goal)).stop).toBe("done");
    expect(files.get(ep.path)).toBe(ep.after.text);
    expect(expected).toHaveLength(0);
    expect(oracle).toHaveLength(0);
  }
  expect(checked).toBe(360);
  expect(policy).toHaveLength(0);
  expect(forecasts.size).toBe(0);
});
