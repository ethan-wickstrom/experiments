// A held lineage consists of an initial library and two successive user requests.
// The user supplies the visible test for each turn. Only the evaluator owns the graders.
type Project = {
  id: string;
  path: string;
  name: string;
  source: string;
  turns: { request: string; visible: string; hidden: string }[];
};

export const returnHeld: Project[] = [
  {
    id: "desk-reservations",
    path: "reservations.ts",
    name: "overlaps",
    source: `/** Desk reservations use minutes since opening. */
export function minutesBooked(start: number, end: number) {
  return end - start;
}

export function overlaps(start: number, end: number, otherStart: number, otherEnd: number): boolean {
  return false;
}

export function reservationLabel(desk: string, start: number, end: number) {
  return desk + " (" + minutesBooked(start, end) + " min)";
}
`,
    turns: [
      {
        request:
          "Implement overlaps for desk bookings. Both intervals have positive duration. Return true if they share any time. A booking ending exactly when the next starts is fine. Either booking may come first.",
        visible: `import { expect, test } from "bun:test";
import { overlaps, reservationLabel } from "./reservations";
test("accept adjacent bookings, flag a collision", () => {
  expect(overlaps(5, 15, 10, 20)).toBe(true);
  expect(overlaps(5, 15, 15, 25)).toBe(false);
  expect(reservationLabel("D4", 5, 15)).toBe("D4 (10 min)");
});
`,
        hidden: `import { expect, test } from "bun:test";
import { overlaps, minutesBooked } from "./reservations";
test("contained, equal, adjacent and distant windows in either order", () => {
  expect(overlaps(13, 18, 11, 22)).toBe(true);
  expect(overlaps(11, 22, 13, 18)).toBe(true);
  expect(overlaps(7, 9, 7, 9)).toBe(true);
  expect(overlaps(30, 31, 26, 30)).toBe(false);
  expect(overlaps(810, 812, 18, 34)).toBe(false);
  expect(minutesBooked(41, 62)).toBe(21);
});
`,
      },
      {
        request:
          "We now import canceled and invalid bookings too. Treat an interval whose end is at or before its own start as empty. An empty interval never overlaps anything. Preserve ordinary bookings.",
        visible: `import { expect, test } from "bun:test";
import { overlaps } from "./reservations";
test("a canceled booking inside a longer one", () => {
  expect(overlaps(8, 8, 4, 12)).toBe(false);
});
`,
        hidden: `import { expect, test } from "bun:test";
import { overlaps } from "./reservations";
test("both sides may be empty or run backwards", () => {
  expect(overlaps(2, 20, 11, 11)).toBe(false);
  expect(overlaps(18, 10, 1, 40)).toBe(false);
  expect(overlaps(1, 40, 18, 10)).toBe(false);
  expect(overlaps(12, 12, 12, 12)).toBe(false);
  expect(overlaps(101, 114, 108, 120)).toBe(true);
});
`,
      },
    ],
  },
  {
    id: "playlist-queue",
    path: "queue.ts",
    name: "nextTrack",
    source: `/** Playlist positions are zero-based. Track IDs keep their original case. */
export function trackCount(tracks: readonly string[]) {
  return tracks.length;
}

export function nextTrack(tracks: readonly string[], current: number, repeat = false): string | undefined {
  return undefined;
}

export function containsTrack(tracks: readonly string[], id: string) {
  return tracks.includes(id);
}
`,
    turns: [
      {
        request:
          "Implement nextTrack. Return the track ID immediately after current, or undefined at the end or on an empty queue. For a nonempty queue current is a valid index. Leave the queue in its original order. Repeat mode is reserved for later.",
        visible: `import { expect, test } from "bun:test";
import { nextTrack, trackCount } from "./queue";
test("advance through a short playlist", () => {
  const tracks = ["intro", "live"];
  expect(nextTrack(tracks, 0)).toBe("live");
  expect(nextTrack(tracks, 1)).toBeUndefined();
  expect(trackCount(tracks)).toBe(2);
});
`,
        hidden: `import { expect, test } from "bun:test";
import { containsTrack, nextTrack } from "./queue";
test("index the next position without changing the caller's list", () => {
  const list = Object.freeze(["fox", "海", "fox", "Encore"]);
  expect(nextTrack(list, 1)).toBe("fox");
  expect(nextTrack(list, 2)).toBe("Encore");
  expect(nextTrack(list, 3)).toBeUndefined();
  expect(nextTrack([], 0)).toBeUndefined();
  expect(containsTrack(list, "Encore")).toBe(true);
});
`,
      },
      {
        request:
          "Enable repeat mode. When repeat is true, advancing past the final track returns the first track. An empty playlist still returns undefined. Keep ordinary advances and repeat-off behavior.",
        visible: `import { expect, test } from "bun:test";
import { nextTrack } from "./queue";
test("repeat after the last track", () => {
  expect(nextTrack(["A", "B"], 1, true)).toBe("A");
});
`,
        hidden: `import { expect, test } from "bun:test";
import { nextTrack } from "./queue";
test("repeat singletons, interior positions and empty IDs", () => {
  const list = Object.freeze(["", "B", "C"]);
  expect(nextTrack(list, 2, true)).toBe("");
  expect(nextTrack(list, 0, true)).toBe("B");
  expect(nextTrack(list, 2, false)).toBeUndefined();
  expect(nextTrack(["solo"], 0, true)).toBe("solo");
  expect(nextTrack([], 0, true)).toBeUndefined();
});
`,
      },
    ],
  },
];
