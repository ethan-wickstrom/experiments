import { once } from "node:events";
import { writeSync } from "node:fs";
import type { Debugger, Runtime } from "node:inspector";
import { Session } from "node:inspector/promises";
import { SourceMap, type SourceMapPayload } from "node:module";
import { posix } from "node:path";
import { fileURLToPath } from "node:url";
import { isDeepStrictEqual } from "node:util";
import { json } from "node:stream/consumers";
import { Readable } from "node:stream";
import { createInterface } from "node:readline";
import vm from "node:vm";
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";
import { LuDecomposition, Matrix, SingularValueDecomposition } from "ml-matrix";
import * as Schema from "effect/Schema";
import * as Struct from "effect/Struct";

function mutableStruct<const Fields extends Schema.Struct.Fields>(fields: Fields) {
  return Schema.Struct(fields).mapFields(Struct.map(Schema.mutableKey));
}

const snapshotSchema = mutableStruct({ value: Schema.MutableJson, exact: Schema.Boolean });
const coordinate = Schema.Int.check(Schema.isGreaterThan(0));
const siteSchema = mutableStruct({
  file: Schema.String,
  line: coordinate,
  column: coordinate,
  fn: Schema.String,
});
const frameSchema = mutableStruct({
  kind: Schema.Literals(["step", "return", "exception"]),
  stack: Schema.mutable(Schema.Array(siteSchema)).check(Schema.isMinLength(1)),
  locals: Schema.Record(Schema.String, Schema.mutableKey(snapshotSchema)),
  value: Schema.optional(snapshotSchema),
}).check(
  Schema.makeFilter(
    (f) => (f.kind === "step") === (f.value === undefined) || "Invalid event payload",
  ),
);
const programSchema = mutableStruct({
  files: Schema.Record(Schema.String, Schema.mutableKey(Schema.String)),
  entry: Schema.String,
  fn: Schema.String,
  args: Schema.mutable(Schema.Array(Schema.MutableJson)),
});
const executionSchema = mutableStruct({
  frames: Schema.mutable(Schema.Array(frameSchema)),
  outcome: mutableStruct({ kind: Schema.Literals(["returned", "threw"]), result: snapshotSchema }),
});
const traceSchema = Schema.Struct({ ...programSchema.fields, ...executionSchema.fields });
const strict = { onExcessProperty: "error" } as const;
const decodeProgram = Schema.decodeUnknownSync(programSchema, strict);
const decodeExecution = Schema.decodeUnknownSync(Schema.fromJsonString(executionSchema), strict);
export type Json = Schema.MutableJson;
export type Snapshot = typeof snapshotSchema.Type;
export type Site = typeof siteSchema.Type;
export type Frame = typeof frameSchema.Type;
export type Program = typeof programSchema.Type;
export type Execution = typeof executionSchema.Type;
export type Trace = typeof traceSchema.Type;
interface Compiled {
  file: string;
  code: string;
  map: SourceMapPayload;
}
interface Job {
  modules: Record<string, Compiled>;
  entry: string;
  fn: string;
  args: Json[];
  maxFrames: number;
}

async function properties(session: Session, ref: Runtime.RemoteObject) {
  if (!ref.objectId) throw new Error("Inspector did not supply an object handle");
  const reply = await session.post("Runtime.getProperties", {
    objectId: ref.objectId,
    ownProperties: true,
  });
  if (reply.exceptionDetails) throw new Error("Inspector could not read properties");
  return reply.result;
}

