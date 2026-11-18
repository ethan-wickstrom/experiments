/** Offline transcript audit. The hidden fixture is read only by this post-run verifier. */
import { strict as assert } from "node:assert";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import type { evaluateSplices } from "../splice-evaluate.ts";
import { spliceHeld } from "../splice-held.ts";
import { ProjectSession } from "../../../project/agent.ts";
import { spliceFile, spliceSource, visiblePass } from "../../../project/splice.ts";

type Run = Awaited<ReturnType<typeof evaluateSplices>>;
for (const [arm, mode] of [
  ["C2", "feedback"],
  ["C2", "no-feedback"],
  ["A", "feedback"],
  ["B2", "feedback"],
] as const) {
  const path = new URL("./" + arm + "-" + mode + ".json.gz", import.meta.url);
  const raw = JSON.parse(gunzipSync(await readFile(path)).toString()) as {
    mode: string;
    runs: Run[];
  };
  assert.equal(raw.mode, mode);
  assert.deepEqual(
    raw.runs.map((r) => r.id),
    spliceHeld.map((f) => f.id),
  );
  for (const [i, project] of raw.runs.entries()) {
    const f = spliceHeld[i]!;
    const goals: string[] = [];
    assert.equal(project.turns.length, f.turns.length);
    let files = { ...f.files };
    for (const [n, turn] of project.turns.entries()) {
      const spec = f.turns[n]!;
      const path = spec.path;
      Object.assign(files, spec.visible);
      goals.push(spec.goal);
      assert.deepEqual(turn.before, files);
      assert.equal(turn.goal, spec.goal);
      assert.equal(turn.path, path);
      assert.equal(turn.trials.length, 8);
      assert.equal(turn.candidates.length, turn.trials.length);
      // Replay the production site menu and reply decoder from raw generations.
      // Only recorded visible observations may advance the search.
      let calls = 0;
      const runs = [
        turn.baseline,
        ...turn.trials.filter((t) => t.status === "tested").map((t) => t.run!),
      ];
      if (turn.verification) runs.push(turn.verification);
      const replay = new ProjectSession(
        { files: new Map(Object.entries(files)) },
        async (prompt, _limit, _signal, _grammar, _verbatim, sampling) => {
          const trial = turn.trials[calls++]!;
          assert.equal(prompt, trial.request);
          assert.deepEqual(sampling, trial.sampling);
          assert.ok(trial.reply);
          return trial.reply;
        },
        async () => {
          const run = runs.shift();
          assert.ok(run);
          return run;
        },
      );
      for (const user of goals.slice(0, -1)) replay.history.push({ user });
      const replayed = await spliceFile(replay, path, spec.goal, { feedback: mode === "feedback" });
      assert.equal(calls, turn.trials.length);
      assert.equal(runs.length, 0);
      for (const [j, trial] of replayed.trials.entries()) {
        assert.deepEqual({ ...trial, elapsedMs: 0 }, { ...turn.trials[j], elapsedMs: 0 });
      }
      const firstDraft = turn.trials.slice(0, 4).find((t) => t.status === "tested");
      const winner = turn.trials.find((t) => t.status === "tested" && visiblePass(t.run!));
      assert.equal(turn.selected, winner?.index ?? null);
      const status = [];
      for (const [j, t] of turn.trials.entries()) {
        const state = JSON.parse(t.request.slice(t.request.indexOf("\n") + 1));
        const parent = j >= 4 ? firstDraft : undefined;
        const source = parent?.text ?? files[path]!;
        const run = parent?.run ?? turn.baseline;
        assert.equal(t.index, j);
        assert.equal(t.parent, parent?.index ?? null);
        assert.deepEqual(state.files, { ...files, [path]: source });
        assert.deepEqual(state.requests, goals);
        assert.equal(state.path, path);
        assert.ok(
          f.turns.every((spec) => !t.request.includes(JSON.stringify(spec.accept).slice(1, -1))),
        );
        const diagnostic =
          mode === "feedback" && j >= 4 && !visiblePass(run)
            ? { exit: run.exit, stderr: run.stderr.slice(-1200), stdout: run.stdout.slice(-200) }
            : undefined;
        assert.deepEqual(state.diagnostic, diagnostic);
        if (t.text !== undefined)
          assert.equal(t.text, spliceSource(path, source, t.site!, t.replacement!));
        const g = turn.candidates[j]!;
        assert.equal(g.index, j);
        assert.equal(g.hidden?.length ?? 0, t.text !== undefined ? n + 1 : 0);
        assert.equal(g.pass, !!t.run && visiblePass(t.run) && !!g.hidden?.every((h) => h.pass));
        for (const h of g.hidden ?? []) assert.equal(h.pass, visiblePass(h.run));
        status.push({
          n: j + 1,
          status: t.status,
          visible: t.run ? visiblePass(t.run) : null,
          hidden: g.hidden?.map((h) => h.pass),
          pass: g.pass,
        });
      }
      if (winner) files = { ...files, [path]: winner.text! };
      assert.deepEqual(turn.after, files);
      assert.equal(turn.hidden.length, n + 1);
      for (const h of turn.hidden) assert.equal(h.pass, visiblePass(h.run));
      assert.equal(turn.pass, visiblePass(turn.visible) && turn.hidden.every((h) => h.pass));
      console.log(
        JSON.stringify({
          arm,
          mode,
          project: f.id,
          turn: n + 1,
          pass: turn.pass,
          selected: turn.selected,
          status,
        }),
      );
    }
  }
}
