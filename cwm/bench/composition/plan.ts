import { entryFunction, expressions, type Expr } from "../../structured/scalar.ts";
export { entryFunction, expressions, scalar, type Expr } from "../../structured/scalar.ts";

export interface Plan {
  names: string[];
  params: number;
  code: { line: number; expr: Expr; returns: boolean }[];
}
// Static scaffolding, not a learned part: lexical slots and straight-line sequencing.
export function plan(source: string): Plan {
  const { names, statements } = entryFunction("input.ts", source),
    read = expressions(names);
  const params = names.length;
  const code: Plan["code"] = [];
  for (const [i, s] of statements.entries()) {
    const line = source.slice(0, s.start).split("\n").length;
    if (line === code.at(-1)?.line || source.slice(s.start, s.end).includes("\n"))
      throw new Error("Projection requires one statement per line");
    if (s.type === "ReturnStatement" && s.argument && i === statements.length - 1) {
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
