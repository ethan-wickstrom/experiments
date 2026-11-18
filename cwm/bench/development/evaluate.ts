import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { createInterface } from "node:readline";
import { Readable } from "node:stream";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { Effect, Schema } from "effect";
import { readTraces, type Frame, type Trace, type Snapshot } from "../../cwm.ts";

const root = import.meta.dir;
const controls = [
  ["What TypeScript primitive type is the expression 7 < 9? Reply with just the type.", "boolean"],
  [
    'In JavaScript, what string does "café".slice(0, 3) produce? Reply with that string only.',
    "caf",
  ],
  ["In TypeScript, what number does [2, 4, 6].length return? Reply with just the number.", "3"],
] as const;
function scalar(x?: Snapshot) {
  assert(
    x?.exact &&
      typeof x.value === "number" &&
      Number.isSafeInteger(x.value) &&
      !Object.is(x.value, -0),
  );
  return x.value;
}
function project(t: Trace, f: Frame) {
  const [s] = f.stack;
  assert(s && f.stack.length === 1 && s.fn === t.fn && s.file === t.entry);
  assert.deepEqual(Object.keys(f.locals).sort(), ["x", "y"]);
  const fields = [
    f.kind === "step" ? "S" : "R",
    s.line,
    s.column,
    scalar(f.locals.x),
    scalar(f.locals.y),
  ];
  if (f.kind !== "step") {
    assert.equal(f.kind, "return");
    fields.push(scalar(f.value));
  }
  const row = fields.join(",");
  assert(domain(row));
  return row;
}
export function domain(output: string) {
  const [kind, ...s] = output.split(",");
  return (
    ((kind === "S" && s.length === 4) || (kind === "R" && s.length === 5)) &&
    s.every((x) => Number.isSafeInteger(Number(x)) && String(Number(x)) === x) &&
    Number(s[0]) > 0 &&
    Number(s[1]) > 0
  );
}
function spawnModel(arm: string) {
  const proc = Bun.spawn(
    [process.env.CWM_PYTHON ?? "python", "-u", join(root, "forward.py"), arm],
    {
      cwd: root,
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    },
  );
  const stdout = createInterface({ input: Readable.from(proc.stdout), crlfDelay: Infinity });
  const lines = stdout[Symbol.asyncIterator]();
  const request = async (body: object): Promise<unknown> => {
    await proc.stdin.write(JSON.stringify(body) + "\n");
    await proc.stdin.flush();
    const next = await lines.next();
    if (next.done) throw Error("Tensor backend stopped: " + (await proc.exited));
    return JSON.parse(next.value);
  };
  return {
    async generate(prompts: string[]) {
      const answers = Schema.decodeUnknownSync(Schema.Array(Schema.String))(
        await request({ prompts }),
      );
      assert.equal(answers.length, prompts.length);
      return answers;
    },
    async loss(rows: string[][]) {
      return Schema.decodeUnknownSync(Schema.Tuple([Schema.Number, Schema.Int]))(
        await request({ loss_rows: rows }),
      );
    },
    async close() {
      stdout.close();
      await proc.stdin.end();
      proc.kill();
      await proc.exited;
    },
  };
}
async function evaluate(arm: string, model: ReturnType<typeof spawnModel>) {
  const path = join(root, "data", "retention.jsonl.gz");
  const pins = JSON.parse(await readFile(join(root, "artifacts.json"), "utf8")) as {
    retention_uncompressed: string;
  };
  const digest = createHash("sha256")
    .update(gunzipSync(await readFile(path)))
    .digest("hex");
  assert.equal(digest, pins.retention_uncompressed);
  const fixed = join(root, "../recurrent/data/fixed.jsonl.gz");
  const trainingSources = new Set(
    (await Array.fromAsync(readTraces(fixed))).map((t) => t.files[t.entry]),
  );
  const tape = await Array.fromAsync(readTraces(path));
  const template = (await readFile(join(root, "../minicpm/resume.txt"), "utf8")).trimEnd();
  const prompt = (source: string, current: string) =>
    template.replace(/\{(source|current)\}/g, (_, f: string) =>
      f === "source" ? source : current,
    );
  const seqs = tape.map((t) => {
    const source = t.files[t.entry]!;
    assert(!trainingSources.has(source));
    assert.equal(t.frames[0]?.stack[0]?.fn, "");
    const [entry, ...gold] = t.frames.slice(1).map((f) => project(t, f));
    assert(entry && gold.length > 0);
    return { args: t.args, source, entry, gold, predictions: [] as string[], stop: "" };
  });
  const rows = seqs.flatMap((s) =>
    s.gold.map((target, i) => [s.source, i ? s.gold[i - 1]! : s.entry, target]),
  );
  const predictions = [];
  const counts = {
    rows: rows.length,
    exact: 0,
    format_domain: 0,
    inside_source: 0,
    site_event: 0,
    locals: 0,
    changed: 0,
    changed_locals_correct: 0,
  };
  let loss = 0,
    tokens = 0;
  for (let i = 0; i < rows.length; i += 6) {
    const batch = rows.slice(i, i + 6);
    const outputs = await model.generate(batch.map((r) => prompt(r[0]!, r[1]!)));
    const [nll, n] = await model.loss(batch);
    loss += nll;
    tokens += n;
    for (const [j, row] of batch.entries()) {
      const [source, current, target] = row as [string, string, string];
      const output = outputs[j]!,
        valid = domain(output),
        fields = output.split(",");
      const gold = target.split(",");
      const rightLocals = valid && fields.slice(3, 5).join(",") === gold.slice(3, 5).join(",");
      const changed = gold.slice(3, 5).join(",") !== current.split(",").slice(3, 5).join(",");
      counts.exact += Number(output === target);
      counts.format_domain += Number(valid);
      counts.inside_source += Number(
        valid && Number(fields[2]) <= (source.split("\n")[Number(fields[1]) - 1]?.length ?? 0),
      );
      counts.site_event += Number(
        valid && fields.slice(0, 3).join(",") === gold.slice(0, 3).join(","),
      );
      counts.locals += Number(rightLocals);
      counts.changed += Number(changed);
      counts.changed_locals_correct += Number(changed && rightLocals);
      predictions.push({ source, current, target, generated: output });
    }
  }
  for (let round = 0; round < 16; round++) {
    const live = seqs.filter((s) => !s.stop);
    if (!live.length) break;
    const outputs = await model.generate(
      live.map((s) => prompt(s.source, s.predictions.at(-1) ?? s.entry)),
    );
    for (const [i, s] of live.entries()) {
      const output = outputs[i]!;
      if (!domain(output)) s.stop = "outside format/numeric domain";
      else if (output.startsWith("R,")) s.stop = "predicted return";
      else if (output === s.entry || s.predictions.includes(output))
        s.stop = "repeated predicted state";
      s.predictions.push(output);
    }
  }
  const rollouts = seqs.map((s) => {
    let prefix = 0;
    while (prefix < s.gold.length && s.predictions[prefix] === s.gold[prefix]) prefix++;
    return {
      ...s,
      stop: s.stop || "budget",
      prefix,
      exact: prefix === s.gold.length && prefix === s.predictions.length,
    };
  });
  const answers = await model.generate(controls.map((c) => c[0]));
  return {
    arm,
    retention: digest,
    transitions: { counts, nll: loss / tokens, target_tokens: tokens, predictions },
    rollouts,
    short_answers: controls.map(([p, target], i) => ({
      prompt: p,
      target,
      generated: answers[i],
      exact: answers[i] === target,
    })),
  };
}
if (import.meta.main) {
  const arm = process.argv[2];
  assert(arm && ["A", "B", "C"].includes(arm));
  const controller = new AbortController();
  process.once("SIGINT", () => controller.abort());
  process.once("SIGTERM", () => controller.abort());
  const result = await Effect.runPromise(
    Effect.acquireUseRelease(
      Effect.sync(() => spawnModel(arm)),
      (m) => Effect.tryPromise(() => evaluate(arm, m)),
      (m) => Effect.promise(() => m.close()),
    ),
    { signal: controller.signal },
  );
  console.log(JSON.stringify(result));
}
