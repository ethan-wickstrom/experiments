type Project = {
  id: string;
  path: string;
  files: Record<string, string>;
  turns: { goal: string; accept: string }[];
};

// Hold out each whole project with both turns. Only the grader receives accept.
export const c2Held: Project[] = [
  {
    id: "thermometer-log",
    path: "thermometer.ts",
    files: {
      "thermometer.ts": `export async function record(path: string, celsius: number) {
  await Bun.write(path, JSON.stringify([celsius]));
}
`,
      "thermometer.test.ts": `import { test, expect } from "bun:test";
import { record } from "./thermometer";

test("retain successive temperatures", async () => {
  const path = "./daily-temperatures.json";
  await Bun.write(path, "[12]");
  await record(path, 18);
  expect(await Bun.file(path).json()).toEqual([12, 18]);
});
`,
    },
    turns: [
      {
        goal: "Fix record(path, celsius) for our thermometer. A missing file starts empty; otherwise read its JSON array of temperatures. Append the new number even if it repeats. Resolve after the updated array is saved to that path.",
        accept: `import { test, expect } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { record } from "./thermometer";

test("resume independent on-disk series in this workspace", async () => {
  const dir = await mkdtemp("./station-");
  try {
    const roof = join(dir, "roof.json"), shed = join(dir, "shed.json");
    await Bun.write(roof, "[-0.5,3]");
    await record(shed, 0);
    expect(await Bun.file(shed).json()).toEqual([0]);
    await record(roof, 3);
    expect(await Bun.file(roof).json()).toEqual([-0.5, 3, 3]);
    await Bun.write(roof, "[9]");
    await record(roof, -4);
    expect(await Bun.file(roof).json()).toEqual([9, -4]);
    expect(await Bun.file(shed).json()).toEqual([0]);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
`,
      },
      {
        goal: "Add an optional third argument keep, a nonnegative integer. After appending, retain only the most recent keep readings in chronological order. A limit of zero saves an empty array. Omitted keep still retains the entire log.",
        accept: `import { test, expect } from "bun:test";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { record } from "./thermometer";

test("retention trims the saved series on each call", async () => {
  const dir = await mkdtemp("./retention-");
  try {
    const path = join(dir, "zone.json");
    await Bun.write(path, "[8,6,4,2]");
    await record(path, -1, 3);
    expect(await Bun.file(path).json()).toEqual([4, 2, -1]);
    await record(path, 2);
    expect(await Bun.file(path).json()).toEqual([4, 2, -1, 2]);
    await record(path, 0, 0);
    expect(await Bun.file(path).json()).toEqual([]);
    await record(path, 7, 5);
    expect(await Bun.file(path).json()).toEqual([7]);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
`,
      },
    ],
  },
  {
    id: "station-departures",
    path: "station.ts",
    files: {
      "station.ts": `export function waitMinutes(now: number, departures: number[]): number | null {
  return null;
}
`,
      "station.test.ts": `import { test, expect } from "bun:test";
import { waitMinutes } from "./station";

test("minutes until the next service", () => {
  expect(waitMinutes(450, [420, 510, 480])).toBe(30);
});
`,
    },
    turns: [
      {
        goal: "Implement waitMinutes(now, departures) for a train display. All times are integer minutes since midnight from 0 to 1439. Return the wait to the earliest departure at or after now, or null if none remains today. Input times may be unsorted. Leave the caller's list untouched.",
        accept: `import { test, expect } from "bun:test";
import { waitMinutes } from "./station";

test("at-platform, unsorted and exhausted schedules", () => {
  const times = [1400, 35, 320, 35];
  expect(waitMinutes(0, times)).toBe(35);
  expect(waitMinutes(35, times)).toBe(0);
  expect(waitMinutes(321, times)).toBe(1079);
  expect(waitMinutes(1439, times)).toBeNull();
  expect(waitMinutes(10, [])).toBeNull();
  expect(times).toEqual([1400, 35, 320, 35]);
});
`,
      },
      {
        goal: "Add an optional third argument daily (default false). For a repeating daily schedule, if all today's trains have left, return the wait to the earliest train tomorrow. An empty schedule still returns null. Preserve normal same-day behavior and input order.",
        accept: `import { test, expect } from "bun:test";
import { waitMinutes } from "./station";

test("wrap a repeating timetable only after the final train", () => {
  const times = [620, 5, 330];
  expect(waitMinutes(1439, times, true)).toBe(6);
  expect(waitMinutes(1439, times)).toBeNull();
  expect(waitMinutes(1439, times, false)).toBeNull();
  expect(waitMinutes(6, times, true)).toBe(324);
  expect(waitMinutes(620, times, true)).toBe(0);
  expect(waitMinutes(1439, [0], true)).toBe(1);
  expect(waitMinutes(0, [], true)).toBeNull();
  expect(times).toEqual([620, 5, 330]);
});
`,
      },
    ],
  },
];