// Read debugger descriptors, never evaluate guest expressions or call toJSON/getters.
async function snapshot(session: Session, root?: Runtime.RemoteObject): Promise<Snapshot> {
  let exact = true;
  let remaining = 256;
  function omitted(reason: string) {
    exact = false;
    return `<${reason}>`;
  }
  async function read(ref: Runtime.RemoteObject | undefined, depth: number): Promise<Json> {
    if (!ref) return omitted("unavailable");
    if (--remaining < 0 || depth > 6) return omitted("limit");
    if (ref.unserializableValue) return omitted(ref.unserializableValue);
    if (ref.subtype === "null") return null;
    if (ref.type === "string" && ref.value.length > 4096) return omitted("long string");
    if (["boolean", "number", "string"].includes(ref.type)) return ref.value;
    const array = ref.subtype === "array";
    if (!array && (ref.subtype || ref.className !== "Object")) {
      const label = ref.subtype === "error" ? ref.description?.split("\n", 1)[0] : undefined;
      return omitted(label?.slice(0, 512) ?? ref.subtype ?? ref.className ?? ref.type);
    }
    const props = await properties(session, ref);
    if (array) {
      const length: number = props.find((p) => p.name === "length")?.value?.value;
      if (!Number.isSafeInteger(length) || length > remaining) return omitted("array limit");
      const indices = new Map(props.map((p) => [p.name, p]));
      const values: Json[] = [];
      for (let i = 0; i < length; i++)
        values.push(await read(indices.get(String(i))?.value, depth + 1));
      if (props.length !== length + 1) exact = false;
      return values;
    }
    const fields: Record<string, Json> = Object.create(null);
    for (const p of props) {
      if (remaining <= 0) {
        exact = false;
        break;
      }
      if (p.symbol || !p.enumerable) {
        exact = false;
        continue;
      }
      fields[p.name] = await read(p.value, depth + 1);
    }
    return fields;
  }
  const value = await read(root, 0);
  return { value, exact };
}

const completionScript = "cwm:completion";

async function observe(job: Job) {
  const port = parentPort!;
  const finished = once(port, "message"); // Keep the worker alive while the main isolate pauses.
  const session = new Session();
  session.connectToMainThread();
  const scripts = new Map<string, { file: string; map: SourceMap }>();
  let completionId: string | undefined;
  session.on("Debugger.scriptParsed", ({ params }) => {
    if (params.url === completionScript) completionId = params.scriptId;
    if (!params.url.startsWith("repo:")) return;
    const unit = job.modules[params.url.slice(5)];
    if (unit) scripts.set(params.scriptId, { file: unit.file, map: new SourceMap(unit.map) });
  });
  function site(frame: Debugger.CallFrame): Site | undefined {
    const { scriptId, lineNumber, columnNumber } = frame.location;
    const script = scripts.get(scriptId);
    if (!script) return;
    const entry = script.map.findEntry(lineNumber, columnNumber ?? 0);
    if (!("originalLine" in entry) || !entry.originalSource) return;
    return {
      file: script.file,
      line: entry.originalLine + 1,
      column: entry.originalColumn + 1,
      fn: frame.functionName,
    };
  }
  const frames: Frame[] = [];
  let result: Snapshot | undefined;
  async function paused(p: Debugger.PausedEventDataType) {
    const top = p.callFrames[0]!;
    if (top.location.scriptId === completionId) {
      const bindings = await properties(session, top.scopeChain[0]!.object);
      result = await snapshot(session, bindings.find((v) => v.name === "result")?.value);
    } else if (site(top)) {
      if (frames.length >= job.maxFrames) throw new Error("Trace frame limit exceeded");
      const locals: Frame["locals"] = Object.create(null);
      for (const scope of top.scopeChain) {
        if (!["block", "local", "closure", "catch"].includes(scope.type)) continue;
        for (const binding of await properties(session, scope.object)) {
          if (!Object.hasOwn(locals, binding.name))
            locals[binding.name] = await snapshot(session, binding.value);
        }
      }
      const exception = p.reason === "exception" || p.reason === "promiseRejection";
      const returned = top.returnValue;
      const frame: Frame = {
        kind: exception ? "exception" : returned ? "return" : "step",
        stack: p.callFrames.map(site).filter((s) => s !== undefined),
        locals,
      };
      if (exception || returned)
        frame.value = await snapshot(
          session,
          exception ? (p.data as Runtime.RemoteObject) : returned,
        );
      frames.push(frame);
    }
    await session.post("Debugger.resume");
  }
  session.on("Debugger.paused", ({ params }) => {
    void paused(params).catch((error) => {
      // Neither worker stdio nor a port message can rely on a blocked debuggee's event loop.
      try {
        writeSync(2, String(error) + "\n");
      } finally {
        process.kill(process.pid, "SIGKILL");
      }
    });
  });
  try {
    await session.post("Debugger.enable");
    for (const scriptId of scripts.keys()) {
      const { locations } = await session.post("Debugger.getPossibleBreakpoints", {
        start: { scriptId, lineNumber: 0 },
      });
      for (const location of locations) await session.post("Debugger.setBreakpoint", { location });
    }
    await session.post("Debugger.setPauseOnExceptions", { state: "all" });
    port.postMessage("ready");
    await finished;
    if (!result) throw new Error("Execution completed without a debugger result");
    port.postMessage({ frames, result });
  } finally {
    session.disconnect();
    port.close();
  }
}

