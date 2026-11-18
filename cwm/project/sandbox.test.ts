import { expect, test } from "bun:test";
import { Effect } from "effect";
import { runTests } from "./sandbox.ts";

// Opt in on machines with the project image already built. Never pull an image during tests.
test.skipIf(!process.env.CWM_TEST_DOCKER)(
  "the container terminates an unfinished Bun test and retains the partial oracle output",
  async () => {
    const files = new Map([
      [
        "delay.test.ts",
        `import { test } from "bun:test";
test("slow external clock", async () => {
  console.log("waiting for the clock");
  await Bun.sleep(60000);
  console.log("clock finished");
}, 70000);
`,
      ],
    ]);
    const run = await Effect.runPromise(runTests(files));
    expect(run.exit).toBe(124);
    expect(run.stdout).toContain("waiting for the clock");
    expect(run.stdout).not.toContain("clock finished");
    expect(run.stderr).toContain("Bun test exceeded the 15-second execution limit");
  },
  30000,
);
