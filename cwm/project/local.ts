import { Schema } from "effect";
import { parseSync } from "oxc-parser";
import { type Generate, type ProjectSession } from "./agent.ts";
import { pythonModel } from "./model-process.ts";
import { maxFileBytes, sourcePath, testPath } from "./workspace.ts";

type Request = {
  goal: string;
  path: string;
  files: { path: string; text: string }[];
  observed: string;
};
const decode = Schema.decodeUnknownSync(
  Schema.Union([
    Schema.Struct({
      stopped: Schema.Literal(true),
      start: Schema.Int,
      end: Schema.Int,
      replacement: Schema.String,
      text: Schema.String,
    }),
    Schema.Struct({ stopped: Schema.Literal(false), error: Schema.String }),
  ]),
);
type Propose = (request: Request, signal?: AbortSignal) => Promise<unknown>;

export function openLocalEditor(arm = "trained") {
  const server = pythonModel(
    new URL("../bench/development/local_edit/project_server.py", import.meta.url),
    arm,
  );
  const completion = Schema.decodeUnknownSync(
    Schema.Union([
      Schema.Struct({
        text: Schema.String,
        finish: Schema.String,
        tokens: Schema.Int,
        inputTokens: Schema.Int,
      }),
      Schema.Struct({ error: Schema.String }),
    ]),
  );
  const forecast: Generate = async (prompt, _limit, signal) => {
    const reply = completion(await server.request({ forecast: prompt }, signal));
    if ("error" in reply) throw Error(reply.error);
    return reply;
  };
  const propose: Propose = (request, signal) => server.request({ edit: request }, signal);
  return { propose, forecast, close: server.close };
}

/** Boundaries count only LF, retaining CRLF and the final unterminated line exactly. */
export function localSplice(source: string, start: number, end: number, replacement: string) {
  const offsets = [0];
  for (let i = source.indexOf("\n"); i !== -1; i = source.indexOf("\n", i + 1)) offsets.push(i + 1);
  if (offsets.at(-1) !== source.length) offsets.push(source.length);
  if (
    !Number.isSafeInteger(start) ||
    !Number.isSafeInteger(end) ||
    start < 0 ||
    end < start ||
    end >= offsets.length
  )
    throw Error("Invalid local edit span");
  return source.slice(0, offsets[start]) + replacement + source.slice(offsets[end]);
}

export async function editLocal(
  session: ProjectSession,
  propose: Propose,
  path: string,
  goal: string,
  signal?: AbortSignal,
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path) || testPath(path))
    throw Error("Expected an implementation TypeScript path");
  await session.begin(goal);
  const original = session.project.files.get(path);
  if (original === undefined) throw Error("Local editing requires an existing file");
  const files = [];
  for (const name of [...session.project.files.keys()].sort()) {
    const { observed } = await session.act({ op: "read", path: name }, signal);
    files.push({ path: name, text: observed });
  }
  const before = await session.act({ op: "test" }, signal, "c2");
  const reply = decode(await propose({ path, goal, files, observed: before.observed }, signal));
  signal?.throwIfAborted();
  if (!reply.stopped) return { stop: "incomplete", before, reply };
  const text = localSplice(original, reply.start, reply.end, reply.replacement);
  if (
    text !== reply.text ||
    !text.isWellFormed() ||
    Buffer.byteLength(text) > maxFileBytes ||
    parseSync(path, text).errors.length
  )
    return { stop: "invalid", before, reply };
  if (session.project.files.get(path) !== original) throw Error("Source changed during local edit");
  if (original === text) return { stop: "unchanged", before, reply };
  const write = await session.act({ op: "write", path, text }, signal);
  if (write.observed !== "written") return { stop: "rejected", before, reply, write };
  const after = await session.act({ op: "test" }, signal, "c2");
  return { stop: after.observed === "pass" ? "tested" : "failed", before, reply, write, after };
}
