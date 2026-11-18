// Each id owns a whole held lineage, including its revisions and candidate writes.
// Only files and the current goal belong in the policy workspace or its transcript.
type HeldProject = {
  id: string;
  files: Record<string, string>;
  turns: { goal: string; accept: string }[];
  alternatives: { path: string; text: string }[];
};

const boardSource = (loadBody: string) => `export type Lane = "todo" | "done";
export type Board = Record<Lane, string[]>;

export async function load(path: string): Promise<Board> {
  ${loadBody}
}

export async function save(path: string, board: Board) {
  await Bun.write(path, JSON.stringify(board));
}

export function move(board: Board, task: string, to: Lane) {
  board[to].push(task);
}
`;

const board: HeldProject = {
  id: "offline-task-board",
  files: {
    "board.ts": boardSource("return { todo: [], done: [] };"),
    "board.test.ts": `import { expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load, save } from "./board";

test("reopen a saved board", async () => {
  const dir = await mkdtemp(join(tmpdir(), "board-"));
  try {
    const path = join(dir, "tasks.json");
    const board = { todo: ["mail"], done: ["pack"] };
    await save(path, board);
    expect(await load(path)).toEqual(board);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
`,
  },
  turns: [
    {
      goal: "Make this task board work offline. save(path, board) must persist both lanes as JSON on disk. load(path) must restore that file, or return fresh empty lanes for a missing file. Keep the board API.",
      accept: `import { expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load, save } from "./board";

test("read existing bytes and checkpoint a detached board", async () => {
  const dir = await mkdtemp(join(tmpdir(), "checkpoint-"));
  try {
    const path = join(dir, "local.json");
    const blank = await load(path);
    expect(blank).toEqual({ todo: [], done: [] });
    blank.todo.push("unsaved");
    expect(await load(path)).toEqual({ todo: [], done: [] });
    const original = { todo: ["配達", "📦"], done: ["audit"] };
    await Bun.write(path, JSON.stringify(original));
    const reopened = await load(path);
    expect(reopened).toEqual(original);
    reopened.todo.reverse();
    expect(await load(path)).toEqual(original);
    await save(path, reopened);
    expect(await Bun.file(path).json()).toEqual({ todo: ["📦", "配達"], done: ["audit"] });
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
`,
    },
    {
      goal: "Fix move(board, task, to) duplicating a task. Boards start with unique task names. Move an existing task in place to the end of its new lane. Repeat moves and unknown tasks do nothing. Preserve order and offline save/load.",
      accept: `import { expect, test } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { load, save, move } from "./board";

test("persist each intermediate move", async () => {
  const dir = await mkdtemp(join(tmpdir(), "moves-"));
  try {
    const path = join(dir, "lanes.json");
    const board = { todo: ["b", "雪", "a"], done: ["c"] };
    move(board, "雪", "done");
    await save(path, board);
    expect(await Bun.file(path).json()).toEqual({ todo: ["b", "a"], done: ["c", "雪"] });
    const copy = await load(path);
    move(copy, "雪", "done");
    move(copy, "c", "done");
    move(copy, "absent", "todo");
    expect(copy).toEqual({ todo: ["b", "a"], done: ["c", "雪"] });
    move(copy, "c", "todo");
    expect(copy).toEqual({ todo: ["b", "a", "c"], done: ["雪"] });
    await save(path, copy);
    expect(await load(path)).toEqual(copy);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
`,
    },
  ],
  alternatives: [
    {
      path: "board.ts",
      text: boardSource(`const file = Bun.file(path);
  if (!(await file.exists())) return { todo: [], done: [] };
  const data = await file.json();
  return { todo: data.todo, done: [] };`),
    },
    {
      path: "board.ts",
      text: boardSource(`const file = Bun.file(path);
  if (!(await file.exists())) return { todo: [], done: [] };
  const data = await file.json();
  return { todo: data.todo, done: data.done };`),
    },
  ],
};

const eraseSource = (body: string) => `export function erase(text: string, index: number): string {
  ${body}
}
`;
const erasePoints = (cut: string) =>
  eraseSource(`const points = Array.from(text);
  if (index < 0 || index >= points.length) return text;
  points.splice(${cut}, 1);
  return points.join("");`);

