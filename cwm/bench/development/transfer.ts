/** Five exploratory transfer cases, one full and one delta query each. No x/y training grammar. */
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { isDeepStrictEqual as equal } from "node:util";
import { gunzipSync, gzipSync } from "node:zlib";
import { trace, type Frame, type Observation, type Program, type Trace } from "../../cwm.ts";

const specs = [
  {
    id: "unicode-write",
    source: 'export function run(label: string) {\n  label += "雪";\n  return 0;\n}',
    args: ["🦊"],
    line: 2,
  },
  {
    id: "alias-write",
    source:
      "export function run(v: number[]) {\n  const left = v;\n  const right = left;\n  left[0] = 7;\n  return right[0];\n}",
    args: [[2]],
    line: 4,
  },
  {
    id: "caught-throw",
    source:
      "export function run(tag: string) {\n  try {\n    throw tag;\n  } catch (fault) {\n    return fault;\n  }\n}",
    args: ["cold"],
    line: 3,
  },
  {
    id: "loop-back",
    source:
      "export function run(count: number) {\n  let sum = 1;\n  while (count > 0) {\n    sum *= 2;\n    count -= 1;\n  }\n  return sum;\n}",
    args: [3],
    line: 5,
  },
  {
    id: "await-resume",
    source:
      'export async function run(word: string) {\n  word = await (word + "Ω");\n  return word;\n}',
    args: ["hi"],
    line: 2,
  },
];
type Spec = (typeof specs)[number];
type Tape = { id: string; trace: Trace } | { id: string; error: string };
const tapeUrl = new URL("./transfer.jsonl.gz", import.meta.url);

function program(s: Spec): Program {
  return { entry: "probe.ts", files: { "probe.ts": s.source }, fn: "run", args: s.args };
}

// Boundary selection uses only the first step at a predeclared site, never the local values.
function boundary(s: Spec, run: Trace) {
  const inRun = (f: Frame) => f.stack[0]?.fn === "run" && f.stack[0].file === run.entry;
  const i = run.frames.findIndex(
    (f) => inRun(f) && f.kind === "step" && f.stack[0]!.line === s.line,
  );
  if (i < 0) throw Error("Current step missing");
  const current = run.frames[i]!;
  const next =
    s.id === "await-resume"
      ? run.frames.slice(i + 1).find((f) => inRun(f) && f.stack[0]!.line !== s.line)
      : (run.frames[i + 1] ?? run.outcome);
  if (!next) throw Error("No post-await function pause");
  return { current, next };
}

async function collect(out: string) {
  if (
    Bun.version !== "1.4.4" ||
    Bun.spawnSync(["node", "--version"]).stdout.toString().trim() !== "v24.19.0"
  )
    throw Error("Recollect with Bun 1.4.4 and Node 24.19.0");
  const rows: Tape[] = [];
  for (const s of specs) {
    try {
      rows.push({ id: s.id, trace: await trace(program(s)) });
    } catch (cause) {
      rows.push({ id: s.id, error: String(cause) });
    }
  }
  await writeFile(out, gzipSync(rows.map((r) => JSON.stringify(r)).join("\n") + "\n"), {
    flag: "wx",
  });
}

type Fields = Record<string, unknown>;
function fields(x: unknown): x is Fields {
  return typeof x === "object" && x !== null && !Array.isArray(x);
}

// A missing field is distinct from a Snapshot whose value is null or inexact.
// Null at a field or local-name position deletes that key; snapshots are always whole objects.
function diff(a: Fields, b: Fields) {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  return Object.fromEntries(
    [...keys].filter((k) => !equal(a[k], b[k])).map((k) => [k, Object.hasOwn(b, k) ? b[k] : null]),
  );
}
function delta(current: Frame, next: Observation) {
  const patch = diff(current, next);
  if (Object.hasOwn(patch, "locals") && "locals" in next)
    patch.locals = diff(current.locals, next.locals);
  return patch;
}
function apply(a: Fields, changes: Fields): Fields {
  const merged = new Map(Object.entries(a));
  for (const [k, v] of Object.entries(changes)) {
    if (v === null) merged.delete(k);
    else merged.set(k, v);
  }
  return Object.fromEntries(merged);
}
function expand(current: Frame, patch: unknown) {
  if (!fields(patch)) throw Error("Expected a patch object");
  const root = apply(current, patch);
  if (fields(patch.locals)) root.locals = apply(current.locals, patch.locals);
  return root;
}

type Format = "full" | "delta";
const formats: Format[] = ["full", "delta"];
const task = (s: Spec) =>
  s.id === "await-resume"
    ? "Predict the first later V8 observation in run on a different line after await."
    : "Predict the immediately next V8 observation.";
function prompt(s: Spec, current: Frame, format: Format) {
  const answer =
    format === "full"
      ? "Return the complete observation as one JSON object."
      : "Return a JSON patch object. Omit unchanged fields. At locals, include only changed names. Null deletes a field or local name. Replace other fields and individual snapshots whole. An empty object means no changes.";
  return (
    task(s) + " " + answer + "\n" + JSON.stringify({ file: "probe.ts", source: s.source, current })
  );
}

type Completion = { text: string; finish: string; tokens: number; inputTokens: number };
type Generate = (prompt: string, limit: number) => Promise<Completion>;
type Status =
  | "exact"
  | "wrong"
  | "invalidJsonOrPatch"
  | "incomplete"
  | "unsupported"
  | "endpointError";
