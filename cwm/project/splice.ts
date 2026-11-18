import {
  parseSync,
  Visitor,
  type BinaryExpression,
  type LogicalExpression,
  type Span,
} from "oxc-parser";
import { type Completion, type ProjectSession } from "./agent.ts";
import { projectJson } from "./protocol.ts";
import { type ToolRun } from "./sandbox.ts";
import { maxFileBytes, sourcePath, testPath } from "./workspace.ts";

type Site = Span & { role: string };
// General TypeScript operator vocabulary. The model supplies the operation at the selected AST span.
const operators: Readonly<Record<string, string>> = {
  add: "+",
  subtract: "-",
  multiply: "*",
  divide: "/",
  remainder: "%",
  exponentiate: "**",
  equal: "==",
  "not equal": "!=",
  "strictly equal": "===",
  "strictly not equal": "!==",
  "less than": "<",
  "at most": "<=",
  "greater than": ">",
  "at least": ">=",
  "logical and": "&&",
  "logical or": "||",
  "nullish coalescing": "??",
  "bitwise or": "|",
  "bitwise and": "&",
  "bitwise xor": "^",
  "left shift": "<<",
  "right shift": ">>",
  "unsigned right shift": ">>>",
  "property in object": "in",
  "instance of": "instanceof",
};

const escapePattern = (s: string) => s.replace(/[|\\{}()[\]^$+*?.]/g, "\\$&");
const operatorFamilies = [
  ["+", "-", "*", "/", "%", "**"],
  ["==", "!=", "===", "!==", "<", "<=", ">", ">="],
  ["&&", "||", "??"],
  ["|", "&", "^", "<<", ">>", ">>>"],
  ["in", "instanceof"],
];
function lineSlot(source: string, site: Site, seen: ReadonlyMap<string, ToolRun>) {
  const start = source.lastIndexOf("\n", site.start - 1) + 1;
  const next = source.indexOf("\n", site.end);
  const prefix = source.slice(start, site.start).trimStart().slice(-96);
  const suffix = source
    .slice(site.end, next < 0 ? source.length : next)
    .trimEnd()
    .slice(0, 96);
  const old = source.slice(site.start, site.end);
  const id = site.start + "-" + site.end + " " + site.role;
  const token = site.role === "property" ? "[a-zA-Z_$][a-zA-Z0-9_$]*" : "[^;{}\r\n]+";
  return {
    id,
    prefix,
    suffix,
    site,
    old,
    operations:
      site.role === "operator"
        ? Object.keys(operators).filter(
            (key) =>
              operators[key] !== old &&
              operatorFamilies.find((family) => family.includes(old))?.includes(operators[key]!) &&
              !seen.has(source.slice(0, site.start) + operators[key] + source.slice(site.end)),
          )
        : undefined,
    pattern: "^" + escapePattern(prefix) + token + escapePattern(suffix) + "$",
  };
}
export function spliceSites(path: string, source: string) {
  const parsed = parseSync(path, source, { preserveParens: true });
  if (parsed.errors.length) return [];
  const sites: Site[] = [];
  function add(role: string, node?: (Span & { type: string }) | null) {
    if (!node || node.type.endsWith("FunctionExpression")) return;
    sites.push({ role, start: node.start, end: node.end });
  }
  function binary(node: BinaryExpression | LogicalExpression) {
    const gap = source.slice(node.left.end, node.right.start);
    if (gap.trim() === node.operator) {
      const start = node.left.end + gap.indexOf(node.operator);
      sites.push({ role: "operator", start, end: start + node.operator.length });
    }
    add("left operand", node.left);
    add("right operand", node.right);
  }
  new Visitor({
    VariableDeclarator: (n) => add("initializer", n.init),
    AssignmentExpression: (n) => add("assigned value", n.right),
    AssignmentPattern: (n) => add("default", n.right),
    IfStatement: (n) => add("condition", n.test),
    WhileStatement: (n) => add("condition", n.test),
    DoWhileStatement: (n) => add("condition", n.test),
    ForStatement: (n) => add("condition", n.test),
    ConditionalExpression: (n) => {
      add("condition", n.test);
      add("then value", n.consequent);
      add("else value", n.alternate);
    },
    MemberExpression: (n) => add(n.computed ? "index" : "property", n.property),
    CallExpression: (n) => n.arguments.forEach((arg) => add("argument", arg)),
    ArrayExpression: (n) => n.elements.forEach((el) => add("element", el)),
    BinaryExpression: binary,
    LogicalExpression: binary,
  }).visit(parsed.program);
  return sites.sort((a, b) => a.start - b.start || b.end - a.end);
}

