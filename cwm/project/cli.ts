import { createInterface } from "node:readline";
import { resolve } from "node:path";
import { ProjectSession, endpoint } from "./agent.ts";
import { openProject } from "./workspace.ts";
import { decodeAction } from "./protocol.ts";
import { workFile } from "./work.ts";
import { editFile } from "./directed.ts";

if (!process.argv[2] || process.argv.includes("--help")) {
  console.log(
    "Usage: bun run project DIRECTORY\nEnter a request, /edit PATH REQUEST, /work PATH REQUEST (C2), /forecast ACTION_JSON, or /quit. Writes update the project. Free-action turns allow eight actions. Directed edits allow two proposals with a test run after each write.",
  );
} else {
  const project = await openProject(resolve(process.argv[2]));
  const model = process.env.CWM_PROJECT_MODEL ?? "minicpm5-joint";
  const generate = endpoint(
    process.env.CWM_PROJECT_URL ?? "http://127.0.0.1:8082/v1/chat/completions",
    model,
  );
  const session = new ProjectSession(project, generate);
  const abort = new AbortController();
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
    console.log("Project:", resolve(process.argv[2]), "  Model:", model);
    lines.setPrompt("> ");
    if (process.stdin.isTTY) lines.prompt();
    for await (const line of lines) {
      if (line.trim() === "/quit") break;
      try {
        if (line.startsWith("/forecast ")) {
          console.log(
            JSON.stringify({
              kind: "prediction",
              answer: await session.predict(decodeAction(line.slice(10)), abort.signal),
            }),
          );
        } else if (line.startsWith("/edit ") || line.startsWith("/work ")) {
          const match = /^\/(?:edit|work) (\S+)\s+(.+)$/.exec(line);
          if (!match) throw Error("Usage: /edit PATH REQUEST");
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
          const result = line.startsWith("/work ")
            ? await workFile(session, match[1]!, match[2]!, { signal: abort.signal, onEvent: show })
            : await editFile(session, match[1]!, match[2]!, abort.signal, show);
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
    process.off("SIGINT", cancel);
    process.off("SIGTERM", cancel);
  }
}
