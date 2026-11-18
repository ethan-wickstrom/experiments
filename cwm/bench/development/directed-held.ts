type DirectedProject = {
  id: string;
  path: string;
  files: Record<string, string>;
  turns: { goal: string; accept: string }[];
};

// Each lineage stays held across both turns. The grader owns accept; the editor sees files and goals.
export const directedHeld: DirectedProject[] = [
  {
    id: "invoice-lines",
    path: "invoice.ts",
    files: {
      "invoice.ts": "",
      "invoice.test.ts": `import { expect, test } from "bun:test";
import { totalCents } from "./invoice";

test("sum extended prices", () => {
  expect(totalCents([{ units: 2, unitCents: 150 }, { units: 1, unitCents: 25 }])).toBe(325);
});
`,
    },
    turns: [
      {
        goal: "Implement totalCents(lines) as a named export. Each invoice line has nonnegative integer units and unitCents. Sum units times unitCents for every line, in cents. An empty invoice totals zero.",
        accept: `import { expect, test } from "bun:test";
import { totalCents } from "./invoice";

test("recalculate after a quantity edit", () => {
  const lines = [{ units: 3, unitCents: 19 }, { units: 0, unitCents: 700 }];
  expect(totalCents([])).toBe(0);
  expect(totalCents(lines)).toBe(57);
  lines[1]!.units = 4;
  expect(totalCents(lines)).toBe(2857);
  expect(totalCents([{ units: 7, unitCents: 0 }])).toBe(0);
});
`,
      },
      {
        goal: "Add an optional nonnegative integer creditCents per invoice line. Subtract it once from that line's extended price, with a minimum of zero for that line. Preserve existing totals when the credit is absent.",
        accept: `import { expect, test } from "bun:test";
import { totalCents } from "./invoice";

test("credit belongs to one line", () => {
  const lines = [
    { units: 2, unitCents: 40, creditCents: 30 },
    { units: 1, unitCents: 10, creditCents: 500 },
    { units: 3, unitCents: 7 },
  ];
  expect(totalCents(lines)).toBe(71);
  expect(totalCents([...lines].reverse())).toBe(71);
  expect(totalCents([{ units: 2, unitCents: 41, creditCents: 0 }])).toBe(82);
  expect(totalCents([])).toBe(0);
});
`,
      },
    ],
  },
  {
    id: "delimited-export",
    path: "export-row.ts",
    files: {
      "export-row.ts": `export function csvRow(fields: string[]): string {
  return fields.join(",");
}
`,
      "export-row.test.ts": `import { expect, test } from "bun:test";
import { csvRow } from "./export-row";

test("quote a field containing the separator", () => {
  expect(csvRow(["A", "red,blue", ""])).toBe('A,"red,blue",');
});
`,
    },
    turns: [
      {
        goal: "Fix the named csvRow(fields) export. Join string fields with commas and add no row terminator. Quote a field only if it contains a comma, double quote, CR or LF. Within a quoted field, double every double quote. Preserve field contents and empty fields.",
        accept: `import { expect, test } from "bun:test";
import { csvRow } from "./export-row";

test("preserve cell text and quote each special character correctly", () => {
  expect(csvRow(["", "雪", ""])).toBe(",雪,");
  expect(csvRow(['a"b"c', "t\\r", "z\\ny"])).toBe('"a""b""c","t\\r","z\\ny"');
  expect(csvRow([" spaced ", "a;b"])).toBe(" spaced ,a;b");
  expect(csvRow([])).toBe("");
});
`,
      },
      {
        goal: "Support a second optional delimiter argument, either comma or semicolon, defaulting to comma. Separate cells with that delimiter and quote for the active delimiter only. Always keep the existing quote, CR and LF escaping rules.",
        accept: `import { expect, test } from "bun:test";
import { csvRow } from "./export-row";

test("switch separator without changing cell contents", () => {
  expect(csvRow(["x,y", "a;b", "尾"], ";")).toBe('x,y;"a;b";尾');
  expect(csvRow(['"note"', "", "m\\r\\nn"], ";")).toBe('"""note""";;"m\\r\\nn"');
  expect(csvRow(["u;v", "x,y"], ",")).toBe('u;v,"x,y"');
  expect(csvRow(["u;v", "x,y"])).toBe('u;v,"x,y"');
});
`,
      },
    ],
  },
];
