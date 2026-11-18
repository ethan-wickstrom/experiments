import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir } from "node:fs/promises";
import type { Debugger, Runtime } from "node:inspector";
import { SourceMap } from "node:module";
import { join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { isDeepStrictEqual } from "node:util";
import { parseSync, Visitor } from "oxc-parser";
import { transformSync } from "oxc-transform";
import { WorldModel, readTraces, trace, type Program } from "../../cwm.ts";
import { cases } from "../cases.ts";

type Event =
  | { method: "Debugger.scriptParsed"; params: Debugger.ScriptParsedEventDataType }
  | { method: "Debugger.paused"; params: Debugger.PausedEventDataType }
  | {
      method: "Runtime.getProperties";
      params: { objectId: string };
      response: { result: Runtime.PropertyDescriptor[] };
    };

function rawPauses(jsonl: string, file: string, emittedHash: string) {
  const pauses = [];
  let props = new Map<string, Runtime.PropertyDescriptor[]>();
  let scriptId: string | undefined;
  for (const line of jsonl.trim().split("\n")) {
    const e: Event = JSON.parse(line);
    if (e.method === "Debugger.scriptParsed") {
      assert.equal(e.params.url, "repo:" + file);
      assert.equal(e.params.hash, emittedHash);
      scriptId = e.params.scriptId;
    } else if (e.method === "Debugger.paused") {
      assert.equal(e.params.callFrames[0]!.location.scriptId, scriptId);
      props = new Map();
      pauses.push({ top: e.params.callFrames[0]!, props });
    } else if (e.method === "Runtime.getProperties")
      props.set(e.params.objectId, e.response.result);
  }
  return pauses;
}

const [out] = process.argv.slice(2);
assert(out, "Usage: bun bench/first-write/replay.ts NEW_OUTPUT_DIR");
const root = resolve(out);
await mkdir(root);
const training = join(root, "train.jsonl");
await Bun.write(
  training,
  Bun.gunzipSync(await Bun.file(new URL("train.jsonl.gz", import.meta.url)).bytes()),
);
const engine = fileURLToPath(new URL("../../cwm.ts", import.meta.url));
const sha = async (path: string) =>
  createHash("sha256")
    .update(await Bun.file(path).bytes())
    .digest("hex");
const modelHash = await sha(engine),
  trainHash = await sha(training);
assert.equal(modelHash, "8a46d619c7a46cff8b89d04224c9bca523d9e90de616b0f73f86a65480b31cb0");
assert.equal(trainHash, "666e16d3a9c4c7f62b44de1dd9920e8b91213a026131a319357753adf03eb041");
const train = await Array.fromAsync(readTraces(training));
const model = new WorldModel().fit(train);
const p = [...cases()].find(
  (c) => c.family === "histogram" && c.program.args.join() === "1,-2",
)!.program;
assert(!train.some((t) => Object.hasOwn(t.files, p.entry)));
const original = p.files[p.entry]!;
const node = Bun.which("node");
assert(node);
const runNode = (args: string[], stdin = "", env: Record<string, string> = {}) => {
  const r = Bun.spawnSync([node, ...args], {
    stdin: Buffer.from(stdin),
    stdout: "pipe",
    stderr: "pipe",
    env,
    timeout: 10000,
  });
  assert(r.success, r.stderr.toString() || "Node did not exit successfully");
  return r.stdout.toString();
};
const summary = [];
for (const [name, source] of Object.entries({
  original,
  shifted: "\n\n" + original,
  opposite: original.replace("Math.abs(n)%2", "1-(Math.abs(n)%2)"),
})) {
  const program: Program = { ...p, files: { [p.entry]: source } };
  const dir = join(root, name);
  await mkdir(dir);
  await Bun.write(join(dir, p.entry), source);
  const labeled = await trace(program);
  // Each call has only source and *this* frame; do not pass args or the oracle successor.
  const predictions = labeled.frames.map((f) => model.predict(program.files, f) ?? null);
  const entry = labeled.frames.findIndex((f) => f.stack[0]?.fn === p.fn);
  assert(entry >= 0);
  const rollout = model.rollout(program.files, labeled.frames[entry]!, 32).next();
  const unit = transformSync(p.entry, source, {
    sourceType: "module",
    sourcemap: true,
    typescript: { rewriteImportExtensions: true },
  });
  assert(unit.map && !unit.errors.length);
  const file = p.entry.replace(/\.ts$/, ".js");
  const map = {
    ...unit.map,
    file: p.entry,
    sources: [p.entry],
    sourcesContent: [source],
    sourceRoot: "",
  };
  await Bun.write(join(dir, "emitted.mjs"), unit.code);
  await Bun.write(join(dir, "source.map.json"), JSON.stringify(map));
  const job = {
    entry: file,
    fn: p.fn,
    args: p.args,
    maxFrames: 2048,
    modules: { [file]: { file: p.entry, code: unit.code, map } },
  };
  const log = join(dir, "protocol.jsonl");
  const observed = JSON.parse(
    runNode(
      [
        "--import",
        new URL("record.mjs", import.meta.url).href,
        "--experimental-vm-modules",
        engine,
        "--cwm-engine",
      ],
      JSON.stringify(job),
      { CWM_PROTOCOL_LOG: log },
    ),
  );
  assert.deepEqual(observed, { frames: labeled.frames, outcome: labeled.outcome });
  const plain = JSON.parse(
    runNode([
      "--input-type=module",
      "-e",
      `import {run} from ${JSON.stringify(pathToFileURL(join(dir, p.entry)).href)};console.log(JSON.stringify(run(...${JSON.stringify(p.args)})))`,
    ]),
  );
  assert.deepEqual(labeled.outcome, { kind: "returned", result: { exact: true, value: plain } });
  const pauses = rawPauses(await Bun.file(log).text(), file, await sha(join(dir, "emitted.mjs"))),
    sm = new SourceMap(map);
  assert.equal(pauses.length, labeled.frames.length);
  const spans: { start: number; end: number }[] = [];
  const parsed = parseSync(p.entry, source);
  assert(!parsed.errors.length);
  new Visitor({
    UpdateExpression(n) {
      spans.push({ start: n.start, end: n.end });
    },
  }).visit(parsed.program);
  assert.equal(spans.length, 1);
  const span = spans[0]!;
  const lines = source.split("\n");
  const sites = pauses.map(({ top }, i) => {
    const { lineNumber, columnNumber } = top.location;
    if (top.functionName !== p.fn)
      return { js: [lineNumber + 1, (columnNumber ?? 0) + 1], ts: null, inside: false };
    const s = sm.findEntry(lineNumber, columnNumber ?? 0);
    assert("originalLine" in s);
    const line = s.originalLine + 1,
      column = s.originalColumn + 1;
    assert.deepEqual(labeled.frames[i]!.stack[0], {
      file: p.entry,
      line,
      column,
      fn: top.functionName,
    });
    const offset = lines.slice(0, line - 1).reduce((v, l) => v + l.length + 1, 0) + column - 1;
    return {
      js: [lineNumber + 1, (columnNumber ?? 0) + 1],
      ts: [line, column],
      inside: offset >= span.start && offset < span.end,
    };
  });
  // Last stop inside the first executed update, before returning to the loop header.
  const i = sites.findIndex((s, j) => s.inside && sites[j + 1]?.inside === false);
  assert(i >= entry && i + 1 < pauses.length);
  function evidence(at: number) {
    const { top, props } = pauses[at]!;
    const bindings = top.scopeChain
      .filter((s) => ["block", "local"].includes(s.type))
      .flatMap((s) => props.get(s.object.objectId!) ?? []);
    const ref = bindings.find((d) => d.name === "a")?.value;
    assert(ref?.subtype === "array" && ref.objectId);
    const fields = props.get(ref.objectId)!;
    const get = (key: string) => fields.find((d) => d.name === key)?.value?.value;
    assert.equal(get("length"), 2);
    const array = [get("0"), get("1")];
    const n = bindings.find((d) => d.name === "n")?.value?.value;
    assert.deepEqual(labeled.frames[at]!.locals.a, { exact: true, value: array });
    assert.deepEqual(labeled.frames[at]!.locals.n, { exact: true, value: n });
    return { pause: at, site: sites[at], array, n };
  }
  const before = evidence(i),
    after = evidence(i + 1);
  assert.deepEqual(before.array, [0, 0]);
  assert.equal(before.n, 1);
  assert.deepEqual(after.array, name === "opposite" ? [1, 0] : [0, 1]);
  assert.deepEqual(plain, [1, 1]);
  assert.deepEqual(rollout, { done: true, value: "unseen" });
  const guess = predictions[i],
    next = labeled.frames[i + 1]!;
  const mark = (match: boolean) => (!guess ? "abstained" : match ? "correct" : "wrong");
  const nextFrame = guess && "stack" in guess ? guess : undefined;
  const scores = {
    site: mark(isDeepStrictEqual(nextFrame?.stack, next.stack)),
    array: mark(isDeepStrictEqual(nextFrame?.locals.a, next.locals.a)),
  };
  assert(predictions.every((g) => g === null));
  const last = labeled.frames.at(-1)!;
  assert(
    last.kind === "return" &&
      last.stack.length === 1 &&
      last.stack[0]?.fn === p.fn &&
      last.value?.exact,
  );
  assert.deepEqual(last.value, labeled.outcome.result);
  await Bun.write(join(dir, "trace.json"), JSON.stringify(labeled));
  summary.push({
    name,
    action: source.slice(span.start, span.end),
    entryPause: entry,
    rollout: rollout.value,
    before,
    after,
    oneStepPrediction: guess,
    scores,
    terminalPrediction: predictions.at(-1),
    returnReadout: last.value.value,
    plainNode: plain,
  });
}
const report = {
  modelHash,
  trainHash,
  trainRuns: train.length,
  bun: Bun.version,
  node: runNode(["--version"]).trim(),
  summary,
};
await Bun.write(join(root, "witness.json"), JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report));
