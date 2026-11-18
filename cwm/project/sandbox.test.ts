import { expect, test } from "bun:test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { setTimeout } from "node:timers/promises";
import { Effect } from "effect";
import { runTests, testObservation } from "./sandbox.ts";

const exec = promisify(execFile);

test("failure history keeps assertion values while the raw run retains full diagnostics", () => {
  const run = {
    exit: 1,
    stdout: "",
    stderr: "Expected: 10\nReceived: 100\n(fail) preserves bytes [0.8ms]\n/path/varies.ts",
  };
  expect(testObservation(run)).toBe("fail\nExpected: 10\nReceived: 100");
  expect(run.stderr).toContain("/path/varies.ts");
});

test.skipIf(!process.env.CWM_TEST_DOCKER)(
  "cancelling a run releases its Docker container",
  async () => {
    const list = async () =>
      (
        await exec("docker", ["ps", "-aq", "--filter", "label=cwm.parent=" + process.pid])
      ).stdout.trim();
    expect(await list()).toBe("");
    const controller = new AbortController();
    const run = Effect.runPromiseExit(
      runTests(
        new Map([
          [
            "slow.test.ts",
            'import {test} from "bun:test"; test("slow",()=>Bun.sleep(12000),14000);',
          ],
        ]),
      ),
      { signal: controller.signal },
    );
    try {
      const deadline = Date.now() + 5000;
      while (!(await list()) && Date.now() < deadline) await setTimeout(50);
      expect(await list()).not.toBe("");
    } finally {
      controller.abort();
      expect((await run)._tag).toBe("Failure");
    }
    expect(await list()).toBe("");
  },
  10000,
);
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
