import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import { readTraces } from "../../cwm.ts";
import { repeated, targeted, junctionTest } from "./junctions.ts";
import { confirmation } from "./confirmation.ts";
import { cases, type Split } from "./cases.ts";

import { blind } from "./blind.ts";

const later = { blind, confirm: confirmation, repeated, targeted, junction: junctionTest };
export type Dataset = Split | keyof typeof later;
export function manifestFor(split: Dataset) {
  if (split === "fixed" || split === "varied" || split === "held") return cases(split);
  return later[split].map((program) => ({ program, family: program.entry, layout: split }));
}
export const fingerprints: Record<Dataset, string> = {
  blind: "a085a9cf560ad70b519f9599f9d9b4255c8a0c11408395bf4f7023af586a9fe8",
  fixed: "96c458b2c043df456f0db53129d51beaedfed0b5c6164f5d6a2039b87d9972fb",
  varied: "978ef5696d8adeb08edfbff83588831d39e435a54e9b4f6087da12d5cc085797",
  held: "eb3245bb7150ff452424501863d2ad51c4d2a38d4d6a5f65ea15c3d019d6e2a8",
  confirm: "55a5797fea66cdec766a991ca376a49f0553e9a231c02d0139f9b19a3f88a450",
  repeated: "1f409b7e8466526e390744741f7ca3b510141045e3978b64c7f7d07532b976de",
  targeted: "b11701d34315e4fa4075142e90725855cad6a325569b897deeda1ff383cf4469",
  junction: "33cc905d487ee0312542ac27bd6b06482f7393846ef77535d7e8cd4b14d76ee5",
};
export function isDataset(name: string): name is Dataset {
  return Object.hasOwn(fingerprints, name);
}
export async function loadSplit(file: string, split: Dataset) {
  const traces = await Array.fromAsync(readTraces(file)),
    manifest = manifestFor(split);
  assert.equal(traces.length, manifest.length);
  // Bind the entire normalized observation sequence before any label can enter a score.
  const hash = createHash("sha256");
  for (const t of traces) hash.update(JSON.stringify(t) + "\n");
  assert.equal(hash.digest("hex"), fingerprints[split], "Changed observations in " + split);
  return traces.map((trace, i) => {
    const { frames: _frames, outcome: _outcome, ...p } = trace;
    const { program, family, layout } = manifest[i]!;
    assert.deepEqual(p, program);
    return { trace, family, layout };
  });
}
