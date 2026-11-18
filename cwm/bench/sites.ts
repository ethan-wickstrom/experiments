import { parseSync, Visitor, visitorKeys } from "oxc-parser";
import type { Frame, Program, Site, Trace } from "../cwm.ts";
import { WorldModel } from "../cwm.ts";

export type Representation = "source" | "filename-blind" | "syntax" | "syntax+operands";
type Point = Omit<Site, "fn">;
const key = (s: Point) => JSON.stringify([s.file, s.line, s.column]);

// Only the single-file diagnostic corpus is in scope. Unknown positions stay source-specific.
function coordinates(p: Program, mode: Representation) {
  if (Object.keys(p.files).length !== 1) throw new Error("Benchmark requires single-file programs");
  const source = p.files[p.entry]!;
  const forward = new Map<string, Point>(),
    reverse = new Map<string, Point>();
  if (mode === "syntax" || mode === "syntax+operands") {
    const syntax = parseSync(p.entry, source);
    if (syntax.errors.length) throw new Error("Invalid benchmark source: " + p.entry);
    const starts = [
      0,
      ...Array.from(source.matchAll(/\r\n|[\r\n\u2028\u2029]/gu), (m) => m.index + m[0].length),
    ];
    type Span = { type: string; start: number; end: number };
    const spans: Span[] = [];
    const capture = (node: Span) => {
      spans.push(node);
    };
    new Visitor(
      Object.fromEntries(
        Object.keys(visitorKeys)
          .filter(
            (k) =>
              k.endsWith("Statement") ||
              k.endsWith("Declaration") ||
              (mode === "syntax+operands" &&
                (k.endsWith("Expression") || k === "Identifier" || k === "Literal")),
          )
          .map((k) => [k, capture]),
      ),
    ).visit(syntax.program);
    const counts = new Map<string, number>();
    const edges = spans
      .map((s) => {
        const n = (counts.get(s.type) ?? 0) + 1;
        counts.set(s.type, n);
        return { start: s.start, end: s.end, type: s.type, n };
      })
      .sort((a, b) => a.end - a.start - (b.end - b.start));
    for (const { start, end, type, n } of edges) {
      for (const [i, offset] of [start, end - 1].entries()) {
        if (offset < start) continue;
        const line = starts.findLastIndex((l) => l <= offset) + 1;
        const point = { file: p.entry, line, column: offset - starts[line - 1]! + 1 };
        if (forward.has(key(point))) continue;
        const anchor = { file: "ast:" + type, line: n, column: i + 1 };
        forward.set(key(point), anchor);
        reverse.set(key(anchor), point);
      }
    }
  }
  const files: Program["files"] = mode === "filename-blind" ? { "@entry": source } : p.files;
  return {
    files,
    encode(this: void, site: Site): Site {
      const point =
        mode === "filename-blind" ? { ...site, file: "@entry" } : forward.get(key(site));
      return point ? { ...point, fn: site.fn } : site;
    },
    decode(site: Site): Site | undefined {
      if (mode === "filename-blind") return { ...site, file: p.entry };
      if (site.file === p.entry) return site;
      const point = reverse.get(key(site));
      return point ? { ...point, fn: site.fn } : undefined;
    },
  };
}

export function fitSites(mode: Representation, train: Trace[]) {
  const codecs = new Map<string, ReturnType<typeof coordinates>>();
  function codec(p: Program) {
    const k = JSON.stringify([p.entry, p.files]);
    if (!codecs.has(k)) codecs.set(k, coordinates(p, mode));
    return codecs.get(k)!;
  }
  const model = new WorldModel().fit(
    train.map((t) => {
      const c = codec(t);
      return {
        ...t,
        files: c.files,
        frames: t.frames.map((f) => ({ ...f, stack: f.stack.map(c.encode) })),
      };
    }),
  );
  return (p: Program, f: Frame) => {
    const c = codec(p);
    const guess = model.predict(c.files, { ...f, stack: f.stack.map(c.encode) });
    if (!guess || !("stack" in guess)) return guess;
    const stack: Site[] = [];
    for (const s of guess.stack) {
      const point = c.decode(s);
      if (!point) return;
      stack.push(point);
    }
    return { ...guess, stack };
  };
}
