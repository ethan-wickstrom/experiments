import { parseSync } from "oxc-parser";
import { type ProjectSession, type TurnEvent } from "./agent.ts";
import { projectJson, type Action } from "./protocol.ts";
import { sourcePath } from "./workspace.ts";

/** The user selects the file. The same checkpoint supplies every byte of each replacement. */
export async function editFile(
  session: ProjectSession,
  path: string,
  goal: string,
  signal?: AbortSignal,
  onEvent?: (event: TurnEvent) => void,
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path))
    throw Error("Expected a TypeScript path");
  await session.begin(goal);
  const { files } = session.project;
  const tests: Record<string, string> = {};
  for (const name of [...files.keys()].sort()) {
    if (name === path || !/\.(test|spec)\.[cm]?tsx?$/.test(name)) continue;
    tests[name] = (await session.act({ op: "read", path: name }, signal)).observed;
  }
  if (files.has(path)) await session.act({ op: "read", path }, signal);
  const requests = session.history.flatMap((event) => ("user" in event ? [event.user] : []));
  const events: TurnEvent[] = [];
  let diagnostic: string | undefined;
  for (let attempt = 0; attempt < 2; attempt++) {
    const prompt =
      "Implement the user's latest request. Return the complete TypeScript source for the target file in a single TypeScript code block. Preserve earlier requested behavior. The tests are separate files.\n" +
      projectJson({ requests, path, source: files.get(path) ?? "", tests, diagnostic });
    if (Buffer.byteLength(prompt) > 32000) return { stop: "context-limit", events };
    const start = performance.now();
    const reply = await session.generate(prompt, 768, signal);
    const event: TurnEvent = {
      request: prompt,
      reply,
      elapsedMs: Math.round(performance.now() - start),
    };
    events.push(event);
    if (reply.finish !== "stop") {
      onEvent?.(event);
      return { stop: "incomplete", events };
    }
    const fence = /^`{3}(?:typescript|ts)?[^\S\r\n]*\r?\n([\s\S]*?)^`{3}\s*$/m.exec(reply.text);
    const text = fence?.[1] ?? reply.text;
    if (
      (reply.text.match(/^`{3}/gm)?.length ?? 0) > 2 ||
      !text.trim() ||
      text.includes("```") ||
      parseSync(path, text).errors.length
    ) {
      onEvent?.(event);
      return { stop: "invalid", events };
    }
    const action: Action = { op: "write", path, text };
    event.action = action;
    const write = await session.act(action, signal);
    event.observed = write.observed;
    if (write.observed !== "written") {
      onEvent?.(event);
      return { stop: "rejected", events };
    }
    const test = await session.act({ op: "test" }, signal);
    event.run = test.run;
    onEvent?.(event);
    if (test.observed === "pass") return { stop: "tested", events };
    diagnostic = test.observed;
  }
  return { stop: "budget", events };
}
