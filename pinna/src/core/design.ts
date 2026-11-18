import { type Material, materialById } from "./materials.ts";
import { type Mesh, type Polygon, meshPolygon, polygonArea } from "./mesh.ts";
import type { Mode } from "./plate.ts";

export type Shape =
  | { readonly kind: "bar"; readonly length: number; readonly width: number }
  | { readonly kind: "disc"; readonly diameter: number }
  | { readonly kind: "polygon"; readonly sides: number; readonly diameter: number }
  | { readonly kind: "free"; readonly points: ReadonlyArray<readonly [number, number]> };

/** Which modes the tuning targets count through. */
export type Family = "bending" | "all";

export interface Design {
  readonly name: string;
  readonly shape: Shape;
  readonly materialId: string;
  /** Grain direction measured from the long (x) axis, degrees. */
  readonly grainAngle: number;
  /** Thickness of the uncut blank, metres. */
  readonly thickness: number;
  readonly profile: {
    /** The undercut varies along the long axis, or with distance from the centre. */
    readonly axis: "axial" | "radial";
    /** Depth of cut as a fraction of the blank thickness, at evenly spaced stations from the centre outward. */
    readonly depth: ReadonlyArray<number>;
  };
  readonly tuning: {
    /** Target frequency of the first partial, Hz. */
    readonly fundamental: number;
    /** Target frequency of each tuned partial as a multiple of the fundamental. */
    readonly ratios: ReadonlyArray<number>;
    readonly family: Family;
  };
}

/** The deepest cut the optimiser may make, as a fraction of the blank. */
export const MAX_DEPTH = 0.8;

export function outlineOf(shape: Shape): Polygon {
  switch (shape.kind) {
    case "bar": {
      const a = shape.length / 2;
      const b = shape.width / 2;
      return [
        [-a, -b],
        [a, -b],
        [a, b],
        [-a, b],
      ];
    }
    case "disc": {
      const out: Array<[number, number]> = [];
      for (let i = 0; i < 180; i++)
        out.push([
          (shape.diameter / 2) * Math.cos((Math.PI * i) / 90),
          (shape.diameter / 2) * Math.sin((Math.PI * i) / 90),
        ]);
      return out;
    }
    case "polygon": {
      const out: Array<[number, number]> = [];
      const offset = Math.PI / 2 + (shape.sides % 2 === 0 ? Math.PI / shape.sides : 0);
      for (let i = 0; i < shape.sides; i++)
        out.push([
          (shape.diameter / 2) * Math.cos(offset + (2 * Math.PI * i) / shape.sides),
          (shape.diameter / 2) * Math.sin(offset + (2 * Math.PI * i) / shape.sides),
        ]);
      return out;
    }
    case "free":
      return shape.points;
  }
}

export interface Extent {
  readonly minX: number;
  readonly maxX: number;
  readonly minY: number;
  readonly maxY: number;
  /** Half the extent along x and the largest distance from the origin. */
  readonly halfLength: number;
  readonly radius: number;
}

export function extentOf(outline: Polygon): Extent {
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  let radius = 0;
  for (const [x, y] of outline) {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
    radius = Math.max(radius, Math.hypot(x, y));
  }
  return { minX, maxX, minY, maxY, halfLength: Math.max(Math.abs(minX), Math.abs(maxX)), radius };
}

/** Move an outline so its centroid is at the origin. */
export function centred(points: Polygon): Array<[number, number]> {
  const area = polygonArea(points);
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < points.length; i++) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[(i + 1) % points.length];
    const cross = x0 * y1 - x1 * y0;
    cx += (x0 + x1) * cross;
    cy += (y0 + y1) * cross;
  }
  cx /= 6 * area;
  cy /= 6 * area;
  return points.map(([x, y]) => [x - cx, y - cy]);
}

export function buildMesh(design: Design, nodeBudget: number): Mesh {
  const outline = outlineOf(design.shape);
  const area = Math.abs(polygonArea(outline));
  const ext = extentOf(outline);
  const narrow = Math.min(ext.maxX - ext.minX, ext.maxY - ext.minY);
  const size = Math.min(Math.sqrt(area / (0.866 * nodeBudget)), narrow / 6);
  return meshPolygon(outline, size);
}

/**
 * Values of the clamped cubic B-spline basis that carries the undercut. The
 * profile is symmetric about the centre, so `stations` control values from the
 * centre outward stand for 2·stations − 1 control points across the piece;
 * the returned weights already fold the mirrored pairs together. They are
 * non-negative and sum to one, so the cut never exceeds its largest control value.
 */
export function profileWeights(u: number, stations: number): Float64Array {
  const n = 2 * stations - 1;
  const degree = Math.min(3, n - 1);
  const knots: number[] = [];
  for (let i = 0; i < n + degree + 1; i++) {
    if (i <= degree) knots.push(-1);
    else if (i >= n) knots.push(1);
    else knots.push(-1 + (2 * (i - degree)) / (n - degree));
  }
  const t = Math.max(-1, Math.min(1, u));
  const basis = new Float64Array(n + degree);
  for (let i = 0; i < n + degree; i++)
    basis[i] =
      (t >= knots[i] && t < knots[i + 1]) || (t === 1 && knots[i] < 1 && knots[i + 1] === 1)
        ? 1
        : 0;
  for (let d = 1; d <= degree; d++) {
    for (let i = 0; i < n + degree - d; i++) {
      const left = knots[i + d] - knots[i];
      const right = knots[i + d + 1] - knots[i + 1];
      basis[i] =
        (left > 0 ? ((t - knots[i]) / left) * basis[i] : 0) +
        (right > 0 ? ((knots[i + d + 1] - t) / right) * basis[i + 1] : 0);
    }
  }
  const out = new Float64Array(stations);
  for (let i = 0; i < n; i++) out[Math.abs(i - (stations - 1))] += basis[i];
  return out;
}

