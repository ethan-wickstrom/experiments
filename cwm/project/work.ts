import { parseSync } from "oxc-parser";
import { decide, edit, type Status } from "../bench/development/c2/wire.ts";
import { type ProjectSession, type TurnEvent } from "./agent.ts";
import { sourcePath } from "./workspace.ts";

export function completeSource(path: string, text: string) {
  return !!text.trim() && !/^\s*\x60{3}/.test(text) && !parseSync(path, text).errors.length;
}

/** Host selects a file. Both the next action and its source payload use the serving checkpoint. */
export async function workFile(
  session: ProjectSession,
  path: string,
  goal: string,
  {
    sourceOnly = false,
    signal,
    onEvent,
  }: {
    sourceOnly?: boolean;
    signal?: AbortSignal;
    onEvent?: (event: TurnEvent) => void;
  } = {},
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path))
    throw Error("Expected a TypeScript path");
  await session.begin(goal);
  const events: TurnEvent[] = [];
  const finish = (stop: string) => ({ stop, events });
  const files = () => Array.from(session.project.files, ([path, text]) => ({ path, text }));
  async function query(request: string, limit: number, verbatim = false) {
    const start = performance.now();
    const reply = await session.generate(request, limit, signal, undefined, verbatim);
    const event: TurnEvent = { request, reply, elapsedMs: Math.round(performance.now() - start) };
    events.push(event);
    return event;
  }
  let status: Status = "unread";
  if (sourceOnly && session.project.files.has(path)) {
    await session.act({ op: "read", path }, signal);
    status = "read";
  }
  for (let step = 0; step < 8; step++) {
    signal?.throwIfAborted();
    if (!sourceOnly) {
      const prompt = decide(goal, path, files(), status);
      if (Buffer.byteLength(prompt) > 32000) return finish("context-limit");
      const event = await query(prompt, 8);
      const choice = event.reply.text;
      if (event.reply.finish !== "stop") {
        onEvent?.(event);
        return finish("incomplete");
      }
      if (choice === "done") {
        event.action = { op: "done" };
        onEvent?.(event);
        return finish(session.untestedChanges ? "untested" : "done");
      }
      if (choice === "read" || choice === "test") {
        const action =
          choice === "test" ? ({ op: "test" } as const) : ({ op: "read", path } as const);
        Object.assign(event, { action }, await session.act(action, signal));
        onEvent?.(event);
        if (event.observed === "rejected") return finish("rejected");
        status = choice === "read" ? "read" : event.observed === "pass" ? "pass" : "fail";
        continue;
      }
      onEvent?.(event);
      if (choice !== "edit") return finish("invalid");
    }
    const prompt = edit(goal, path, files());
    if (Buffer.byteLength(prompt) > 32000) return finish("context-limit");
    const event = await query(prompt, 384, true);
    const text = event.reply.text;
    if (event.reply.finish !== "stop" || !completeSource(path, text)) {
      onEvent?.(event);
      return finish(event.reply.finish !== "stop" ? "incomplete" : "invalid");
    }
    event.action = { op: "write", path, text };
    Object.assign(event, await session.act(event.action, signal));
    if (event.observed === "rejected") {
      onEvent?.(event);
      return finish("rejected");
    }
    if (sourceOnly) {
      const test = await session.act({ op: "test" }, signal);
      event.run = test.run;
      onEvent?.(event);
      return finish(test.observed === "pass" ? "tested" : "failed");
    }
    onEvent?.(event);
    status = "written";
  }
  return finish("budget");
}
