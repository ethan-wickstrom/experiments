import { expect, test } from "bun:test";
import type { Material } from "../src/core/materials.ts";
import { meshPolygon, meshArea } from "../src/core/mesh.ts";
import { PlateSystem, shiftFrequency } from "../src/core/plate.ts";

function iso(E: number, nu: number, rho: number): Material {
  const G = E / (2 * (1 + nu));
  return {
    id: "t",
    name: "t",
    kind: "metal",
    E1: E,
    E2: E,
    nu12: nu,
    G12: G,
    G13: G,
    G23: G,
    rho,
    eta: 0,
    color: "#000",
    metalness: 0,
    roughness: 0,
  };
}

function solve(
  outline: Array<[number, number]>,
  size: number,
  h: number,
  mat: Material,
  count: number,
) {
  const mesh = meshPolygon(outline, size);
  const sys = new PlateSystem(mesh, mat);
  const th = new Float64Array(mesh.tris.length / 3).fill(h);
  let longest = 0;
  for (const [x, y] of outline)
    for (const [u, v] of outline) longest = Math.max(longest, Math.hypot(x - u, y - v));
  sys.assemble(th, shiftFrequency(mat, h, longest));
  return { mesh, sys, th, result: sys.solve(count) };
}

test("mesh covers the outline", () => {
  const mesh = meshPolygon(
    [
      [0, 0],
      [2, 0],
      [2, 1],
      [0, 1],
    ],
    0.05,
  );
  expect(meshArea(mesh)).toBeCloseTo(2, 6);
});

test("free square plate matches Leissa's frequency parameters", () => {
  const a = 1;
  const h = 0.01;
  const mat = iso(70e9, 0.3, 2700);
  const D = (mat.E1 * h ** 3) / (12 * (1 - 0.3 ** 2));
  const { result, mesh } = solve(
    [
      [0, 0],
      [a, 0],
      [a, a],
      [0, a],
    ],
    a / 44,
    h,
    mat,
    6,
  );
  const params = result.modes.map(
    (m) => 2 * Math.PI * m.frequency * a * a * Math.sqrt((mat.rho * h) / D),
  );
  console.log(
    "square",
    mesh.nodes.length / 2,
    "nodes",
    result.iterations,
    "iters",
    params.map((p) => p.toFixed(3)).join(" "),
  );
  const leissa = [13.468, 19.596, 24.27, 34.801, 34.801, 61.093];
  for (let i = 0; i < leissa.length; i++)
    expect(Math.abs(params[i] / leissa[i] - 1)).toBeLessThan(0.01);
});

test("free circular plate matches the classical parameters", () => {
  const a = 0.5;
  const h = 0.005;
  const nu = 0.33;
  const mat = iso(70e9, nu, 2700);
  const D = (mat.E1 * h ** 3) / (12 * (1 - nu ** 2));
  const outline: Array<[number, number]> = [];
  for (let i = 0; i < 240; i++)
    outline.push([a * Math.cos((2 * Math.PI * i) / 240), a * Math.sin((2 * Math.PI * i) / 240)]);
  const { result } = solve(outline, a / 24, h, mat, 5);
  const params = result.modes.map(
    (m) => 2 * Math.PI * m.frequency * a * a * Math.sqrt((mat.rho * h) / D),
  );
  console.log("disc", params.map((p) => p.toFixed(3)).join(" "));
  const classical = [5.253, 5.253, 9.084, 12.23, 12.23];
  for (let i = 0; i < classical.length; i++)
    expect(Math.abs(params[i] / classical[i] - 1)).toBeLessThan(0.012);
});

