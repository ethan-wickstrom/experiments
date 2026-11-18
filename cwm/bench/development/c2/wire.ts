/** One stock user message; use release chat template with thinking disabled. */
export const EDIT =
  "Write the complete TypeScript file for the goal. Reply only with raw file contents.";
export const DECIDE =
  "Choose the next action for the selected file. Reply with one word: read, edit, test or done.";
export type Source = { path: string; text: string };
export type Status = "unread" | "read" | "written" | "pass" | "fail";

function state(goal: string, path: string, files: readonly Source[]) {
  const ordered = [...files].sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  return { goal, path, files: ordered.map((f) => ({ path: f.path, text: f.text })) };
}

export function edit(goal: string, path: string, files: readonly Source[]) {
  return EDIT + "\n" + JSON.stringify(state(goal, path, files));
}

export function decide(goal: string, path: string, files: readonly Source[], status: Status) {
  return DECIDE + "\n" + JSON.stringify({ ...state(goal, path, files), status });
}