async function execute(job: Job): Promise<Execution> {
  const context = vm.createContext(Object.create(null), {
    codeGeneration: { strings: false, wasm: false },
  });
  const modules = new Map(
    Object.entries(job.modules).map(([name, unit]) => [
      name,
      new vm.SourceTextModule(unit.code, { context, identifier: "repo:" + name }),
    ]),
  );
  const entry = modules.get(job.entry)!;
  await entry.link((path, parent) => {
    const name = posix.join(posix.dirname(parent.identifier.slice(5)), path);
    const module = modules.get(name);
    if (!module || !(path.startsWith("./") || path.startsWith("../")))
      throw new Error(`Not a repository import: ${path}`);
    return module;
  });
  const complete = vm.compileFunction("debugger;", ["result"], {
    parsingContext: context,
    filename: completionScript,
  });
  const args = vm.runInContext(`JSON.parse(${JSON.stringify(JSON.stringify(job.args))})`, context);
  const worker = new Worker(new URL(import.meta.url), { workerData: { cwmObserver: true, job } });
  try {
    const [ready] = await once(worker, "message");
    if (ready !== "ready") throw new Error("Observer failed to initialize");
    const report = once(worker, "message");
    let kind: Execution["outcome"]["kind"] = "returned";
    let value: unknown;
    // Link/configuration errors are not observations of a guest exception.
    if (!Object.getOwnPropertyNames(entry.namespace).includes(job.fn))
      throw new Error(`Missing export: ${job.fn}`);
    try {
      await entry.evaluate();
    } catch (error) {
      kind = "threw";
      value = error;
    }
    if (kind !== "threw") {
      const fn = (entry.namespace as Record<string, unknown>)[job.fn];
      if (typeof fn !== "function") throw new Error(`Export is not callable: ${job.fn}`);
      try {
        value = await Reflect.apply(fn, undefined, args);
      } catch (error) {
        kind = "threw";
        value = error;
      }
    }
    complete(value);
    worker.postMessage("finished");
    const [answer] = await report;
    return { frames: answer.frames, outcome: { kind, result: answer.result } };
  } finally {
    await worker.terminate();
  }
}

