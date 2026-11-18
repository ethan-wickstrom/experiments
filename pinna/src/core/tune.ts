import {
  type Design,
  MAX_DEPTH,
  applyDepth,
  familyModes,
  materialOf,
  outlineOf,
  extentOf,
  type ThicknessField,
} from "./design.ts";
import type { Mesh } from "./mesh.ts";
import { type Mode, type PlateSystem, shiftFrequency } from "./plate.ts";

export interface TuneStep {
  readonly iteration: number;
  readonly depth: number[];
  /** Deviation of each targeted partial from its target, in cents. */
  readonly cents: number[];
  readonly frequencies: number[];
}

export interface TuneResult {
  readonly depth: number[];
  readonly cents: number[];
  readonly converged: boolean;
  readonly iterations: number;
  readonly modes: ReadonlyArray<Mode>;
  readonly thickness: Float64Array;
  /** Why tuning stopped short, when it did. */
  readonly note?: string;
}

const CENTS = 1200 / Math.LN2;

/**
 * Second-difference penalty that keeps the cut smooth enough to machine, in
 * cents per unit of depth curvature. It is relaxed as the partials approach
 * their targets, so it shapes the path without holding the result off pitch.
 */
const smoothnessFor = (worstCents: number) => 40 * Math.min(1, Math.max(0.002, worstCents / 100));

export function solveDesign(
  system: PlateSystem,
  design: Design,
  field: ThicknessField,
  depth: ReadonlyArray<number>,
  modeCount: number,
  warm?: Float64Array,
) {
  const thickness = applyDepth(field.weights, depth, design.thickness);
  let thinnest = Infinity;
  for (let e = 0; e < thickness.length; e++) thinnest = Math.min(thinnest, thickness[e]);
  const ext = extentOf(outlineOf(design.shape));
  system.assemble(thickness, shiftFrequency(materialOf(design), thinnest, 2 * ext.radius));
  return { thickness, result: system.solve(modeCount, warm, warm ? 1e-8 : 1e-9) };
}

/**
 * Find the undercut that puts the targeted partials on their target frequencies.
 *
 * This is Levenberg-Marquardt on the deviations in cents. The Jacobian comes
 * from the exact derivative of each eigenvalue with respect to each element's
 * thickness, dλ/dh = φᵀ(∂K/∂h − λ ∂M/∂h)φ, chained through the profile's
 * spline. Each trial costs one eigen-solve, warm-started from the last.
 */
