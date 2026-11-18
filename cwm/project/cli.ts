import { createInterface } from "node:readline";
import { resolve } from "node:path";
import { ProjectSession, endpoint } from "./agent.ts";
import { openProject } from "./workspace.ts";
import { decodeAction } from "./protocol.ts";
import { workFile } from "./work.ts";
import { editFile } from "./directed.ts";
import { editReturn } from "./return.ts";
import { editBody } from "./body.ts";
import { bodyEndpoint } from "./body-completion.ts";
import { openRanker, planFile } from "./plan.ts";
import { spliceFile } from "./splice.ts";
import { openLocalEditor, editLocal } from "./local.ts";

if (!process.argv[2] || process.argv.includes("--help")) {
  console.log(
    "Usage: bun run project DIRECTORY [--local PATH]\nEnter a request, /edit PATH REQUEST, /work PATH REQUEST (C2), /plan PATH REQUEST (two proposals with C2 ranking), /local PATH REQUEST, /splice PATH REQUEST, /body PATH EXPORT|* REQUEST, /return PATH FUNC REQUEST, /forecast ACTION_JSON, or /quit. Writes update the project.",
  );
} else {
  const args = process.argv.slice(3);
  if (args.length && (args.length !== 2 || args[0] !== "--local" || !args[1]))
    throw Error("Usage: bun run project DIRECTORY [--local PATH]");
  let focusedPath = args[1];
  const project = await openProject(resolve(process.argv[2]));
  const model = process.env.CWM_PROJECT_MODEL ?? "minicpm5-joint";
  const generate = endpoint(
    process.env.CWM_PROJECT_URL ?? "http://127.0.0.1:8082/v1/chat/completions",
    model,
  );
  const format = process.env.CWM_PROJECT_FORMAT ?? "project";
  if (format !== "project" && format !== "c2")
    throw Error("Expected CWM_PROJECT_FORMAT=project or c2");
  const session = new ProjectSession(project, generate, undefined, format);
  const abort = new AbortController();
  const ranker = openRanker();
  const localEditor = openLocalEditor(process.env.CWM_LOCAL_ARM);
  const lines = createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: Boolean(process.stdin.isTTY),
  });
  const cancel = () => {
    abort.abort();
    lines.close();
  };
  lines.on("SIGINT", cancel);
  process.once("SIGINT", cancel);
  process.once("SIGTERM", cancel);
  try {
    const displayedModel = focusedPath
      ? "local/" + (process.env.CWM_LOCAL_ARM ?? "trained")
      : model;
    console.log("Project:", resolve(process.argv[2]), "  Model:", displayedModel);
    lines.setPrompt("> ");
    if (process.stdin.isTTY) lines.prompt();
    for await (const line of lines) {
      if (line.trim() === "/quit") break;
      try {
        if (line.startsWith("/forecast ")) {
          console.log(
            JSON.stringify({
              kind: "prediction",
              answer: await session.predict(
                decodeAction(line.slice(10)),
                abort.signal,
                focusedPath ? localEditor.forecast : generate,
              ),
            }),
          );
        } else if (
          /^\/local\b/.test(line) ||
          (focusedPath && line.trim() && !line.startsWith("/"))
        ) {
          let path = focusedPath;
          let goal = line;
          if (line.startsWith("/local")) {
            const match = /^\/local\s+(\S+)\s+(.+)$/.exec(line);
            if (!match) throw Error("Usage: /local PATH REQUEST");
            path = match[1]!;
            goal = match[2]!;
          }
          const result = await editLocal(session, localEditor.propose, path!, goal, abort.signal);
          if (focusedPath) focusedPath = path;
          console.log(JSON.stringify({ kind: "local", path, ...result }));
        } else if (/^\/body\b/.test(line)) {
          const match = /^\/body\s+(\S+)\s+(\S+)\s+(.+)$/.exec(line);
          if (!match) throw Error("Usage: /body PATH EXPORT|* REQUEST");
          const generateBody = bodyEndpoint(
            process.env.CWM_PROJECT_URL ?? "http://127.0.0.1:8082",
            model,
          );
          const result = await editBody(session, generateBody, match[1]!, match[3]!, {
            name: match[2] === "*" ? undefined : match[2],
            signal: abort.signal,
          });
          console.log(
            JSON.stringify({
              kind: "body",
              stop: result.stop,
              selection: result.selection,
              selected: result.selected,
              before: result.before,
              calls: result.calls.map(({ kind, reply }) => ({
                kind,
                text: reply.text,
                finish: reply.finish,
                tokens: reply.tokens,
              })),
              writes: result.writes,
            }),
          );
        } else if (/^\/(?:edit|work|return|plan|splice)\b/.test(line)) {
          const match = /^\/(edit|work|return|plan|splice)\s+(\S+)\s+(.+)$/.exec(line);
          if (!match)
            throw Error(
              "Usage: /edit PATH REQUEST, /work PATH REQUEST, /plan PATH REQUEST, /splice PATH REQUEST, or /return PATH FUNC REQUEST",
            );
          const show = (event: import("./agent.ts").TurnEvent) => {
            console.log(
              JSON.stringify({
                kind: "assistant",
                text: event.reply.text,
                finish: event.reply.finish,
              }),
            );
            if (event.observed !== undefined)
              console.log(
                JSON.stringify({
                  kind: "observation",
                  action: event.action,
                  result: event.observed,
                }),
              );
            if (event.run)
              console.log(
                JSON.stringify({ kind: "observation", action: { op: "test" }, result: event.run }),
              );
          };
          const [, command, path, request] = match;
          let result;
          if (command === "splice") {
            result = await spliceFile(session, path!, request!, { signal: abort.signal });
            console.log(JSON.stringify({ kind: "splice", ...result }));
          } else if (command === "plan") {
            result = await planFile(session, path!, request!, {
              signal: abort.signal,
              choose: ranker.choose,
            });
            if (result.prediction)
              console.log(JSON.stringify({ kind: "prediction", ...result.prediction }));
            for (const event of result.events) show(event);
          } else if (command === "return") {
            const args = /^(\S+)\s+(.+)$/.exec(request!);
            if (!args) throw Error("Usage: /return PATH FUNC REQUEST");
            result = await editReturn(session, path!, args[1]!, args[2]!, abort.signal, show);
          } else if (command === "work") {
            result = await workFile(session, path!, request!, {
              signal: abort.signal,
              onEvent: show,
            });
          } else result = await editFile(session, path!, request!, abort.signal, show);
          console.log(JSON.stringify({ kind: "turn", stop: result.stop }));
        } else if (line.trim()) {
          const result = await session.turn(line, {
            signal: abort.signal,
            onEvent: (e) => {
              console.log(
                JSON.stringify({ kind: "assistant", text: e.reply.text, finish: e.reply.finish }),
              );
              if (e.observed !== undefined)
                console.log(
                  JSON.stringify({ kind: "observation", action: e.action, result: e.observed }),
                );
            },
          });
          console.log(JSON.stringify({ kind: "turn", stop: result.stop }));
        }
      } catch (error) {
        console.error(String(error));
      }
      if (abort.signal.aborted) break;
      if (process.stdin.isTTY) lines.prompt();
    }
  } finally {
    lines.close();
    await Promise.all([ranker.close(), localEditor.close()]);
    process.off("SIGINT", cancel);
    process.off("SIGTERM", cancel);
  }
}