/** Execute a fresh, trusted, closed ESM repository. Never train on a failed collection. */
export async function trace(
  program: Program,
  { maxFrames = 2048, timeoutMs = 10000 } = {},
): Promise<Trace> {
  const decoded = decodeProgram(program);
  if (!Object.hasOwn(decoded.files, decoded.entry)) throw new Error("Entry file is missing");
  const args: Json[] = JSON.parse(JSON.stringify(decoded.args));
  if (!isDeepStrictEqual(args, program.args)) {
    throw new Error("Expected losslessly JSON-serializable arguments");
  }
  program = { ...decoded, args };
  if (![timeoutMs, maxFrames].every((n) => Number.isSafeInteger(n) && n > 0))
    throw new Error("Expected positive limits");
  const { transformSync } = await import("oxc-transform");
  const { parseSync } = await import("oxc-parser");
  const modules: Job["modules"] = Object.create(null);
  for (const [file, source] of Object.entries(program.files)) {
    if (
      !file.endsWith(".ts") ||
      file.endsWith(".d.ts") ||
      file.startsWith("/") ||
      file.startsWith("../") ||
      posix.normalize(file) !== file ||
      file.includes("\\")
    ) {
      throw new Error(`Expected a canonical relative .ts path: ${file}`);
    }
    const { code, map, errors } = transformSync(file, source, {
      sourceType: "module",
      sourcemap: true,
      typescript: { rewriteImportExtensions: true },
    });
    if (errors.length || !map)
      throw new Error(
        `${file}: ${errors.map((e) => e.message).join("; ") || "Missing source map"}`,
      );
    const { module } = parseSync(file + ".js", code);
    if (module.dynamicImports.length || module.importMetas.length)
      throw new Error("Only static repository imports are supported");
    modules[file.slice(0, -3) + ".js"] = {
      file,
      code,
      map: { ...map, file, sources: [file], sourcesContent: [source], sourceRoot: "" },
    };
  }
  const job: Job = {
    modules,
    entry: program.entry.slice(0, -3) + ".js",
    fn: program.fn,
    args: program.args,
    maxFrames,
  };
  const node = Bun.which("node");
  if (!node) throw new Error("Tracing requires Node 24+ on PATH for V8 inspector");
  const child = Bun.spawn(
    [
      node,
      "--disable-warning=ExperimentalWarning",
      "--max-old-space-size=192",
      "--experimental-vm-modules",
      fileURLToPath(import.meta.url),
      "--cwm-engine",
    ],
    {
      stdin: new Blob([JSON.stringify(job)]),
      stdout: "pipe",
      stderr: "pipe",
      env: {},
      timeout: timeoutMs,
      killSignal: "SIGKILL",
    },
  );
  const [code, stdout, stderr] = await Promise.all([
    child.exited,
    new Response(child.stdout).text(),
    new Response(child.stderr).text(),
  ]);
  if (code !== 0)
    throw new Error(
      stderr.trim() || `Engine stopped (${child.signalCode ?? code}; deadline ${timeoutMs} ms)`,
    );
  return { ...program, ...decodeExecution(stdout) };
}

export interface Edit {
  file: string;
  offset: number;
  before: string;
  after: string;
}

/** Enumerate reproducible, reversible edits, not text matches inside strings or comments. */
export async function mutations(program: Program): Promise<Edit[]> {
  const { parseSync, Visitor } = await import("oxc-parser");
  const edits: Edit[] = [];
  for (const file of Object.keys(program.files).sort()) {
    const source = program.files[file]!;
    const parsed = parseSync(file, source);
    if (parsed.errors.length) throw new Error(`${file}: ${parsed.errors[0]!.message}`);
    function replace(node: { start: number; end: number }, after: string) {
      edits.push({ file, offset: node.start, before: source.slice(node.start, node.end), after });
    }
    new Visitor({
      Literal(node) {
        let replacement: string;
        if (typeof node.value === "boolean") replacement = String(!node.value);
        else if (typeof node.value === "number" && Number.isSafeInteger(node.value))
          replacement = String(node.value + 1);
        else return;
        replace(node, replacement);
      },
      BinaryExpression(node) {
        if (node.operator !== "+" && node.operator !== "-") return;
        const left = source.slice(node.left.start, node.left.end);
        const right = source.slice(node.right.start, node.right.end);
        replace(node, `((${left}) ${node.operator === "+" ? "-" : "+"} (${right}))`);
      },
      IfStatement({ test }) {
        replace(test, `!(${source.slice(test.start, test.end)})`);
      },
    }).visit(parsed.program);
  }
  return edits;
}

