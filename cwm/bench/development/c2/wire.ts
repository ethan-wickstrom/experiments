/** One stock user message; use release chat template with thinking disabled. */
export const EDIT =
  "Write the complete TypeScript file for the goal. Reply only with raw file contents.";
export const DECIDE =
  "Choose the next action for the selected file. Reply with one word: read, edit, test or done.";
export type Source = { path: string; text: string };
export type Status = "unread" | "read" | "written" | "pass" | "fail";

/** Both transformations operate inside JSON strings and preserve JSON.parse. */
export function jsonState(value: object) {
  return JSON.stringify(value)
    .replaceAll("<", "\\u003c")
    .replace(/\/(?=(?:no_)?think)/g, "\\u002f");
}

function state(goal: string, path: string, files: readonly Source[]) {
  const ordered = [...files].sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  return { goal, path, files: ordered.map((f) => ({ path: f.path, text: f.text })) };
}

export function edit(goal: string, path: string, files: readonly Source[]) {
  return EDIT + "\n" + jsonState(state(goal, path, files));
}

export function decide(goal: string, path: string, files: readonly Source[], status: Status) {
  return DECIDE + "\n" + jsonState({ ...state(goal, path, files), status });
}
