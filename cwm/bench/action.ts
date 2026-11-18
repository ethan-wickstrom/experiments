import { parseSync, type Expression } from "oxc-parser";
import { WorldModel, type Frame, type Program, type Site, type Trace, type Json } from "../cwm.ts";

// Deliberately one lexical scope. Refuse unknown syntax rather than erase its meaning.
function actionCodec(p: Program) {
  const source = p.files[p.entry];
  if (source === undefined || Object.keys(p.files).length !== 1) return;
  const { program, errors } = parseSync(p.entry, source);
  const item = program.body[0];
  if (errors.length || program.body.length !== 1 || item?.type !== "ExportNamedDeclaration") return;
  const fn = item.declaration;
  if (
    fn?.type !== "FunctionDeclaration" ||
    fn.async ||
    fn.generator ||
    fn.id?.name !== p.fn ||
    !fn.body
  )
    return;
  const names: string[] = [];
  function declare(name: string) {
    if (names.includes(name)) return false;
    names.push(name);
    return true;
  }
  for (const param of fn.params) if (param.type !== "Identifier" || !declare(param.name)) return;
  const starts = [
    0,
    ...Array.from(source.matchAll(/\r\n|[\r\n\u2028\u2029]/gu), (m) => m.index + m[0].length),
  ];
  const forward = new Map<number, Site>(),
    reverse = new Map<string, Site>(),
    counts = new Map<string, number>();
  const key = (s: Site) => JSON.stringify([s.file, s.line, s.column, s.fn]);
  for (const stmt of fn.body.body) {
    const offsets = [stmt.start];
    function shape(expr: Expression): Json | undefined {
      offsets.push(expr.start);
      if (expr.type === "Identifier") {
        const slot = names.indexOf(expr.name);
        return slot < 0 ? undefined : ["binding", slot];
      }
      if (
        expr.type === "Literal" &&
        (typeof expr.value === "boolean" ||
          (typeof expr.value === "number" && Number.isFinite(expr.value)))
      )
        return ["literal", expr.value];
      if (expr.type === "ParenthesizedExpression") return shape(expr.expression);
      if (expr.type === "BinaryExpression" && expr.left.type !== "PrivateIdentifier") {
        const left = shape(expr.left),
          right = shape(expr.right);
        if (left && right) return [expr.operator, left, right];
      }
    }
    let action: Json;
    if (stmt.type === "ReturnStatement" && stmt.argument) {
      const value = shape(stmt.argument);
      if (!value) return;
      action = ["return", value];
    } else if (
      stmt.type === "VariableDeclaration" &&
      stmt.kind === "const" &&
      stmt.declarations.length === 1
    ) {
      const d = stmt.declarations[0]!;
      if (d.id.type !== "Identifier" || !d.init) return;
      const init = shape(d.init);
      if (!init || !declare(d.id.name)) return;
      action = ["const", names.length - 1, init];
    } else return;
    const file = "action:" + JSON.stringify(action);
    const occurrence = (counts.get(file) ?? 0) + 1;
    counts.set(file, occurrence);
    for (const [j, offset] of offsets.entries()) {
      const line = starts.findLastIndex((s) => s <= offset) + 1;
      const site = { file: p.entry, line, column: offset - starts[line - 1]! + 1, fn: p.fn };
      const anchor = { file, line: occurrence, column: j + 1, fn: p.fn };
      if (!forward.has(offset)) forward.set(offset, anchor);
      reverse.set(key(anchor), site);
    }
  }
  function frame(f: Frame, inverse: boolean): Frame | undefined {
    if (f.stack.length !== 1) return;
    const site = f.stack[0]!;
    const mapped = inverse
      ? reverse.get(key(site))
      : site.file === p.entry && site.fn === p.fn
        ? forward.get((starts[site.line - 1] ?? NaN) + site.column - 1)
        : undefined;
    if (!mapped) return;
    const locals: Frame["locals"] = Object.create(null);
    for (const [name, value] of Object.entries(f.locals)) {
      const slot = inverse ? Number(name) : names.indexOf(name);
      if (!Number.isSafeInteger(slot) || slot < 0 || slot >= names.length) return;
      locals[inverse ? names[slot]! : String(slot)] = value;
    }
    return { ...f, stack: [mapped], locals: { ...locals } };
  }
  return frame;
}

export function fitActions(train: Trace[]) {
  const model = new WorldModel().fit(
    train.flatMap((t) => {
      const codec = actionCodec(t);
      if (!codec) return [];
      // Preserve every real edge: an unrecognized site is private to the source, not deleted.
      return [{ ...t, files: {}, frames: t.frames.map((f) => codec(f, false) ?? f) }];
    }),
  );
  const codecs = new Map<string, ReturnType<typeof actionCodec>>();
  return (p: Program, f: Frame) => {
    const key = JSON.stringify([p.entry, p.fn, p.files]);
    if (!codecs.has(key)) codecs.set(key, actionCodec(p));
    const codec = codecs.get(key),
      frame = codec?.(f, false);
    if (!codec || !frame) return;
    const next = model.predict({}, frame);
    return next && "stack" in next ? codec(next, true) : next;
  };
}
