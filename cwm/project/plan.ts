import { fileURLToPath } from "node:url";
import { Schema } from "effect";
import { edit, type Source } from "../bench/development/c2/wire.ts";
import { type ProjectSession, type TurnEvent } from "./agent.ts";
import { type Action } from "./protocol.ts";
import { completeSource } from "./work.ts";
import { sourcePath } from "./workspace.ts";

type Write = Extract<Action, { op: "write" }>;
export type Pair = { goal: string; path: string; files: Source[]; candidates: [Write, Write] };
const decision = Schema.Struct({
  scores: Schema.Tuple([Schema.Finite, Schema.Finite]),
  choice: Schema.Union([Schema.Literal(0), Schema.Literal(1), Schema.Null]),
});
type Decision = typeof decision.Type;
type Rank = (pair: Pair, signal?: AbortSignal) => Promise<Decision>;

/** One local model load can score a batch. Only visible files and proposed writes cross stdin. */
export async function rankPairs(pairs: Pair[], arm = "C2", signal?: AbortSignal) {
  if (!pairs.length) return [];
  const script = fileURLToPath(new URL("../bench/development/ranking/rank.py", import.meta.url));
  const child = Bun.spawn([process.env.CWM_PYTHON ?? "python", script, "--serve", "--arm", arm], {
    stdin: new Blob(pairs.map((pair) => JSON.stringify(pair) + "\n")),
    stdout: "pipe",
    stderr: "inherit",
    signal,
    timeout: 600000,
    killSignal: "SIGKILL",
  });
  try {
    const raw = await new Response(child.stdout).text();
    if ((await child.exited) !== 0) throw Error("Consequence ranker failed");
    const lines = raw.trimEnd().split("\n");
    if (lines.length !== pairs.length) throw Error("Incomplete ranking batch");
    return lines.map((line) => Schema.decodeUnknownSync(Schema.fromJsonString(decision))(line));
  } finally {
    child.kill();
    await child.exited;
  }
}

function rank(pair: Pair, signal?: AbortSignal) {
  return rankPairs([pair], "C2", signal).then((answers) => answers[0]!);
}

/** Sample twice from one observed state. Execute only after the selection is recorded. */
export async function planFile(
  session: ProjectSession,
  path: string,
  goal: string,
  { choose = rank, signal }: { choose?: Rank; signal?: AbortSignal } = {},
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path))
    throw Error("Expected a TypeScript path");
  await session.begin(goal);
  if (session.project.files.has(path)) await session.act({ op: "read", path }, signal);
  const files = [...session.project.files].map(([path, text]) => ({ path, text }));
  const request = edit(goal, path, files);
  const events: TurnEvent[] = [];
  const proposals: { action: Write; index: number }[] = [];
  let prediction: Decision | null = null;
  const finish = (stop: string) => ({ stop, events, prediction });
  if (Buffer.byteLength(request) > 32000) return finish("context-limit");
  for (const sampling of [undefined, { temperature: 0.7, seed: 17 }]) {
    const start = performance.now();
    const reply = await session.generate(request, 384, signal, undefined, true, sampling);
    const index =
      events.push({ request, reply, elapsedMs: Math.round(performance.now() - start) }) - 1;
    if (
      reply.finish === "stop" &&
      completeSource(path, reply.text) &&
      !proposals.some((p) => p.action.text === reply.text)
    )
      proposals.push({ action: { op: "write", path, text: reply.text }, index });
  }
  if (!proposals.length) return finish("no-valid-proposal");
  let selected = proposals[0]!;
  if (proposals.length === 2) {
    prediction = await choose(
      { goal, path, files, candidates: [selected.action, proposals[1]!.action] },
      signal,
    );
    if (prediction.choice === null) return finish("tie");
    selected = proposals[prediction.choice]!;
  }
  const event = events[selected.index]!;
  event.action = selected.action;
  event.observed = (await session.act(selected.action, signal)).observed;
  if (event.observed !== "written") return finish("rejected");
  const test = await session.act({ op: "test" }, signal);
  event.run = test.run;
  return finish(test.observed === "pass" ? "tested" : "failed");
}
