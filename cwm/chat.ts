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
  /predict [12,3]                     Predict frames and outcome with the structured CWM
  /resume S,2,1,2,3                   Ask the neural model for the next x,y pause
  /verify [12,3]                      Compare the structured forecast with trusted execution
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
  let feedback: string | undefined;
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
            feedback = undefined;
            console.log("Case recorded", JSON.stringify(example));
            break;
          }
          case "/cases":
            console.log(JSON.stringify(examples));
            break;
          case "/clear":
            examples.length = 0;
            feedback = undefined;
            console.log("Cases cleared");
            break;
          case "/predict": {
            const args = parseArgs(arg),
              prediction = forecast(model, draft, args);
            feedback = JSON.stringify({
              source: "CWM prediction",
              args,
              stop: prediction.stop,
              lastFrame: prediction.frames.at(-1),
              outcome: prediction.stop === "terminal" ? prediction.outcome : undefined,
            });
            console.log("Structured CWM prediction", JSON.stringify(prediction));
            break;
          }
          case "/resume": {
            const answer = await resume(draft, arg);
            feedback = JSON.stringify({
              source: "neural prediction",
              model: modelName,
              current: arg,
              ...answer,
            });
            console.log(feedback);
            break;
          }
          case "/verify": {
            const args = parseArgs(arg),
              report = await verify(model, draft, args);
            const { observedFrom, exactPrefix, complete } = report.comparison;
            feedback = JSON.stringify({
              source: "oracle verification",
              args,
              comparison: report.comparison,
              firstDivergentObservation:
                !complete && observedFrom !== null
                  ? report.observed.frames[observedFrom + exactPrefix]
                  : undefined,
              observedOutcome: report.observed.outcome,
              predictionStop: report.prediction.stop,
            });
            console.log("Structured CWM vs V8 oracle", JSON.stringify(report));
            break;
          }
          case "/check":
            feedback = JSON.stringify({
              source: "CWM assessment",
              cases: assess(model, draft, examples),
            });
            console.log(feedback);
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
              : await propose({ draft, examples, instructions: [...instructions, line], feedback });
            if (!source?.trim()) throw Error("Provide a draft before /repair");
            const result = await plan(model, { ...draft, files: { [entry]: source } }, examples);
            draft = result.draft;
            if (!command) {
              instructions.push(line);
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
            feedback = JSON.stringify({
              source: "CWM assessment",
              status: result.status,
              cases: result.assessment,
            });
            console.log(feedback);
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