test("slender free bar follows Euler-Bernoulli, thick bar falls below it", () => {
  const L = 0.4;
  const b = 0.04;
  const mat = iso(70e9, 0, 2700);
  const betaL2 = [22.3733, 61.6728, 120.9034];
  const bend = (h: number) => {
    const { result, mesh } = solve(
      [
        [0, 0],
        [L, 0],
        [L, b],
        [0, b],
      ],
      b / 8,
      h,
      mat,
      10,
    );
    // Bending modes are uniform across the width: pick modes whose deflection does not change sign across y.
    const out: number[] = [];
    for (const mode of result.modes) {
      let twist = 0;
      let norm = 0;
      for (let i = 0; i < mode.shape.length; i++) {
        twist += mode.shape[i] * mode.shape[i] * (mesh.nodes[2 * i + 1] > b / 2 ? 1 : -1);
        norm += mode.shape[i] * mode.shape[i];
      }
      let across = 0;
      for (let i = 0; i < mode.shape.length; i++)
        across += mode.shape[i] * (mesh.nodes[2 * i + 1] - b / 2) * Math.abs(mode.shape[i]);
      void twist;
      if (Math.abs(across) / (norm * b) < 0.05 && isBending(mode.shape, mesh.nodes, b))
        out.push(mode.frequency);
    }
    return out;
  };
  const euler = (h: number) =>
    betaL2.map((v) => (v / (2 * Math.PI * L * L)) * Math.sqrt((mat.E1 * h * h) / (12 * mat.rho)));
  const thin = bend(0.002);
  const e = euler(0.002);
  console.log(
    "thin bar",
    thin
      .slice(0, 3)
      .map((f) => f.toFixed(2))
      .join(" "),
    "euler",
    e.map((f) => f.toFixed(2)).join(" "),
  );
  for (let i = 0; i < 3; i++) expect(Math.abs(thin[i] / e[i] - 1)).toBeLessThan(0.01);
  const thick = bend(0.03);
  const et = euler(0.03);
  console.log(
    "thick bar ratio to Euler",
    thick
      .slice(0, 3)
      .map((f, i) => (f / et[i]).toFixed(4))
      .join(" "),
  );
  // Timoshenko: shear and rotary inertia lower the partials, the higher the more.
  expect(thick[0] / et[0]).toBeLessThan(0.995);
  expect(thick[2] / et[2]).toBeLessThan(thick[1] / et[1]);
  expect(thick[1] / et[1]).toBeLessThan(thick[0] / et[0]);
});

function isBending(shape: Float32Array, nodes: Float64Array, b: number): boolean {
  // Correlation of deflection with the across-width coordinate is near zero for bending modes.
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (let i = 0; i < shape.length; i++) {
    const y = nodes[2 * i + 1] - b / 2;
    sxy += Math.abs(shape[i]) * y * Math.sign(shape[i]);
    sxx += shape[i] * shape[i];
    syy += y * y;
  }
  // Torsion: w ∝ y·f(x); measure energy in the part odd in y.
  let odd = 0;
  const cells = new Map<number, { up: number; down: number }>();
  for (let i = 0; i < shape.length; i++) {
    const key = Math.round(nodes[2 * i] / (b / 4));
    const c = cells.get(key) ?? { up: 0, down: 0 };
    if (nodes[2 * i + 1] > b / 2) c.up += shape[i];
    else c.down += shape[i];
    cells.set(key, c);
  }
  let even = 0;
  for (const c of cells.values()) {
    odd += (c.up - c.down) ** 2;
    even += (c.up + c.down) ** 2;
  }
  void sxy;
  void sxx;
  void syy;
  return even > odd;
}

test("thickness sensitivities agree with finite differences", () => {
  const mat = iso(70e9, 0.33, 2700);
  const outline: Array<[number, number]> = [
    [0, 0],
    [0.3, 0],
    [0.3, 0.05],
    [0, 0.05],
  ];
  const mesh = meshPolygon(outline, 0.01);
  const sys = new PlateSystem(mesh, mat);
  const elements = mesh.tris.length / 3;
  const centroidX = (e: number) =>
    (mesh.nodes[2 * mesh.tris[3 * e]] +
      mesh.nodes[2 * mesh.tris[3 * e + 1]] +
      mesh.nodes[2 * mesh.tris[3 * e + 2]]) /
    3;
  const field = (amount: number) => {
    const th = new Float64Array(elements);
    for (let e = 0; e < elements; e++)
      th[e] = 0.01 - amount * Math.exp(-(((centroidX(e) - 0.15) / 0.05) ** 2));
    return th;
  };
  const run = (amount: number) => {
    sys.assemble(field(amount), 50);
    return sys.solve(4, undefined, 1e-12);
  };
  const base = run(0.003);
  const eps = 1e-6;
  const plus = run(0.003 + eps);
  const minus = run(0.003 - eps);
  for (let k = 0; k < 4; k++) {
    let analytic = 0;
    for (let e = 0; e < elements; e++)
      analytic +=
        base.modes[k].thicknessSensitivity[e] * -Math.exp(-(((centroidX(e) - 0.15) / 0.05) ** 2));
    const numeric = (plus.modes[k].lambda - minus.modes[k].lambda) / (2 * eps);
    console.log("sens", k, analytic.toExponential(5), numeric.toExponential(5));
    expect(Math.abs(analytic / numeric - 1)).toBeLessThan(2e-3);
  }
});