export function tune(
  system: PlateSystem,
  mesh: Mesh,
  design: Design,
  field: ThicknessField,
  modeCount: number,
  onStep?: (step: TuneStep) => void,
  maxIterations = 40,
  toleranceCents = 0.2,
): TuneResult {
  const targets = design.tuning.ratios.map((r) => r * design.tuning.fundamental);
  const stations = design.profile.depth.length;
  const elements = field.weights.length / stations;
  let depth = design.profile.depth.map((d) => Math.min(MAX_DEPTH, Math.max(0, d)));
  let warm: Float64Array | undefined;

  const evaluate = (candidate: number[]) => {
    const { thickness, result } = solveDesign(system, design, field, candidate, modeCount, warm);
    const family = familyModes(mesh, result.modes, design);
    if (family.length < targets.length) return null;
    const residual = targets.map((t, i) => CENTS * Math.log(result.modes[family[i]].frequency / t));
    return { thickness, result, family, residual };
  };
  let SMOOTHNESS = 0;
  const cost = (residual: number[], d: number[]) => {
    let c = 0;
    for (const r of residual) c += r * r;
    for (let k = 0; k < stations; k++) {
      const curve = SMOOTHNESS * (d[Math.min(k + 1, stations - 1)] - 2 * d[k] + d[Math.abs(k - 1)]);
      c += curve * curve;
    }
    return c;
  };

  let current = evaluate(depth);
  if (!current) throw new Error("Not enough modes of the chosen family were found to tune.");
  warm = current.result.subspace;
  let damping = 1e-2;
  let iteration = 0;
  onStep?.({
    iteration,
    depth,
    cents: current.residual,
    frequencies: current.family
      .slice(0, targets.length)
      .map((i) => current!.result.modes[i].frequency),
  });
  let note: string | undefined;
  while (
    iteration < maxIterations &&
    Math.max(...current.residual.map(Math.abs)) > toleranceCents
  ) {
    iteration++;
    SMOOTHNESS = smoothnessFor(Math.max(...current.residual.map(Math.abs)));
    // Rows: one per target, then one smoothness row per station.
    const rows = targets.length + stations;
    const jac = new Float64Array(rows * stations);
    const res = new Float64Array(rows);
    for (let i = 0; i < targets.length; i++) {
      const mode = current.result.modes[current.family[i]];
      res[i] = current.residual[i];
      const scale = (CENTS / (2 * mode.lambda)) * -design.thickness;
      for (let e = 0; e < elements; e++) {
        const s = mode.thicknessSensitivity[e] * scale;
        for (let k = 0; k < stations; k++)
          jac[i * stations + k] += s * field.weights[e * stations + k];
      }
    }
    for (let k = 0; k < stations; k++) {
      const row = targets.length + k;
      const up = Math.min(k + 1, stations - 1);
      const down = Math.abs(k - 1);
      jac[row * stations + up] += SMOOTHNESS;
      jac[row * stations + k] -= 2 * SMOOTHNESS;
      jac[row * stations + down] += SMOOTHNESS;
      res[row] = SMOOTHNESS * (depth[up] - 2 * depth[k] + depth[down]);
    }
    const jtj = new Float64Array(stations * stations);
    const jtr = new Float64Array(stations);
    for (let r = 0; r < rows; r++) {
      for (let a = 0; a < stations; a++) {
        jtr[a] += jac[r * stations + a] * res[r];
        for (let b = 0; b < stations; b++)
          jtj[a * stations + b] += jac[r * stations + a] * jac[r * stations + b];
      }
    }
    let accepted = false;
    const before = cost(current.residual, depth);
    for (let attempt = 0; attempt < 8 && !accepted; attempt++) {
      const a = Float64Array.from(jtj);
      const rhs = Float64Array.from(jtr);
      for (let k = 0; k < stations; k++)
        a[k * stations + k] += damping * (jtj[k * stations + k] + 1e-9);
      // Active set: a station resting on a bound that the gradient pushes
      // further outward is held there, and the step is solved in the rest.
      for (let k = 0; k < stations; k++) {
        const held = (depth[k] <= 0 && jtr[k] > 0) || (depth[k] >= MAX_DEPTH && jtr[k] < 0);
        if (!held) continue;
        for (let j = 0; j < stations; j++) {
          a[k * stations + j] = 0;
          a[j * stations + k] = 0;
        }
        a[k * stations + k] = 1;
        rhs[k] = 0;
      }
      const step = solveDense(a, rhs, stations);
      const candidate = depth.map((d, k) => Math.min(MAX_DEPTH, Math.max(0, d - step[k])));
      const trial = evaluate(candidate);
      if (trial && cost(trial.residual, candidate) < before) {
        depth = candidate;
        current = trial;
        warm = trial.result.subspace;
        damping = Math.max(damping / 4, 1e-7);
        accepted = true;
      } else {
        damping *= 6;
      }
    }
    onStep?.({
      iteration,
      depth,
      cents: current.residual,
      frequencies: current.family
        .slice(0, targets.length)
        .map((i) => current!.result.modes[i].frequency),
    });
    if (!accepted) {
      note =
        "No further cut along this profile brings the partials closer. Change the blank's length or thickness, or the targets.";
      break;
    }
  }
  const worst = Math.max(...current.residual.map(Math.abs));
  if (!note && worst > toleranceCents) note = "Stopped at the iteration limit.";
  return {
    depth,
    cents: current.residual,
    converged: worst <= Math.max(toleranceCents, 1),
    iterations: iteration,
    modes: current.result.modes,
    thickness: current.thickness,
    note: worst <= toleranceCents ? undefined : note,
  };
}

/** Gaussian elimination with partial pivoting on a small dense system. */
function solveDense(a: Float64Array, b: Float64Array, n: number): Float64Array {
  const x = Float64Array.from(b);
  for (let c = 0; c < n; c++) {
    let pivot = c;
    for (let r = c + 1; r < n; r++)
      if (Math.abs(a[r * n + c]) > Math.abs(a[pivot * n + c])) pivot = r;
    if (pivot !== c) {
      for (let k = 0; k < n; k++)
        [a[c * n + k], a[pivot * n + k]] = [a[pivot * n + k], a[c * n + k]];
      [x[c], x[pivot]] = [x[pivot], x[c]];
    }
    const d = a[c * n + c];
    if (d === 0) continue;
    for (let r = c + 1; r < n; r++) {
      const f = a[r * n + c] / d;
      if (f === 0) continue;
      for (let k = c; k < n; k++) a[r * n + k] -= f * a[c * n + k];
      x[r] -= f * x[c];
    }
  }
  for (let c = n - 1; c >= 0; c--) {
    let s = x[c];
    for (let k = c + 1; k < n; k++) s -= a[c * n + k] * x[k];
    x[c] = a[c * n + c] === 0 ? 0 : s / a[c * n + c];
  }
  return x;
}
