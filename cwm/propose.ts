import { readFile } from "node:fs/promises";
import { entryFunction, scalar } from "./structured/scalar.ts";
import { parseSync } from "oxc-parser";
import { type Draft, type Example } from "./prompt.ts";

export type Request = {
  draft: Draft;
  instructions: readonly string[];
  examples: readonly Example[];
};
export const modelName = process.env.CWM_CHAT_MODEL ?? "typescript-cwm-minicpm5";

export async function propose({ draft, instructions, examples }: Request): Promise<string> {
  const source = draft.files[draft.entry]!;
  const system = [
    "Implement the user's request as TypeScript. Respond with just the complete source file in one code block.",
    "The entry point must start with export function " +
      draft.fn +
      " and use descriptive, typed parameters.",
    "For arithmetic use a single return expression. For control flow, use braced if/else, while, and assignments to parameters. Avoid temporary variable declarations when the same result can be expressed directly.",
    "Example syntax: export function " +
      draft.fn +
      "(left: number, right: number): number { return left - right; }",
    "Use the requested behavior. Example calls are specifications and belong outside the source.",
  ].join("\n");
  const context = [
    ...instructions.slice(0, -1).map((s) => "Earlier request: " + s),
    ...(source ? ["Current TypeScript source:\n" + source] : []),
    ...examples.map(
      (c) =>
        "Required: " +
        draft.fn +
        "(" +
        c.args.map((a) => JSON.stringify(a)).join(", ") +
        ") returns " +
        JSON.stringify(c.returns) +
        (c.visits?.length ? "; ordered local states " + JSON.stringify(c.visits) : ""),
    ),
    "Current request: " + instructions.at(-1),
  ].join("\n\n");
  const text = await complete(
    [
      { role: "system", content: system },
      { role: "user", content: context },
    ],
    0.25,
    1536,
  );
  const fenced = [...text.matchAll(/^```(?:typescript|ts)?[ \t]*\r?\n([\s\S]*?)^```[ \t]*\r?$/gm)];
  if (fenced.length > 1) throw Error("Expected one source file, received several code blocks");
  const code = fenced[0]?.[1] ?? text;
  const ast = parseSync(draft.entry, code);
  if (ast.errors.length) throw Error("Invalid TypeScript proposal: " + ast.errors[0]!.message);
  if (
    !ast.program.body.some(
      (n) =>
        n.type === "ExportNamedDeclaration" &&
        n.declaration?.type === "FunctionDeclaration" &&
        n.declaration.id?.name === draft.fn,
    )
  )
    throw Error("The proposal needs a named function export " + draft.fn);
  return code;
}

async function complete(
  messages: { role: "system" | "user"; content: string }[],
  temperature: number,
  limit: number,
) {
  const endpoint = process.env.CWM_CHAT_URL ?? "http://127.0.0.1:8080/v1/chat/completions";
  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: modelName,
        messages,
        temperature,
        top_p: 0.95,
        min_p: 0,
        max_tokens: limit,
        chat_template_kwargs: { enable_thinking: false },
      }),
      signal: AbortSignal.timeout(120000),
    });
  } catch (error) {
    throw Error(
      "Model unavailable. Start llama-server as described in PROMPTING.md. " + String(error),
    );
  }
  if (!response.ok)
    throw Error(
      "Model request failed (" + response.status + "): " + (await response.text()).slice(0, 500),
    );
  const body = (await response.json()) as {
    choices?: { message?: { content?: unknown }; finish_reason?: string }[];
  };
  const choice = body.choices?.[0];
  if (choice?.finish_reason !== "stop" || typeof choice.message?.content !== "string")
    throw Error("Incomplete model response");
  return choice.message.content.trim();
}

/** The observation language is the one used to train the adapter. Preserve malformed answers for inspection. */
export async function resume(draft: Draft, current: string) {
  const source = draft.files[draft.entry]!;
  const { names } = entryFunction(draft.entry, source, draft.fn);
  if (names.length !== 2 || !names.includes("x") || !names.includes("y"))
    throw Error("The neural pause experiment requires exactly the parameters x and y");
  if (
    !/^S,[1-9][0-9]*,[1-9][0-9]*,-?(?:0|[1-9][0-9]*),-?(?:0|[1-9][0-9]*)$/.test(current) ||
    !current
      .split(",")
      .slice(1)
      .every((s) => scalar(Number(s)))
  )
    throw Error("Expected an observed step S,line,column,x,y with exact integers");
  const template = await readFile(new URL("./bench/minicpm/resume.txt", import.meta.url), "utf8");
  const content = template
    .trimEnd()
    .replace(/\{(source|current)\}/g, (_, field: string) =>
      field === "source" ? source : current,
    );
  return complete([{ role: "user", content }], 0, 32);
}
