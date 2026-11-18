import { parseSync, type Expression } from "oxc-parser";

export type Expr = { slot: number } | { literal: number } | { op: string; l: Expr; r: Expr };
export interface Plan {
  names: string[];
  params: number;
  code: { line: number; expr: Expr; returns: boolean }[];
}
export function scalar(n: unknown): n is number {
  return typeof n === "number" && Number.isSafeInteger(n) && !Object.is(n, -0);
}

// Static scaffolding, not a learned part: lexical slots and straight-line sequencing.
export function plan(source: string): Plan {
  const syntax = parseSync("input.ts", source);
  const [top] = syntax.program.body;
  const f = top?.type === "ExportNamedDeclaration" ? top.declaration : null;
  if (
    syntax.errors.length ||
    syntax.program.body.length !== 1 ||
    f?.type !== "FunctionDeclaration" ||
    f.id?.name !== "run" ||
    f.async ||
    f.generator ||
    !f.body
  )
    throw new Error("Expected a single synchronous exported run function");
  const names: string[] = [];
  for (const p of f.params) {
    if (p.type !== "Identifier" || names.includes(p.name)) throw new Error("Invalid parameter");
    names.push(p.name);
  }
  function read(e: Expression): Expr {
    if (e.type === "ParenthesizedExpression") return read(e.expression);
    if (e.type === "Literal" && scalar(e.value)) return { literal: e.value };
    if (e.type === "Identifier" && names.includes(e.name)) return { slot: names.indexOf(e.name) };
    if (e.type === "BinaryExpression" && e.left.type !== "PrivateIdentifier")
      return { op: e.operator, l: read(e.left), r: read(e.right) };
    throw new Error("Unsupported expression: " + e.type);
  }
  const params = names.length;
  const code: Plan["code"] = [];
  for (const [i, s] of f.body.body.entries()) {
    const line = source.slice(0, s.start).split("\n").length;
    if (line === code.at(-1)?.line || source.slice(s.start, s.end).includes("\n"))
      throw new Error("Projection requires one statement per line");
    if (s.type === "ReturnStatement" && s.argument && i === f.body.body.length - 1) {
      code.push({ line, expr: read(s.argument), returns: true });
    } else if (
      s.type === "VariableDeclaration" &&
      s.kind === "const" &&
      s.declarations.length === 1
    ) {
      const d = s.declarations[0]!;
      if (d.id.type !== "Identifier" || names.includes(d.id.name) || !d.init)
        throw new Error("Expected a fresh scalar binding");
      code.push({ line, expr: read(d.init), returns: false });
      names.push(d.id.name);
    } else throw new Error("Unsupported statement: " + s.type);
  }
  if (!code.at(-1)?.returns) throw new Error("Expected final return");
  return { names, params, code };
}
