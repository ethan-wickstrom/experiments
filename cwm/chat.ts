import { readFile, writeFile } from "node:fs/promises";
import { basename } from "node:path";
import { createInterface } from "node:readline";
import { isDeepStrictEqual as equal } from "node:util";
import { modelName, propose, resume } from "./propose.ts";
import {
  assess,
  forecast,
  parseArgs,
  parseExample,
  plan,
  trainingModel,
  verify,
  type Draft,
  type Example,
} from "./prompt.ts";

const help = `Usage: bun run chat [file.ts [exportName]]
Write a request in ordinary language to create or revise the current function.
  /case {"args":[12,3],"returns":36}   Add or replace an expected behavior
  /cases                              Show current expectations
  /clear                              Clear expectations
  /predict [12,3]                     Predict raw frames and the outcome
  /resume S,2,1,2,3                   Ask the neural model for the next x,y pause
  /verify [12,3]                      Execute trusted source and compare the oracle trace
  /check                              Compare predictions with all cases
  /repair                             Search single edits using the CWM
  /source                             Show the current draft
  /save new-file.ts                   Write a new file
  /quit                               End this session`;

export async function chat(argv: string[]) {
  if (argv.includes("--help") || argv.includes("-h")) {
    console.log(help);
    return;
  }
  if (argv.length > 2) throw Error(help);
  const [file, fn = "run"] = argv,
    entry = file ? basename(file) : "main.ts";
  let draft: Draft = { entry, fn, files: { [entry]: file ? await readFile(file, "utf8") : "" } };
  const examples: Example[] = [],
    instructions: string[] = [];
  const model = await trainingModel();
  const interactive = Boolean(process.stdin.isTTY && process.stdout.isTTY);
  const lines = createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: interactive,
  });
  if (interactive) {
    console.log(help);
    lines.setPrompt("cwm> ");
    lines.prompt();
  }
  try {
    for await (const input of lines) {
      try {
        const line = input.trim();
        if (!line) continue;
        if (line === "/quit") break;
        const match = /^(\/\S+)(?:\s+([\s\S]*))?$/.exec(line);
        const command = match?.[1],
          arg = match?.[2] ?? "";
        switch (command) {
          case "/help":
            console.log(help);
            break;
          case "/source":
            console.log(draft.files[entry]);
            break;
          case "/case": {
            const example = parseExample(arg);
            const idx = examples.findIndex((c) => equal(c.args, example.args));
            if (idx < 0) examples.push(example);
            else examples[idx] = example;
            console.log("Case recorded", JSON.stringify(example));
            break;
          }
          case "/cases":
            console.log(JSON.stringify(examples));
            break;
          case "/clear":
            examples.length = 0;
            console.log("Cases cleared");
            break;
          case "/predict":
            console.log("CWM prediction", JSON.stringify(forecast(model, draft, parseArgs(arg))));
            break;
          case "/resume":
            console.log("Neural prediction (" + modelName + ")", await resume(draft, arg));
            break;
          case "/verify":
            console.log(
              "Oracle verification",
              JSON.stringify(await verify(model, draft, parseArgs(arg))),
            );
            break;
          case "/check":
            console.log("CWM assessment", JSON.stringify(assess(model, draft, examples)));
            break;
          case "/save":
            if (!arg || !draft.files[entry])
              throw Error("Use /save new-file.ts with a nonempty draft");
            await writeFile(arg, draft.files[entry]!, { flag: "wx" });
            console.log("Saved", arg);
            break;
          case undefined:
          case "/repair": {
            if (command && !examples.length) throw Error("Provide a /case before /repair");
            const source = command
              ? draft.files[entry]
              : await propose({ draft, examples, instructions: [...instructions, line] });
            if (!source?.trim()) throw Error("Provide a draft before /repair");
            const result = await plan(model, { ...draft, files: { [entry]: source } }, examples);
            draft = result.draft;
            if (!command) instructions.push(line);
            if (!command) {
              console.log("Language proposal (" + modelName + ")");
              console.log(source);
            }
            if (result.status === "repaired") {
              console.log(
                "CWM edit",
                JSON.stringify({ before: result.originalAssessment, edit: result.edit }),
              );
              console.log(draft.files[entry]);
            }
            console.log(
              "CWM assessment",
              JSON.stringify({ status: result.status, cases: result.assessment }),
            );
            break;
          }
          default:
            throw Error("Unknown command. Use /help");
        }
      } catch (error) {
        console.error(error instanceof Error ? error.message : String(error));
        if (!interactive) process.exitCode = 1;
      } finally {
        if (interactive) lines.prompt();
      }
    }
  } finally {
    lines.close();
  }
}

if (import.meta.main) await chat(process.argv.slice(2));
