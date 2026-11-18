import { expect, test } from "bun:test";
import { lines, splice } from "./checks.ts";
import { validate } from "./reply.ts";

test("line splice keeps original separators, including the unterminated last line", () => {
  expect(lines("")).toEqual([]);
  expect(lines("a\r\n\nβ")).toEqual(["a\r\n", "\n", "β"]);
  expect(splice("a\nb\n", 2, 2, "c")).toBe("a\nb\nc");
  expect(splice("a\nb", 0, 1, "")).toBe("b");
});
test("response validation requires exact text, bounded lines and a parsable TypeScript file", () => {
  const original = "const a = 1;\nconst b = a;\n";
  const edit = {
    stopped: true,
    start: 0,
    end: 1,
    replacement: "const a = 2;\n",
    text: "const a = 2;\nconst b = a;\n",
  };
  const check = (change: object) =>
    validate(JSON.stringify({ ...edit, ...change }), "lib.ts", original);
  expect(check({}).accepted).toBe(true);
  for (const change of [
    { start: false },
    { end: 3 },
    { start: 2 },
    { end: 0.5 },
    { text: original },
    { replacement: "{", text: "{const b = a;\n" },
  ]) {
    expect(check(change)).toMatchObject({ accepted: false, text: original });
  }
  expect(validate('{"stopped":false,"error":"capped"}', "lib.ts", original).edit).toBeNull();
  expect(check({ stopped: false, start: 0, end: 1, error: "capped" })).toMatchObject({
    accepted: false,
    span: [0, 1],
    edit: null,
  });
});
