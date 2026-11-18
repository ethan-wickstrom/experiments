import { SourceMap } from "node:module";
import { parseSync, Visitor, type Expression, type Statement } from "oxc-parser";
import { transformSync } from "oxc-transform";
import type { Site } from "../cwm.ts";
import { entryFunction, expressions, type Expr } from "./scalar.ts";

type Flow =
  | { kind: "set"; slot: number; next: number }
  | { kind: "return" }
  | { kind: "if" | "while"; yes: number; no: number };
export type Instruction = Flow & {
  id: number;
  expr: Expr;
  start: number;
  end: number;
  anchors: Record<string, number>;
};

function leaf(e: Expression, right: boolean): Expression {
  if (e.type === "ParenthesizedExpression") return leaf(e.expression, right);
  if (e.type === "BinaryExpression" && e.left.type !== "PrivateIdentifier")
    return leaf(right ? e.right : e.left, right);
  return e;
}

// This graph supplies possible transfers and expression roles. No breakpoint list is consulted.
export function compile(file: string, fn: string, source: string, mapReturns = false) {
  const { names, statements } = entryFunction(file, source, fn);
  const read = expressions(names);
  const nodes: Instruction[] = [];
  let serial = 0;
  function block(stmts: Statement[], after: number): number {
    let next = after;
    for (const s of stmts.toReversed()) {
      const id = serial++;
      let flow: Flow, e: Expression;
      if (s.type === "ReturnStatement" && s.argument) {
        flow = { kind: "return" };
        e = s.argument;
      } else if (
        s.type === "ExpressionStatement" &&
        s.expression.type === "AssignmentExpression" &&
        s.expression.operator === "=" &&
        s.expression.left.type === "Identifier" &&
        names.includes(s.expression.left.name)
      ) {
        flow = { kind: "set", next, slot: names.indexOf(s.expression.left.name) };
        e = s.expression.right;
      } else if (
        s.type === "IfStatement" &&
        s.consequent.type === "BlockStatement" &&
        (!s.alternate || s.alternate.type === "BlockStatement")
      ) {
        flow = {
          kind: "if",
          yes: block(s.consequent.body, next),
          no: s.alternate ? block(s.alternate.body, next) : next,
        };
        e = s.test;
      } else if (
        s.type === "WhileStatement" &&
        s.body.type === "BlockStatement" &&
        s.body.body.length
      ) {
        flow = { kind: "while", yes: block(s.body.body, id), no: next };
        e = s.test;
      } else throw Error("Unsupported instruction: " + s.type);
      const first = leaf(e, false),
        last = leaf(e, true);
      const end = flow.kind === "if" || flow.kind === "while" ? e.end : s.end;
      nodes[id] = {
        ...flow,
        id,
        expr: read(e),
        start: s.start,
        end,
        anchors: {
          statement: s.start,
          lastCharacter: end - 1,
          expression: e.start,
          expressionLast: e.end - 1,
          firstLeaf: first.start,
          lastLeaf: last.start,
          lastLeafEnd: last.end - 1,
        },
      };
      next = id;
    }
    return next;
  }
  const entry = block(statements, -1);
  const starts = [
    0,
    ...Array.from(source.matchAll(/\r\n|[\r\n\u2028\u2029]/gu), (m) => m.index + m[0].length),
  ];
  if (mapReturns) {
    const { code, map, errors } = transformSync(file, source, {
      sourceType: "module",
      sourcemap: true,
      typescript: { rewriteImportExtensions: true },
    });
    if (!map || errors.length) throw Error("Missing emitted source map");
    const sm = new SourceMap({
      ...map,
      file,
      sources: [file],
      sourcesContent: [source],
      sourceRoot: "",
    });
    const jsLines = [
      0,
      ...Array.from(code.matchAll(/\r\n|[\r\n\u2028\u2029]/gu), (m) => m.index + m[0].length),
    ];
    const original = (offset: number) => {
      const line = jsLines.findLastIndex((start) => start <= offset);
      const entry = sm.findEntry(line, offset - jsLines[line]!);
      if (!("originalLine" in entry) || !entry.originalSource) return;
      const base = starts[entry.originalLine];
      return base === undefined ? undefined : base + entry.originalColumn;
    };
    const byStart = new Map(nodes.filter((n) => n.kind === "return").map((n) => [n.start, n]));
    new Visitor({
      ReturnStatement(s) {
        const start = original(s.start),
          end = original(s.end);
        const n = start === undefined ? undefined : byStart.get(start);
        if (n && end !== undefined && end >= n.start && end < n.end) n.anchors.mappedReturn = end;
      },
    }).visit(parseSync("emitted.js", code).program);
  }
  function position(site: Site) {
    const start = starts[site.line - 1];
    if (start === undefined || site.fn !== fn || site.file !== file || site.column < 1) return;
    const pos = start + site.column - 1;
    if (pos >= (starts[site.line] ?? source.length)) return;
    return pos;
  }
  return {
    entry,
    names,
    nodes,
    position,
    at(pos: number) {
      return nodes.find((n) => n.start <= pos && pos < n.end);
    },
    site(pos: number): Site {
      const line = starts.findLastIndex((start) => start <= pos) + 1;
      return { file, fn, line, column: pos - starts[line - 1]! + 1 };
    },
  };
}
export type Graph = ReturnType<typeof compile>;
