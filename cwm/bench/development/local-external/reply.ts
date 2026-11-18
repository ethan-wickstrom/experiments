import { legalSpan, lines, splice, syntax } from "./checks.ts";

export type Edit = { start: number; end: number; replacement: string };
export type Validated = {
  span: [number, number] | null;
  edit: Edit | null;
  accepted: boolean;
  reason: string;
  text: string;
};
export function validate(raw: string, path: string, before: string): Validated {
  let span: Validated["span"] = null;
  const reject = (reason: string, edit: Edit | null = null) => ({
    reason,
    edit,
    span,
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
  if (legalSpan(reply.start, reply.end, lines(before).length)) span = [reply.start, reply.end];
  if (reply.stopped === false && typeof reply.error === "string") return reject(reply.error);
  if (reply.stopped !== true || typeof reply.replacement !== "string")
    return reject("invalid stopped response");
  const { start, end, replacement } = reply;
  if (!span) return reject("invalid bounds");
  const text = splice(before, start, end, replacement);
  const edit = { start, end, replacement };
  if (reply.text !== text) return reject("reported text disagrees with splice", edit);
  const errors = syntax(path, text);
  if (errors.length) return reject("syntax: " + errors.join(", "), edit);
  return { span, edit, accepted: true, text, reason: text === before ? "identical" : "changed" };
}
