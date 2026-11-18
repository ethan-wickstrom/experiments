import { splice, syntax } from "./checks.ts";

export type Edit = { start: number; end: number; replacement: string };
export type Validated = { edit: Edit | null; accepted: boolean; reason: string; text: string };
export function validate(raw: string, path: string, before: string): Validated {
  const reject = (reason: string, edit: Edit | null = null) => ({
    reason,
    edit,
    accepted: false,
    text: before,
  });
  let reply;
  try {
    reply = JSON.parse(raw);
  } catch {
    return reject("invalid JSON");
  }
  if (!reply || typeof reply !== "object") return reject("invalid response");
  if (reply.stopped === false && typeof reply.error === "string") return reject(reply.error);
  if (reply.stopped !== true || typeof reply.replacement !== "string")
    return reject("invalid stopped response");
  const { start, end, replacement } = reply;
  let text;
  try {
    text = splice(before, start, end, replacement);
  } catch {
    return reject("invalid bounds");
  }
  const edit = { start, end, replacement };
  if (reply.text !== text) return reject("reported text disagrees with splice", edit);
  const errors = syntax(path, text);
  if (errors.length) return reject("syntax: " + errors.join(", "), edit);
  return { edit, accepted: true, text, reason: text === before ? "identical" : "changed" };
}
