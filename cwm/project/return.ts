import { parseSync } from "oxc-parser";
import { type ProjectSession, type TurnEvent } from "./agent.ts";
import { projectJson } from "./protocol.ts";
import { sourcePath } from "./workspace.ts";

// Oxc's JavaScript spans index UTF-16 code units, as does String.slice().
function selection(path: string, source: string, name: string) {
  const parsed = parseSync(path, source, { preserveParens: true });
  if (parsed.errors.length) return;
  const selected = parsed.program.body.flatMap((node) => {
    const fn = node.type === "ExportNamedDeclaration" ? node.declaration : null;
    return fn?.type === "FunctionDeclaration" && fn.id?.name === name && fn.body ? [fn] : [];
  });
  if (selected.length !== 1) return;
  const fn = selected[0]!;
  const body = fn.body!;
  const statement = body.body[0];
  if (body.body.length !== 1 || statement?.type !== "ReturnStatement" || !statement.argument)
    return;
  return {
    signature: source.slice(fn.start, body.start).trimEnd(),
    body: source.slice(body.start, body.end),
    expression: statement.argument,
  };
}

/** Replace only the argument of a named exported function's sole return statement. */
export async function editReturn(
  session: ProjectSession,
  path: string,
  name: string,
  goal: string,
  signal?: AbortSignal,
  onEvent?: (event: TurnEvent) => void,
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path))
    throw Error("Expected a TypeScript path");
  await session.begin(goal);
  const source = (await session.act({ op: "read", path }, signal)).observed;
  const current = selection(path, source, name);
  if (!current) throw Error("Expected a named exported function with one return expression");
  const tests: Record<string, string> = {};
  for (const file of session.state().files) {
    if (file !== path && /\.(?:spec|test)\.[cm]?tsx?$/.test(file))
      tests[file] = (await session.act({ op: "read", path: file }, signal)).observed;
  }
  const requests = session.history.flatMap((event) => ("user" in event ? [event.user] : []));
  const request =
    "Implement the latest request for this exported TypeScript function. Reply only with the expression that should follow return. Omit the return keyword, semicolon, code fences and explanation.\n" +
    projectJson({ path, signature: current.signature, body: current.body, tests, requests });
  const events: TurnEvent[] = [];
  if (Buffer.byteLength(request) > 32000) return { stop: "context-limit", events };
  const start = performance.now();
  const reply = await session.generate(request, 96, signal, undefined, true);
  const event: TurnEvent = { request, reply, elapsedMs: Math.round(performance.now() - start) };
  events.push(event);
  const finish = (stop: string) => {
    onEvent?.(event);
    return { stop, events };
  };
  if (reply.finish !== "stop") return finish("incomplete");
  const expression = reply.text.trim();
  if (!expression || /^\x60{3}/.test(expression)) return finish("invalid");
  const span = current.expression;
  const text = source.slice(0, span.start) + expression + source.slice(span.end);
  const replaced = selection(path, text, name)?.expression;
  // The entire trimmed reply must be the return argument in its actual TypeScript context.
  if (!replaced || replaced.start !== span.start || replaced.end !== span.start + expression.length)
    return finish("invalid");
  event.action = { op: "write", path, text };
  event.observed = (await session.act(event.action, signal)).observed;
  if (event.observed !== "written") return finish("rejected");
  const test = await session.act({ op: "test" }, signal);
  event.run = test.run;
  return finish(test.observed === "pass" ? "tested" : "failed");
}