/** Re-parse the whole file and require the replacement to occupy the same syntactic role and span. */
export function spliceSource(path: string, source: string, site: Site, replacement: string) {
  const fragment = replacement.trim();
  if (!fragment) return;
  const text = source.slice(0, site.start) + fragment + source.slice(site.end);
  if (Buffer.byteLength(text) > maxFileBytes) return;
  const end = site.start + fragment.length;
  if (
    spliceSites(path, text).some(
      (s) => s.role === site.role && s.start === site.start && s.end === end,
    )
  )
    return text;
}

export type SpliceTrial = {
  index: number;
  parent: number | null;
  request: string;
  reply?: Completion;
  error?: string;
  sampling: { temperature: number; seed: number };
  elapsedMs: number;
  status:
    | "generation-error"
    | "test-error"
    | "incomplete"
    | "invalid"
    | "unchanged"
    | "duplicate"
    | "tested";
  site?: Site;
  replacement?: string;
  text?: string;
  run?: ToolRun;
};
export const visiblePass = (run: ToolRun) =>
  run.exit === 0 && /^\s*[1-9]\d* pass$/m.test(run.stderr);

/** Sample token and expression edits on the request state, then on the first tested draft. */
export async function spliceFile(
  session: ProjectSession,
  path: string,
  goal: string,
  { feedback = true, signal }: { feedback?: boolean; signal?: AbortSignal } = {},
) {
  if (!sourcePath(path) || !/\.(?:[cm]?ts|tsx)$/i.test(path) || testPath(path))
    throw Error("Select a TypeScript implementation file");
  await session.begin(goal);
  if (!session.project.files.has(path)) throw Error("Missing target: " + path);
  for (const file of session.state().files) await session.act({ op: "read", path: file }, signal);
  const base = new Map(session.observedFiles);
  const original = base.get(path)!;
  const requests = session.history.flatMap((e) => ("user" in e ? [e.user] : []));
  const baseline = await session.act({ op: "test" }, signal);
  const trials: SpliceTrial[] = [];
  let selected: number | null = null;
  let reason: string | undefined;
  let parent: SpliceTrial | undefined;
  const seen = new Map<string, ToolRun>([[original, baseline.run!]]);
  for (let round = 0; round < 2; round++) {
    if (round === 1) parent = trials.find((t) => t.status === "tested");
    const source = parent?.text ?? original;
    const sites = spliceSites(path, source);
    if (!sites.length) {
      reason = "no-sites";
      break;
    }
    const files = Object.fromEntries(new Map(base).set(path, source));
    const run = parent?.run ?? baseline.run!;
    const diagnostic =
      feedback && round === 1 && !visiblePass(run)
        ? { exit: run.exit, stderr: run.stderr.slice(-1200), stdout: run.stdout.slice(-200) }
        : undefined;
    for (const [sample, sampling] of [
      { temperature: round === 0 ? 0 : 0.35, seed: round === 0 ? 11 : 31 },
      { temperature: 0.75, seed: round === 0 ? 17 : 37 },
      { temperature: 0.9, seed: round === 0 ? 23 : 41 },
      { temperature: 0.9, seed: round === 0 ? 29 : 43 },
    ].entries()) {
      signal?.throwIfAborted();
      const all = sites
        .map((s) => lineSlot(source, s, seen))
        .filter((s) => s.operations?.length !== 0);
      if (!all.length) {
        reason = "no-new-sites";
        break;
      }
      const partition = all.filter(
        ({ site }) => (site.role === "operator" || site.role === "property") === (sample % 2 === 0),
      );
      const slots = partition.length ? partition : all;
      const menu = slots.map(({ id, prefix, suffix, old, operations }) => ({
        id,
        line: prefix + "«" + old + "»" + suffix,
        operations,
      }));
      const request =
        "Correct one marked TypeScript fragment for the latest request. Choose the site, then name the new operator in English or write the edited line for an expression or property. The « » marks delimit the editable span.\n" +
        projectJson({ files, path, sites: menu, diagnostic, requests });
      if (Buffer.byteLength(request) > 24000 || sites.length > 96) {
        reason = "context-limit";
        break;
      }
      const alternatives = slots.map(({ id, site, operations, pattern }) => {
        const operator = site.role === "operator";
        const output = operator ? "operation" : "line";
        return {
          type: "object" as const,
          properties: {
            site: { const: id },
            [output]: operator
              ? {
                  type: "string" as const,
                  enum: operations!,
                }
              : { type: "string" as const, pattern },
          },
          required: ["site", output],
          additionalProperties: false,
        };
      });
      const grammar = { oneOf: alternatives };
      const start = performance.now();
      const trial: SpliceTrial = {
        index: trials.length,
        parent: parent?.index ?? null,
        sampling,
        request,
        elapsedMs: 0,
        status: "invalid",
      };
      trials.push(trial);
      try {
        trial.reply = await session.generate(request, 128, signal, grammar, true, sampling);
      } catch (error) {
        signal?.throwIfAborted();
        trial.status = "generation-error";
        trial.error = String(error);
        continue;
      } finally {
        trial.elapsedMs = Math.round(performance.now() - start);
      }
      const reply = trial.reply;
      if (reply.finish !== "stop") {
        trial.status = "incomplete";
        continue;
      }
      let answer: { site?: string; line?: string; operation?: string } | null;
      try {
        answer = JSON.parse(reply.text);
      } catch {
        continue;
      }
      if (typeof answer?.site !== "string") continue;
      const slot = slots.find((s) => s.id === answer.site);
      if (!slot) continue;
      const { site } = slot;
      trial.site = site;
      if (site.role === "operator") {
        if (typeof answer.operation !== "string" || !slot.operations?.includes(answer.operation))
          continue;
        trial.replacement = operators[answer.operation]!;
      } else {
        if (
          typeof answer.line !== "string" ||
          !answer.line.startsWith(slot.prefix) ||
          !answer.line.endsWith(slot.suffix)
        )
          continue;
        trial.replacement = answer.line.slice(
          slot.prefix.length,
          answer.line.length - slot.suffix.length,
        );
        if (!new RegExp(slot.pattern).test(answer.line)) continue;
      }
      const text = spliceSource(path, source, site, trial.replacement);
      if (text === undefined) continue;
      trial.text = text;
      trial.run = seen.get(text);
      if (trial.run) {
        trial.status = source === text || original === text ? "unchanged" : "duplicate";
        continue;
      }
      try {
        trial.run = await session.test(new Map(base).set(path, text), signal);
      } catch (error) {
        signal?.throwIfAborted();
        trial.status = "test-error";
        trial.error = String(error);
        continue;
      }
      trial.status = "tested";
      seen.set(text, trial.run);
      if (selected === null && visiblePass(trial.run)) selected = trial.index;
    }
    if (reason) break;
  }
  const winner = selected === null ? undefined : trials[selected];
  let verification: ToolRun | undefined;
  let stop = "no-visible-pass";
  if (winner) {
    const write = await session.act({ op: "write", path, text: winner.text! }, signal);
    stop = write.observed;
    if (stop === "written") {
      verification = (await session.act({ op: "test" }, signal)).run;
      stop = visiblePass(verification!) ? "tested" : "verification-failed";
    }
  }
  return {
    stop: winner ? stop : (reason ?? stop),
    reason,
    selected,
    baseline: baseline.run!,
    trials,
    verification,
  };
}