const editor: HeldProject = {
  id: "unicode-line-editor",
  files: {
    "editor.ts": eraseSource(`if (index < 0 || index >= text.length) return text;
  return text.slice(0, index) + text.slice(index + 1);`),
    "editor.test.ts": `import { expect, test } from "bun:test";
import { erase } from "./editor";

test("erase at cursor", () => {
  expect(erase("A📌Z", 1)).toBe("AZ");
  expect(erase("home", 0)).toBe("ome");
});
`,
  },
  turns: [
    {
      goal: "Fix erase(text, index) in the line editor. The zero-based integer cursor counts Unicode code points. Remove just that code point. An out-of-range cursor leaves the original string unchanged.",
      accept: `import { expect, test } from "bun:test";
import { erase } from "./editor";

test("cursor after astral characters", () => {
  expect(erase("𝄞🚢水", 2)).toBe("𝄞🚢");
  expect(erase("𐐀B", 0)).toBe("B");
  expect(erase("猫🦦", 2)).toBe("猫🦦");
  expect(erase("𐐀B", -1)).toBe("𐐀B");
  expect(erase("", 0)).toBe("");
});
`,
    },
    {
      goal: "Update the cursor to count user-perceived characters (extended grapheme clusters). Erasing a flag, joined emoji, or letter plus combining mark takes one deletion. Keep the remaining text unchanged and preserve out-of-range behavior.",
      accept: `import { expect, test } from "bun:test";
import { erase } from "./editor";

test("erase one cluster and preserve the other clusters exactly", () => {
  const accent = "e\\u0301";
  const row = accent + "🇺🇾" + "👩🏽‍🔬" + "!";
  expect(erase(row, 0)).toBe("🇺🇾👩🏽‍🔬!");
  expect(erase(row, 1)).toBe(accent + "👩🏽‍🔬!");
  expect(erase(row, 2)).toBe(accent + "🇺🇾!");
  expect(erase(row, 3)).toBe(accent + "🇺🇾👩🏽‍🔬");
  expect(erase(row, 4)).toBe(row);
  expect(erase(row, -2)).toBe(row);
});
`,
    },
  ],
  alternatives: [
    { path: "editor.ts", text: erasePoints("index") },
    { path: "editor.ts", text: erasePoints("index + 1") },
  ],
};

const readerSource = (body: string) => `import { Effect } from "effect";

export function collect(ids: string[], read: (id: string) => Promise<string>) {
  return Effect.tryPromise({
    try: async () => {
      ${body}
    },
    catch: (error) => String(error),
  });
}
`;

const orderedReader = (ids: string) =>
  readerSource(`const rows: string[] = [];
      for (const id of ${ids}) rows.push(await read(id));
      return rows;`);

// The offline Bun test runner supplies the same pinned Effect package as CWM.
const reader: HeldProject = {
  id: "ordered-sample-reader",
  files: {
    "package.json": '{"private":true,"dependencies":{"effect":"4.1.4"}}\n',
    "reader.ts": readerSource("return Promise.all(ids.map((id) => read(id)));"),
    "reader.test.ts": `import { expect, test } from "bun:test";
import { Effect } from "effect";
import { collect } from "./reader";

test("finish one sample before starting the next", async () => {
  const events: string[] = [];
  const sample = collect(["red", "blue"], async (id) => {
    events.push("begin " + id);
    await Promise.resolve();
    events.push("end " + id);
    return id.toUpperCase();
  });
  expect(await Effect.runPromise(sample)).toEqual(["RED", "BLUE"]);
  expect(events).toEqual(["begin red", "end red", "begin blue", "end blue"]);
});
`,
  },
  turns: [
    {
      goal: "A device can read only one sample at a time. Keep collect(ids, read) a lazy Effect. On each run await the reads one by one in input order, return the strings in that order, and fail with String(error) at the first rejection.",
      accept: `import { expect, test } from "bun:test";
import { Effect } from "effect";
import { collect } from "./reader";

test("lazy serial reads, empty inputs and typed failures", async () => {
  const calls: string[] = [];
  let busy = false;
  const read = async (id: string) => {
    if (busy) throw Error("overlap");
    busy = true;
    calls.push(id);
    await Promise.resolve();
    busy = false;
    if (id === "bad") throw new Error("offline");
    return id + "✓";
  };
  const good = collect(["3", "1", "2"], read);
  expect(calls).toEqual([]);
  expect(await Effect.runPromise(good)).toEqual(["3✓", "1✓", "2✓"]);
  expect(await Effect.runPromise(collect([], read))).toEqual([]);
  const failed = collect(["あ", "bad", "after"], read);
  expect(await Effect.runPromise(Effect.flip(failed))).toBe("Error: offline");
  expect(calls).toEqual(["3", "1", "2", "あ", "bad"]);
});
`,
    },
    {
      goal: "Cache duplicate sample IDs during a single run of collect. Preserve one result per input position and the order of first reads. Start a fresh cache every time the same Effect is run. Keep lazy sequential reads and stop at the first rejection.",
      accept: `import { expect, test } from "bun:test";
import { Effect } from "effect";
import { collect } from "./reader";

test("reuse even empty readings only within this run", async () => {
  const seen: string[] = [];
  const effect = collect(["空", "b", "空", "b"], async (id) => {
    seen.push(id);
    await Promise.resolve();
    return id === "空" ? "" : String(seen.length);
  });
  expect(seen).toEqual([]);
  expect(await Effect.runPromise(effect)).toEqual(["", "2", "", "2"]);
  expect(await Effect.runPromise(effect)).toEqual(["", "4", "", "4"]);
  expect(seen).toEqual(["空", "b", "空", "b"]);
});

test("stop after a rejected read", async () => {
  const calls: string[] = [];
  const effect = collect(["a", "a", "!", "later"], async (id) => {
    calls.push(id);
    if (id === "!") throw "sensor";
    return id;
  });
  expect(await Effect.runPromise(Effect.flip(effect))).toBe("sensor");
  expect(calls).toEqual(["a", "!"]);
});
`,
    },
  ],
  alternatives: [
    { path: "reader.ts", text: orderedReader("[...ids].reverse()") },
    { path: "reader.ts", text: orderedReader("ids") },
  ],
};

export const held: HeldProject[] = [board, editor, reader];
