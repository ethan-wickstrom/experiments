import { parseSync } from "oxc-parser";
import { type ProjectSession } from "./agent.ts";
import { type BodyGenerate, type BodyQuery, type BodyReply } from "./body-completion.ts";
import { projectJson, wire } from "./protocol.ts";
import { testObservation, type ToolRun } from "./sandbox.ts";
import { sourcePath, testPath } from "./workspace.ts";

const fence = "\x60\x60\x60";
type Target = { name: string; declaration: string; start: number; end: number };

function targets(path: string, source: string): Target[] {
  const parsed = parseSync(path, source);
  if (parsed.errors.length) return [];
  return parsed.program.body.flatMap((node) => {
    if (node.type !== "ExportNamedDeclaration") return [];
    const fn = node.declaration;
    if (fn?.type !== "FunctionDeclaration" || !fn.id || !fn.body) return [];
    const { start, end } = fn.body;
    return [{ name: fn.id.name, declaration: source.slice(node.start, start + 1), start, end }];
  });
}

// Take only a complete continuation of the already open block. Oxc decides
// which closing brace belongs to this function, including nested literals.
export function spliceBody(path: string, source: string, target: Target, generated: string) {
  for (const match of generated.matchAll(/}/g)) {
    const chunk = generated.slice(0, match.index + 1);
    const length = target.start + 1 + chunk.length;
    const text = source.slice(0, target.start + 1) + chunk + source.slice(target.end);
    const found = targets(path, text).find(
      (fn) => fn.name === target.name && fn.start === target.start,
    );
    if (found?.end === length) return { text, consumed: chunk.length };
  }
}

type Call = {
  kind: "select" | "body" | "forecast";
  query: BodyQuery;
  reply: BodyReply;
  elapsedMs: number;
};
type Write = {
  path: string;
  before: string;
  after: string;
  consumed: number;
  observed: string;
  prediction: string | null;
  forecastFailure?: { query: BodyQuery; error: string; elapsedMs: number };
  run?: ToolRun;
};
const completed = (r: BodyReply) => !r.truncated && (r.finish === "eos" || r.finish === "word");

/** A path is user-directed. Omit name to let the checkpoint choose among multiple exports. */
export async function editBody(
  session: ProjectSession,
  generate: BodyGenerate,
  path: string,
  goal: string,
  { name, signal }: { name?: string; signal?: AbortSignal } = {},
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path) || testPath(path))
    throw Error("Expected an implementation TypeScript path");
  await session.begin(goal);
  const files: Record<string, string> = Object.create(null);
  for (const file of session.state().files)
    files[file] = (await session.act({ op: "read", path: file }, signal)).observed;
  const candidates = targets(path, files[path] ?? "");
  if (!candidates.length || (name !== undefined && !candidates.some((c) => c.name === name)))
    throw Error("Expected an exported named function declaration with a body");
  const calls: Call[] = [];
  const writes: Write[] = [];
  const before = (await session.act({ op: "test" }, signal)).run!;
  let run = before;
  const selection = name !== undefined ? "user" : candidates.length === 1 ? "only-export" : "model";
  let selected = name ?? candidates[0]!.name;
  const finish = (stop: string) => ({ stop, selection, selected, before, calls, writes });
  async function query(kind: Call["kind"], q: BodyQuery) {
    const start = performance.now();
    const reply = await generate(q, signal);
    calls.push({ kind, query: q, reply, elapsedMs: Math.round(performance.now() - start) });
    return reply;
  }
  const state = () => ({
    goal,
    path,
    files: Object.entries(files).map(([path, text]) => ({ path, text })),
    visibleTest: testObservation(run),
  });
  if (selection === "model") {
    const names = candidates.map((c) => c.name);
    const reply = await query("select", {
      user:
        "Which exported function needs a change for this request? Answer with one listed name.\n" +
        projectJson({ ...state(), exports: names }),
      prefill: "",
      limit: 24,
      grammar: "root ::= " + names.map((s) => JSON.stringify(s)).join(" | "),
    });
    selected = reply.text.trim();
    if (!completed(reply) || !names.includes(selected)) return finish("invalid-selection");
  }
  for (let attempt = 0; attempt < 2; attempt++) {
    const source = files[path]!;
    const target = targets(path, source).find((fn) => fn.name === selected)!;
    const newline = /^(?:\r\n|\n)/.exec(source.slice(target.start + 1))?.[0] ?? "";
    const reply = await query("body", {
      user:
        "Write the selected TypeScript function for the goal. Reply with the complete function in one TypeScript code block.\n" +
        projectJson({ ...state(), selected }),
      prefill: fence + "typescript\n" + target.declaration + newline,
      limit: 384,
      stop: ["\n" + fence],
    });
    if (!completed(reply)) return finish("incomplete");
    const patch = spliceBody(path, source, target, newline + reply.text);
    if (!patch) return finish("invalid-body");
    const action = { op: "write" as const, path, text: patch.text };
    const snapshot = session.state();
    const forecastQuery = {
      user: wire(snapshot.files, snapshot.history, action),
      prefill: "",
      limit: 8,
    };
    let prediction: string | null = null;
    let forecastFailure: Write["forecastFailure"];
    const forecastStart = performance.now();
    try {
      const forecast = await query("forecast", forecastQuery);
      const word = forecast.text.trim();
      if (completed(forecast) && ["pass", "fail", "rejected"].includes(word)) prediction = word;
    } catch (error) {
      forecastFailure = {
        query: forecastQuery,
        error: String(error),
        elapsedMs: Math.round(performance.now() - forecastStart),
      };
    }
    signal?.throwIfAborted();
    const observed = (await session.act(action, signal)).observed;
    const write: Write = {
      path,
      before: source,
      after: patch.text,
      consumed: patch.consumed - newline.length,
      observed,
      prediction,
      forecastFailure,
    };
    writes.push(write);
    if (observed !== "written") return finish("rejected");
    files[path] = patch.text;
    run = (await session.act({ op: "test" }, signal)).run!;
    write.run = run;
    if (run.exit === 0) return finish("tested");
  }
  return finish("failed");
}
