import { expect, test } from "bun:test";
import {
  PRESETS,
  buildMesh,
  extentOf,
  isAxialBending,
  materialOf,
  outlineOf,
  profileWeights,
  thicknessField,
} from "../src/core/design.ts";
import { PlateSystem } from "../src/core/plate.ts";
import { solveDesign, tune } from "../src/core/tune.ts";

test("profile weights are a symmetric partition of unity", () => {
  for (const u of [-1, -0.63, -0.2, 0, 0.31, 0.8, 1]) {
    const w = profileWeights(u, 7);
    const mirror = profileWeights(-u, 7);
    let sum = 0;
    for (let k = 0; k < 7; k++) {
      sum += w[k];
      expect(w[k]).toBeGreaterThanOrEqual(0);
      expect(w[k]).toBeCloseTo(mirror[k], 12);
    }
    expect(sum).toBeCloseTo(1, 12);
  }
});

for (const preset of PRESETS.slice(0, 3)) {
  test(`tunes: ${preset.name}`, () => {
    const mesh = buildMesh(preset, 1200);
    const system = new PlateSystem(mesh, materialOf(preset), (preset.grainAngle * Math.PI) / 180);
    const field = thicknessField(mesh, preset);
    const before = solveDesign(system, preset, field, preset.profile.depth, 16).result;
    const ext = extentOf(outlineOf(preset.shape));
    const bending = before.modes
      .filter((m) => isAxialBending(mesh, m.shape, ext))
      .map((m) => m.frequency);
    console.log(
      preset.name,
      mesh.nodes.length / 2,
      "nodes; blank bending partials",
      bending
        .slice(0, 3)
        .map((f) => f.toFixed(1))
        .join(" "),
    );
    // An uncut bar has the free beam's inharmonic partials, a little flattened by shear.
    expect(bending[1] / bending[0]).toBeGreaterThan(2.5);
    expect(bending[1] / bending[0]).toBeLessThan(2.76);
    const start = performance.now();
    const result = tune(system, mesh, preset, field, 16);
    console.log(
      "  ",
      result.iterations,
      "iterations",
      (performance.now() - start).toFixed(0),
      "ms; cents",
      result.cents.map((c) => c.toFixed(2)).join(" "),
      "depth",
      result.depth.map((d) => d.toFixed(3)).join(" "),
      result.note ?? "",
    );
    expect(result.converged).toBe(true);
    for (const c of result.cents) expect(Math.abs(c)).toBeLessThan(1);
  }, 60_000);
}