/** Normalised profile coordinate of a point: −1..1 along the axis, or 0..1 from the centre. */
export function profileCoordinate(
  axis: "axial" | "radial",
  ext: Extent,
  x: number,
  y: number,
): number {
  return axis === "axial" ? x / ext.halfLength : Math.hypot(x, y) / ext.radius;
}

export function depthAt(depth: ReadonlyArray<number>, u: number): number {
  const w = profileWeights(u, depth.length);
  let c = 0;
  for (let k = 0; k < depth.length; k++) c += w[k] * depth[k];
  return c;
}

export interface ThicknessField {
  /** Thickness of each element, metres. */
  readonly thickness: Float64Array;
  /** Profile basis weights of each element, `stations` per element. */
  readonly weights: Float64Array;
}

export function thicknessField(mesh: Mesh, design: Design): ThicknessField {
  const { nodes, tris } = mesh;
  const elements = tris.length / 3;
  const stations = design.profile.depth.length;
  const ext = extentOf(outlineOf(design.shape));
  const weights = new Float64Array(elements * stations);
  for (let e = 0; e < elements; e++) {
    const x =
      (nodes[2 * tris[3 * e]] + nodes[2 * tris[3 * e + 1]] + nodes[2 * tris[3 * e + 2]]) / 3;
    const y =
      (nodes[2 * tris[3 * e] + 1] +
        nodes[2 * tris[3 * e + 1] + 1] +
        nodes[2 * tris[3 * e + 2] + 1]) /
      3;
    weights.set(
      profileWeights(profileCoordinate(design.profile.axis, ext, x, y), stations),
      e * stations,
    );
  }
  return { thickness: applyDepth(weights, design.profile.depth, design.thickness), weights };
}

export function applyDepth(
  weights: Float64Array,
  depth: ReadonlyArray<number>,
  blank: number,
): Float64Array {
  const stations = depth.length;
  const elements = weights.length / stations;
  const out = new Float64Array(elements);
  for (let e = 0; e < elements; e++) {
    let c = 0;
    for (let k = 0; k < stations; k++) c += weights[e * stations + k] * depth[k];
    out[e] = blank * (1 - c);
  }
  return out;
}

/**
 * Whether a mode bends along the long axis, as opposed to twisting about it.
 * A bending mode moves the strip along the axis as much as the rest of the
 * piece; a torsional mode has a nodal line there.
 */
export function isAxialBending(mesh: Mesh, shape: Float32Array, ext: Extent): boolean {
  const { nodes } = mesh;
  const strip = 0.2 * Math.max(Math.abs(ext.minY), Math.abs(ext.maxY));
  let inStrip = 0;
  let countStrip = 0;
  let total = 0;
  for (let i = 0; i < shape.length; i++) {
    const e = shape[i] * shape[i];
    total += e;
    if (Math.abs(nodes[2 * i + 1]) <= strip) {
      inStrip += e;
      countStrip++;
    }
  }
  if (countStrip === 0 || total === 0) return false;
  return inStrip / countStrip > 0.5 * (total / shape.length);
}

/** Indices of the modes that the tuning targets count through, lowest first. */
export function familyModes(mesh: Mesh, modes: ReadonlyArray<Mode>, design: Design): number[] {
  if (design.tuning.family === "all") return modes.map((_, i) => i);
  const ext = extentOf(outlineOf(design.shape));
  const out: number[] = [];
  for (let i = 0; i < modes.length; i++) if (isAxialBending(mesh, modes[i].shape, ext)) out.push(i);
  return out;
}

export function materialOf(design: Design): Material {
  return materialById(design.materialId);
}

const bar = (
  name: string,
  materialId: string,
  length: number,
  width: number,
  thickness: number,
  fundamental: number,
  ratios: number[],
): Design => ({
  name,
  shape: { kind: "bar", length, width },
  materialId,
  grainAngle: 0,
  thickness,
  profile: { axis: "axial", depth: [0, 0, 0, 0, 0, 0, 0] },
  tuning: { fundamental, ratios, family: "bending" },
});

/** Starting points. The bars are uncut blanks; tuning them is the first thing to try. */
export const PRESETS: ReadonlyArray<Design> = [
  bar("Marimba bar, A3", "rosewood", 0.4, 0.058, 0.022, 220, [1, 4, 10]),
  bar("Vibraphone bar, F3", "aluminium", 0.36, 0.057, 0.0127, 174.614, [1, 4, 10]),
  bar("Xylophone bar, C5", "rosewood", 0.29, 0.038, 0.019, 523.251, [1, 3]),
  bar("Glockenspiel bar, C6", "steel", 0.19, 0.03, 0.008, 1046.5, [1]),
  {
    name: "Chladni plate",
    shape: { kind: "polygon", sides: 4, diameter: 0.34 },
    materialId: "brass",
    grainAngle: 0,
    thickness: 0.001,
    profile: { axis: "radial", depth: [0, 0, 0, 0, 0, 0, 0] },
    tuning: { fundamental: 0, ratios: [], family: "all" },
  },
  {
    name: "Bronze disc",
    shape: { kind: "disc", diameter: 0.3 },
    materialId: "bronze",
    grainAngle: 0,
    thickness: 0.004,
    profile: { axis: "radial", depth: [0, 0, 0, 0, 0, 0, 0] },
    tuning: { fundamental: 0, ratios: [], family: "all" },
  },
];
