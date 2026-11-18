import { expect, test } from "bun:test";
import { ProjectSession } from "./agent.ts";
import { spliceFile, spliceSites, spliceSource } from "./splice.ts";

test("only the chosen UTF-16 AST span is replaced, including nested same-start operands", () => {
  const source = "// 🙂\nexport const x = (a:number,b:number,c:number) => a*b+c;";
  const sites = spliceSites("m.ts", source);
  const plus = sites.find((s) => source.slice(s.start, s.end) === "+")!;
  expect(spliceSource("m.ts", source, plus, "-")).toBe(source.replace("+", "-"));
  const operand = sites.find((s) => source.slice(s.start, s.end) === "c")!;
  expect(spliceSource("m.ts", source, operand, "c; export const leaked = 1")).toBeUndefined();
});

test("repair uses the tested parent, shares all other context with the control, and writes only the visible winner", async () => {
  for (const feedback of [true, false]) {
    const initial = "export const calc = (n:number) => n+2;";
    const files = new Map([
      ["calc.ts", initial],
      ["config.ts", "export const fee = 2;"],
    ]);
    let call = 0;
    const session = new ProjectSession(
      { files },
      async (request) => {
        const index = call++;
        const state = JSON.parse(request.split("\n")[1]!) as {
          sites: { id: string }[];
          files: Record<string, string>;
          diagnostic?: { stderr: string };
        };
        expect(files.get("calc.ts")).toBe(initial);
        expect(state.files["config.ts"]).toBe(files.get("config.ts")!);
        if (index < 4 || !feedback) expect(state.diagnostic).toBeUndefined();
        else expect(state.diagnostic?.stderr).toContain("Expected: 6");
        if (index >= 4) expect(state.files["calc.ts"]).toBe(initial.replace("+", "-"));
        const text =
          index % 2
            ? "{}"
            : JSON.stringify({
                site: state.sites[0]!.id,
                operation: index < 4 ? "subtract" : "multiply",
              });
        return { text, finish: "stop", tokens: 1, inputTokens: 1 };
      },
      async (snapshot) => {
        const pass = snapshot.get("calc.ts")?.includes("n*2");
        return {
          exit: pass ? 0 : 1,
          stdout: "",
          stderr: pass ? "1 pass" : "Expected: 6\nReceived: 1\n1 fail",
        };
      },
    );
    const result = await spliceFile(session, "calc.ts", "compute fee", { feedback });
    expect(result.stop).toBe("tested");
    expect(result.trials).toHaveLength(8);
    expect(result.selected).toBe(4);
    expect(result.trials[4]!.parent).toBe(0);
    expect(result.trials[6]!.status).toBe("invalid");
    expect(files.get("calc.ts")).toBe(initial.replace("+", "*"));
    expect(session.history.filter((e) => "action" in e && e.action.op === "write")).toHaveLength(1);
  }
});

test("unavailable sites and context limits retain the original workspace and never query the model", async () => {
  for (const [text, stop] of [
    ["export function noop() {}", "no-sites"],
    ["export const x = 1;\n//" + "x".repeat(25000), "context-limit"],
  ] as const) {
    const session = new ProjectSession(
      { files: new Map([["x.ts", text]]) },
      async () => {
        throw Error("Unexpected model call");
      },
      async () => ({ exit: 1, stdout: "", stderr: "1 fail" }),
    );
    const result = await spliceFile(session, "x.ts", "repair");
    expect(result.stop).toBe(stop);
    expect(result.trials).toHaveLength(0);
    expect(session.project.files.get("x.ts")).toBe(text);
  }
});