const tally = () => ({
  exact: 0,
  wrong: 0,
  invalidJsonOrPatch: 0,
  incomplete: 0,
  unsupported: 0,
  endpointError: 0,
  promptTokens: 0,
  generationTokens: 0,
  goldBytes: 0,
  goldTokens: 0,
});
const errorText = (e: unknown) => (e instanceof Error ? e.message : String(e));
const maxTokens = 128;

// tokenizers 0.22.1 encode(gold, add_special_tokens=False), openbmb/MiniCPM5-1B
// ac83f813ba7da263c51a9f3ec37c2072597e54af. Each gold is JSON.stringify(next or delta).
const goldTokens: Record<string, [number, number]> = {
  "unicode-write": [40, 36],
  "alias-write": [57, 53],
  "caught-throw": [47, 15],
  "loop-back": [47, 33],
  "await-resume": [38, 34],
};

export async function evaluateTransfer(generate: Generate) {
  const bytes = gunzipSync(await readFile(tapeUrl));
  if (
    createHash("sha256").update(bytes).digest("hex") !==
    "eba0968210d9bd23b7bb79489fe05d19856a1249772188469680cdd4501dfaa6"
  )
    throw Error("Frozen oracle observations changed");
  const tape = bytes
    .toString()
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line) as Tape);
  if (tape.length !== specs.length) throw Error("Incomplete frozen tape");
  const totals = { full: tally(), delta: tally() };
  const rows = [];
  for (const [i, s] of specs.entries()) {
    const r = tape[i]!;
    if (r.id !== s.id) throw Error("Unexpected tape id");
    let pair;
    try {
      if ("error" in r) throw Error(r.error);
      const { frames: _frames, outcome: _outcome, ...p } = r.trace;
      if (!equal(p, program(s))) throw Error("Unexpected source or invocation");
      pair = boundary(s, r.trace);
    } catch (cause) {
      totals.full.unsupported++;
      totals.delta.unsupported++;
      rows.push({ id: s.id, status: "unsupported", error: errorText(cause) });
      continue;
    }
    const { current, next } = pair;
    const compact = delta(current, next);
    if (!equal(expand(current, compact), next)) throw Error("Gold delta lost observation fields");
    for (const format of formats) {
      const request = prompt(s, current, format);
      const gold = JSON.stringify(format === "full" ? next : compact);
      const referenceTokens = goldTokens[s.id]![format === "full" ? 0 : 1];
      const referenceBytes = Buffer.byteLength(gold);
      totals[format].goldTokens += referenceTokens;
      totals[format].goldBytes += referenceBytes;
      let completion: Completion | undefined;
      let prediction: unknown;
      let status: Status;
      let error: string | undefined;
      try {
        completion = await generate(request, maxTokens);
        totals[format].promptTokens += completion.inputTokens;
        totals[format].generationTokens += completion.tokens;
        if (completion.finish !== "stop") status = "incomplete";
        else {
          try {
            const parsed: unknown = JSON.parse(completion.text);
            prediction = format === "delta" ? expand(current, parsed) : parsed;
            status = equal(prediction, next) ? "exact" : "wrong";
          } catch (cause) {
            status = "invalidJsonOrPatch";
            error = errorText(cause);
          }
        }
      } catch (cause) {
        status = "endpointError";
        error = errorText(cause);
      }
      totals[format][status]++;
      rows.push({
        id: s.id,
        format,
        request,
        promptBytes: Buffer.byteLength(request),
        gold,
        goldBytes: referenceBytes,
        goldTokens: referenceTokens,
        current,
        expected: next,
        completion,
        prediction,
        status,
        error,
      });
    }
  }
  return { cases: specs.length, maxTokens, totals, rows };
}

// Stock single-user OpenAI chat endpoint; same options and usage fields as the project agent.
function endpoint(url: string, model: string): Generate {
  return async (request, limit) => {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: request }],
        max_tokens: limit,
        temperature: 0,
        chat_template_kwargs: { enable_thinking: false },
        stream: false,
      }),
      signal: AbortSignal.timeout(180_000),
    });
    if (!r.ok) throw Error("Model HTTP " + r.status);
    const data = (await r.json()) as {
      usage?: { prompt_tokens?: number; completion_tokens?: number };
      choices?: { finish_reason?: string; message?: { content?: string } }[];
    };
    const choice = data.choices?.[0],
      usage = data.usage;
    if (
      typeof choice?.message?.content !== "string" ||
      typeof choice.finish_reason !== "string" ||
      typeof usage?.prompt_tokens !== "number" ||
      typeof usage.completion_tokens !== "number"
    )
      throw Error("Incomplete completion or missing usage");
    return {
      text: choice.message.content,
      finish: choice.finish_reason,
      tokens: usage.completion_tokens,
      inputTokens: usage.prompt_tokens,
    };
  };
}

if (import.meta.main) {
  const [url, model, out] = process.argv.slice(2);
  if (url === "collect" && model && !out) await collect(model);
  else if (url && model && out) {
    if (await Bun.file(out).exists()) throw Error("Use a fresh output path");
    const report = await evaluateTransfer(endpoint(url, model));
    await writeFile(out, JSON.stringify({ model, ...report }, null, 2) + "\n", { flag: "wx" });
    console.log(JSON.stringify(report.totals));
  } else throw Error("Usage: bun transfer.ts URL MODEL FRESH.json | collect FRESH.jsonl.gz");
}
