import { expect, test } from "bun:test";
import { ProjectSession } from "./agent.ts";
import { planFile } from "./plan.ts";

test("score two complete alternatives before writing only the selected source", async () => {
  for (const choice of [null, 1] as const) {
    const initial = "export const n = 0;\n";
    const files = new Map([["n.ts", initial]]);
    const texts = ["export const n = 1;\n", "export const n = 2;\n"];
    let calls = 0,
      tests = 0;
    const session = new ProjectSession(
      { files },
      async () => {
        return { text: texts[calls++]!, finish: "stop", tokens: 9, inputTokens: 60 };
      },
      async () => {
        tests++;
        expect(files.get("n.ts")).toBe(texts[1]);
        return { exit: 1, stdout: "", stderr: "1 fail" };
      },
    );
    const result = await planFile(session, "n.ts", "Double one", {
      choose: async (pair) => {
        expect(files.get("n.ts")).toBe(initial);
        expect(pair.candidates.map((c) => c.text)).toEqual(texts);
        expect(tests).toBe(0);
        return { scores: choice === null ? [0, 0] : [-2, 2], choice };
      },
    });
    expect(result.stop).toBe(choice === null ? "tie" : "failed");
    expect(tests).toBe(choice === null ? 0 : 1);
    expect(files.get("n.ts")).toBe(choice === null ? initial : texts[1]);
    expect(result.events).toHaveLength(2);
  }
});