export function applyEdit(program: Program, edit: Edit): Program {
  const source = program.files[edit.file];
  const { offset, before, after } = edit;
  if (
    typeof source !== "string" ||
    !Number.isSafeInteger(offset) ||
    offset < 0 ||
    offset > source.length ||
    source.slice(offset, offset + before.length) !== before
  )
    throw new Error("Edit does not match source");
  const replacement = source.slice(0, offset) + after + source.slice(offset + before.length);
  return { ...program, files: { ...program.files, [edit.file]: replacement } };
}

type Action = "run" | Edit;
type Interaction =
  | { action: Edit; applied: true }
  | { action: Action; error: string }
  | { action: "run"; execution: Execution; verdict: "pass" | "fail" | "unknown" };

export async function episode(initial: Program, actions: Iterable<Action>, expected: Json) {
  initial = structuredClone(initial);
  expected = structuredClone(expected);
  let program = initial;
  const steps: Interaction[] = [];
  for (const input of actions) {
    const action = input === "run" ? input : { ...input };
    try {
      if (action !== "run") {
        program = applyEdit(program, action);
        steps.push({ action, applied: true });
      } else {
        const { frames, outcome } = await trace(program);
        const verdict =
          outcome.kind === "threw"
            ? "fail"
            : !outcome.result.exact
              ? "unknown"
              : isDeepStrictEqual(outcome.result.value, expected)
                ? "pass"
                : "fail";
        steps.push({ action, execution: { frames, outcome }, verdict });
      }
    } catch (error) {
      steps.push({ action, error: String(error) });
    }
  }
  return { initial, expected, steps };
}

export function repair(program: Program, edit: Edit, expected: Json) {
  return episode(
    applyEdit(program, edit),
    ["run", { ...edit, before: edit.after, after: edit.before }, "run"],
    expected,
  );
}

export type Observation = Frame | Execution["outcome"];

export function* transitions(run: Execution): Generator<readonly [Frame, Observation]> {
  for (const [i, frame] of run.frames.entries()) yield [frame, run.frames[i + 1] ?? run.outcome];
}

type Example = readonly [Frame, Observation];

// Namespaced slots distinguish a local called "value" from a function's return value.
function scalars(state: Observation): Map<string, Snapshot & { value: number }> {
  const slots = new Map<string, Snapshot & { value: number }>();
  const add = (name: string, slot?: Snapshot) => {
    if (slot?.exact && typeof slot.value === "number")
      slots.set(name, slot as Snapshot & { value: number });
  };
  if ("locals" in state) {
    for (const [name, slot] of Object.entries(state.locals)) add("local:" + name, slot);
    add("value", state.value);
  } else add("value", state.result);
  return slots;
}

function location(state: Observation, line?: string) {
  const stack = "stack" in state ? state.stack.map((s) => [s.file, s.line, s.column, s.fn]) : null;
  return JSON.stringify([state.kind, stack, line]);
}

