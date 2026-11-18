import { parseSync } from "oxc-parser";
import { decide, edit, observation, type Status } from "../bench/development/c2/wire.ts";
import { type ProjectSession, type TurnEvent } from "./agent.ts";
import { sourcePath } from "./workspace.ts";

/** Host selects a file. Both the next action and its source payload use the serving checkpoint. */
export async function workFile(
  session: ProjectSession,
  path: string,
  goal: string,
  {
    sourceOnly = false,
    visibility = "training-aligned",
    signal,
    onEvent,
  }: {
    sourceOnly?: boolean;
    visibility?: "training-aligned" | "full-context";
    signal?: AbortSignal;
    onEvent?: (event: TurnEvent) => void;
  } = {},
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path))
    throw Error("Expected a TypeScript path");
  await session.begin(goal);
  const events: TurnEvent[] = [];
  const finish = (stop: string) => ({ stop, events });
  const aligned = !sourceOnly && visibility === "training-aligned";
  const files = () =>
    Array.from(aligned ? session.observedFiles : session.project.files, ([path, text]) => ({
      path,
      text,
    }));
  async function read() {
    if (!aligned || !session.project.files.has(path))
      return session.act({ op: "read", path }, signal);
    // A training read observes every visible file in path order, including tests and helpers.
    for (const name of [...session.project.files.keys()].sort()) {
      signal?.throwIfAborted();
      await session.act({ op: "read", path: name }, signal);
    }
    return { observed: session.observedFiles.get(path)! };
  }
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
        const result =
          action.op === "read"
            ? await read()
            : await session.act(action, signal, aligned ? observation : undefined);
        Object.assign(event, { action }, result);
        onEvent?.(event);
        if (action.op === "read" && !session.observedFiles.has(path)) return finish("rejected");
        status = choice === "read" ? "read" : event.observed === "pass" ? "pass" : "fail";
        continue;
      }
      if (
        aligned &&
        choice === "edit" &&
        session.project.files.has(path) &&
        !session.observedFiles.has(path)
      ) {
        event.observed = "rejected";
        onEvent?.(event);
        return finish("rejected");
      }
      onEvent?.(event);
      if (choice !== "edit") return finish("invalid");
    }
    const prompt = edit(goal, path, files());
    if (Buffer.byteLength(prompt) > 32000) return finish("context-limit");
    const event = await query(prompt, 384, true);
    const text = event.reply.text;
    if (
      event.reply.finish !== "stop" ||
      !text.trim() ||
      /^\s*\x60{3}/m.test(text) ||
      parseSync(path, text).errors.length
    ) {
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
