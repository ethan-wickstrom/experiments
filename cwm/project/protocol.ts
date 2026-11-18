import { Schema } from "effect";

const readSchema = Schema.Struct({ op: Schema.Literal("read"), path: Schema.String });
const writeSchema = Schema.Struct({
  op: Schema.Literal("write"),
  path: Schema.String,
  text: Schema.String,
});
const testSchema = Schema.Struct({ op: Schema.Literal("test") });
const doneSchema = Schema.Struct({ op: Schema.Literal("done") });
const actionSchema = Schema.Union([readSchema, writeSchema, testSchema, doneSchema]);
const strict = { onExcessProperty: "error" } as const;
export type Action = typeof actionSchema.Type;
export const decodeAction = Schema.decodeUnknownSync(Schema.fromJsonString(actionSchema), strict);
export type Event = { user: string } | { action: Action; observed: string };
export const POLICY =
  "Choose one TypeScript project action as compact JSON. Actions: read(path), write(path,text), test(), done(). Use the key op for the action name. Read before replacing a file. Run tests after changes.";
export const FORECAST =
  "Predict the result of the candidate project action. Reply with one word: pass, fail or rejected.";
// MiniCPM5 registers XML-like delimiters and the two bare thinking directives.
// Escape inside the serialized JSON so one ordinary JSON parse restores the source.
export function projectJson(value: unknown) {
  return JSON.stringify(value)
    .replaceAll("<", "\\u003c")
    .replace(/\/(?=(?:no_)?think)/g, "\\u002f");
}
export function wire(files: string[], history: Event[], candidate?: Action) {
  const state = candidate ? { files, history, candidate } : { files, history };
  return (candidate ? FORECAST : POLICY) + "\n" + projectJson(state);
}
export function actionGrammar(unread: string[], tested: boolean) {
  const schemas: Schema.Top[] = [writeSchema, doneSchema];
  if (!tested) schemas.push(testSchema);
  if (unread.length)
    schemas.push(Schema.Struct({ op: Schema.Literal("read"), path: Schema.Literals(unread) }));
  return Schema.toJsonSchemaDocument(Schema.Union(schemas), strict).schema;
}