/** Fit identifiable affine updates for one control-flow edge; keep retrieval for other outputs. */
function fitDynamics(examples: Example[]) {
  const inputs = examples.map(([before]) => scalars(before));
  const outputs = examples.map(([, after]) => scalars(after));
  const shared = [...inputs[0]!.keys()].filter((k) => inputs.every((row) => row.has(k))).sort();
  const constants = new Map<string, number>();
  const features = shared.filter((k) => {
    const first = inputs[0]!.get(k)!.value;
    if (inputs.some((r) => r.get(k)!.value !== first)) return true;
    constants.set(k, first);
    return false;
  });
  const targets = [...outputs[0]!.keys()].filter(
    (k) =>
      outputs.every((row) => row.has(k)) &&
      !outputs.every((row, i) => row.get(k)!.value === inputs[i]!.get(k)?.value),
  );
  if (!shared.length || !targets.length || examples.length < 2) return;
  const vector = (row: ReturnType<typeof scalars>) => [
    1,
    ...features.map((k) => row.get(k)!.value),
  ];
  const x = new Matrix(inputs.map(vector));
  const scales = x
    .clone()
    .abs()
    .max("column")
    .map((v) => v || 1);
  const y = new Matrix(outputs.map((row) => targets.map((k) => row.get(k)!.value)));
  const decomposition = new SingularValueDecomposition(x.clone().divRowVector(scales), {
    autoTranspose: true,
  });
  const rank = decomposition.rank;
  if (examples.length <= rank) return;
  // Pivot the singular vectors to choose independent real observations and coordinates.
  const pivots = (basis: Matrix) =>
    new LuDecomposition(
      basis.subMatrix(0, basis.rows - 1, 0, rank - 1),
    ).pivotPermutationVector.slice(0, rank);
  const cols = pivots(decomposition.rightSingularVectors);
  const rows = pivots(decomposition.leftSingularVectors);
  const basis = new LuDecomposition(x.selection(rows, cols));
  if (basis.isSingular()) return;
  const weights = basis.solve(y.subMatrixRow(rows));
  const residual = x.subMatrixColumn(cols).mmul(weights).sub(y);
  const learned = targets.flatMap((key, i) =>
    residual.getColumn(i).every((e, r) => Math.abs(e) <= 1e-10 * Math.abs(y.get(r, i)))
      ? [{ key, coefficients: weights.getColumn(i) }]
      : [],
  );
  if (!learned.length) return;
  const constraints = scales.flatMap((scale, j) =>
    cols.includes(j)
      ? []
      : [
          {
            j,
            scale,
            coefficients: basis.solve(x.selection(rows, [j])).getColumn(0),
          },
        ],
  );
  return (before: Frame, prediction: Observation) => {
    const row = scalars(before);
    for (const [k, value] of constants) if (row.get(k)?.value !== value) return false;
    if (!features.every((k) => row.has(k))) return false;
    const values = vector(row);
    const independent = cols.map((j) => values[j]!);
    if (
      !constraints.every(
        ({ j, scale, coefficients }) =>
          Math.abs(dot(independent, coefficients) - values[j]!) <=
          1e-10 * Math.max(scale, Math.abs(values[j]!)),
      )
    )
      return false;
    const output = scalars(prediction);
    for (const { key, coefficients } of learned) {
      const estimate = dot(independent, coefficients);
      const field = output.get(key);
      if (!field || !Number.isFinite(estimate)) return false;
      field.value = estimate;
    }
    return true;
  };
}

function dot(a: number[], b: number[]) {
  return a.reduce((sum, v, i) => sum + v * b[i]!, 0);
}

/** Fit control-flow examples and local scalar dynamics. Prediction never executes source. */
export class WorldModel {
  private readonly cases = new Map<string, Example[]>();
  private readonly dynamics = new Map<string, Map<string, ReturnType<typeof fitDynamics>>>();

  private key(files: Program["files"], frame: Frame) {
    const action = frame.stack[0]!;
    const line = files[action.file]?.split(/\r\n|[\r\n\u2028\u2029]/u)[action.line - 1];
    return location(frame, line);
  }

  fit(runs: Iterable<Trace>) {
    this.cases.clear();
    this.dynamics.clear();
    for (const { files, frames, outcome } of runs) {
      for (const pair of transitions(structuredClone({ frames, outcome }))) {
        const key = this.key(files, pair[0]);
        const cases = this.cases.get(key) ?? [];
        cases.push(pair);
        this.cases.set(key, cases);
      }
    }
    for (const [key, cases] of this.cases) {
      const edges = Map.groupBy(cases, ([, next]) => location(next));
      this.dynamics.set(key, new Map([...edges].map(([edge, rows]) => [edge, fitDynamics(rows)])));
    }
    return this;
  }

