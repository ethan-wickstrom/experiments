export const POLICY =
  "Choose one TypeScript project action as compact JSON. Actions: read(path), write(path,text), test(), done(). Use the key op for the action name. Read before replacing a file. Run tests after changes.";
export const FORECAST =
  "Predict the result of the candidate project action. Reply with one word: pass, fail or rejected.";
export type Action =
  | { op: "read"; path: string }
  | { op: "write"; path: string; text: string }
  | { op: "test" }
  | { op: "done" };
export type Event = { user: string } | { action: Action; observed: string };
export function wire(files: string[], history: Event[], candidate?: Action) {
  const state = candidate ? { files, history, candidate } : { files, history };
  return (candidate ? FORECAST : POLICY) + "\n" + JSON.stringify(state);
}