  predict(files: Program["files"], current: Frame): Observation | undefined {
    const key = this.key(files, current);
    const cases = this.cases.get(key);
    if (!cases) return;
    let best = -Infinity;
    const nearest: Example[] = [];
    for (const pair of cases) {
      const previous = pair[0];
      let score = Number(isDeepStrictEqual(previous.value, current.value));
      for (const name of new Set([
        ...Object.keys(previous.locals),
        ...Object.keys(current.locals),
      ])) {
        score += isDeepStrictEqual(previous.locals[name], current.locals[name]) ? 1 : -1;
      }
      if (score > best) {
        nearest.length = 0;
        best = score;
      }
      if (score === best) nearest.push(pair);
    }
    let answer: Observation | undefined;
    for (const [from, to] of nearest) {
      const next = structuredClone(to);
      if (!isDeepStrictEqual(current, from)) {
        if ("locals" in next) {
          for (const [name, old] of Object.entries(from.locals)) {
            if (Object.hasOwn(current.locals, name) && isDeepStrictEqual(next.locals[name], old)) {
              next.locals[name] = structuredClone(current.locals[name]!);
            }
          }
          if (from.value && current.value && isDeepStrictEqual(from.value, next.value))
            next.value = structuredClone(current.value);
        } else if (from.value && current.value && isDeepStrictEqual(from.value, next.result)) {
          next.result = structuredClone(current.value);
        }
        if (this.dynamics.get(key)?.get(location(next))?.(current, next) === false) return;
      }
      if (answer && !isDeepStrictEqual(answer, next)) return;
      answer = next;
    }
    return answer;
  }

  *rollout(
    files: Program["files"],
    start: Frame,
    maxSteps: number,
  ): Generator<Observation, "terminal" | "unseen" | "limit"> {
    if (!Number.isSafeInteger(maxSteps) || maxSteps < 1)
      throw new Error("Expected a positive rollout budget");
    let current = start;
    for (let i = 0; i < maxSteps; i++) {
      const next = this.predict(files, current);
      if (!next) return "unseen";
      yield next;
      if (!("stack" in next)) return "terminal";
      current = next;
    }
    return "limit";
  }
}

export function evaluate(
  model: WorldModel,
  heldOut: Iterable<Trace>,
  { total, predicted, correct } = { total: 0, predicted: 0, correct: 0 },
) {
  for (const run of heldOut) {
    for (const [frame, truth] of transitions(run)) {
      const guess = model.predict(run.files, frame);
      total++;
      if (guess) predicted++;
      if (isDeepStrictEqual(guess, truth)) correct++;
    }
  }
  return { total, predicted, correct };
}

async function* records<T>(
  input: NodeJS.ReadableStream,
  schema: Schema.Codec<T>,
): AsyncGenerator<T> {
  const decode = Schema.decodeUnknownSync(Schema.fromJsonString(schema), strict);
  let index = 0;
  for await (const line of createInterface({ input, crlfDelay: Infinity })) {
    index++;
    if (!line.trim()) continue;
    try {
      yield decode(line);
    } catch (cause) {
      throw new Error(`Invalid JSONL record at line ${index}`, { cause });
    }
  }
}

export function readTraces(path: string) {
  return records(Readable.from(Bun.file(path).stream()), traceSchema);
}

if (!isMainThread && workerData?.cwmObserver) {
  await observe(workerData.job as Job);
} else if (import.meta.main) {
  if (process.argv[2] === "--cwm-engine") {
    process.stdout.write(JSON.stringify(await execute((await json(process.stdin)) as Job)));
  } else if (process.argv.length === 5 && process.argv[2] === "score") {
    const model = new WorldModel().fit(await Array.fromAsync(readTraces(process.argv[3]!)));
    let score = evaluate(model, []);
    for await (const run of readTraces(process.argv[4]!)) score = evaluate(model, [run], score);
    console.log(JSON.stringify(score));
  } else if (process.argv.length === 2) {
    for await (const program of records(process.stdin, programSchema))
      console.log(JSON.stringify(await trace(program)));
  } else
    throw new Error("Usage: bun cwm.ts < programs.jsonl | bun cwm.ts score TRAIN.jsonl TEST.jsonl");
}
