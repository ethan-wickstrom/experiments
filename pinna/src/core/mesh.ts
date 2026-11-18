import Delaunator from "delaunator";

/** A triangulated plate midsurface. Coordinates are metres. */
export interface Mesh {
  /** Node coordinates, interleaved x0 y0 x1 y1 ... */
  readonly nodes: Float64Array;
  /** Counter-clockwise triangles, three node indices each. */
  readonly tris: Int32Array;
  /** Boundary edges as node index pairs, oriented with the interior on the left. */
  readonly boundaryEdges: Int32Array;
  /** Target edge length the mesh was built with. */
  readonly size: number;
}

export type Polygon = ReadonlyArray<readonly [number, number]>;

export function polygonArea(poly: Polygon): number {
  let a = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    a += x0 * y1 - x1 * y0;
  }
  return a / 2;
}

export function pointInPolygon(poly: Polygon, x: number, y: number): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function distanceToPolygon(poly: Polygon, x: number, y: number): number {
  let best = Infinity;
  for (let i = 0; i < poly.length; i++) {
    const [ax, ay] = poly[i];
    const [bx, by] = poly[(i + 1) % poly.length];
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / len2));
    const px = ax + t * dx - x;
    const py = ay + t * dy - y;
    const d = px * px + py * py;
    if (d < best) best = d;
  }
  return Math.sqrt(best);
}

/**
 * Resample a closed outline so that consecutive points are about `size` apart.
 * Vertices where the outline turns by more than `cornerAngle` are kept exactly;
 * the runs between them are resampled by arc length.
 */
export function resampleOutline(
  poly: Polygon,
  size: number,
  cornerAngle = (25 * Math.PI) / 180,
): Array<[number, number]> {
  const n = poly.length;
  const pts: Array<[number, number]> = [];
  for (let i = 0; i < n; i++) {
    const p = poly[i];
    const q = poly[(i + 1) % n];
    if (Math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-12 * (1 + Math.abs(p[0]) + Math.abs(p[1])))
      pts.push([p[0], p[1]]);
  }
  const m = pts.length;
  if (m < 3) throw new Error("An outline needs at least three distinct points.");
  if (polygonArea(pts) < 0) pts.reverse();
  const corners: number[] = [];
  for (let i = 0; i < m; i++) {
    const a = pts[(i + m - 1) % m];
    const b = pts[i];
    const c = pts[(i + 1) % m];
    const turn = Math.abs(
      Math.atan2(
        (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]),
        (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]),
      ),
    );
    if (turn > cornerAngle) corners.push(i);
  }
  const out: Array<[number, number]> = [];
  const emitRun = (start: number, count: number, closedLoop: boolean) => {
    // Points start..start+count (indices mod m) form one run; emit all but the last point.
    const run: Array<[number, number]> = [];
    for (let k = 0; k <= count; k++) run.push(pts[(start + k) % m]);
    const cum = [0];
    for (let k = 1; k < run.length; k++)
      cum.push(cum[k - 1] + Math.hypot(run[k][0] - run[k - 1][0], run[k][1] - run[k - 1][1]));
    const total = cum[cum.length - 1];
    const segs = Math.max(closedLoop ? 3 : 1, Math.round(total / size));
    let k = 0;
    for (let s = 0; s < segs; s++) {
      const target = (s / segs) * total;
      while (k < cum.length - 2 && cum[k + 1] < target) k++;
      const span = cum[k + 1] - cum[k];
      const t = span === 0 ? 0 : (target - cum[k]) / span;
      out.push([
        run[k][0] + t * (run[k + 1][0] - run[k][0]),
        run[k][1] + t * (run[k + 1][1] - run[k][1]),
      ]);
    }
  };
  if (corners.length === 0) {
    emitRun(0, m, true);
  } else {
    for (let c = 0; c < corners.length; c++) {
      const start = corners[c];
      const end = corners[(c + 1) % corners.length];
      const count = c + 1 < corners.length ? end - start : end + m - start;
      emitRun(start, count, false);
    }
  }
  return out;
}

/**
 * Triangulate the region inside a closed outline with nearly equilateral triangles
 * of edge length `size`: boundary points at that spacing, a hexagonal lattice inside,
 * a Delaunay triangulation of both, and Laplacian smoothing of the interior.
 */
export function meshPolygon(outline: Polygon, size: number): Mesh {
  const boundary = resampleOutline(outline, size);
  const nb = boundary.length;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const [x, y] of boundary) {
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
  }
  const pts: number[] = [];
  for (const [x, y] of boundary) pts.push(x, y);
  const rowH = (size * Math.sqrt(3)) / 2;
  const rows = Math.max(1, Math.round((maxY - minY) / rowH));
  const dy = (maxY - minY) / rows;
  const cols = Math.max(1, Math.round((maxX - minX) / size));
  const dx = (maxX - minX) / cols;
  for (let r = 0; r <= rows; r++) {
    const y = minY + r * dy;
    const shift = r % 2 === 0 ? 0 : dx / 2;
    for (let c = 0; c <= cols; c++) {
      const x = minX + c * dx + shift;
      if (pointInPolygon(boundary, x, y) && distanceToPolygon(boundary, x, y) > 0.55 * size)
        pts.push(x, y);
    }
  }
  let coords = Float64Array.from(pts);
  let tris = triangulateInside(coords, boundary, size);
  for (let pass = 0; pass < 4; pass++) {
    const count = coords.length / 2;
    const sumX = new Float64Array(count);
    const sumY = new Float64Array(count);
    const deg = new Int32Array(count);
    for (let t = 0; t < tris.length; t += 3) {
      for (let e = 0; e < 3; e++) {
        const a = tris[t + e];
        const b = tris[t + ((e + 1) % 3)];
        sumX[a] += coords[2 * b];
        sumY[a] += coords[2 * b + 1];
        deg[a]++;
      }
    }
    const next = coords.slice();
    for (let i = nb; i < count; i++) {
      if (deg[i] === 0) continue;
      next[2 * i] = sumX[i] / deg[i];
      next[2 * i + 1] = sumY[i] / deg[i];
    }
    coords = next;
    tris = triangulateInside(coords, boundary, size);
  }
  return compact(coords, tris, size);
}

function triangulateInside(coords: Float64Array, boundary: Polygon, size: number): Int32Array {
  const d = new Delaunator(coords);
  const keep: number[] = [];
  const minArea = 1e-3 * size * size;
  for (let t = 0; t < d.triangles.length; t += 3) {
    const a = d.triangles[t];
    const b = d.triangles[t + 1];
    const c = d.triangles[t + 2];
    const ax = coords[2 * a];
    const ay = coords[2 * a + 1];
    const bx = coords[2 * b];
    const by = coords[2 * b + 1];
    const cx = coords[2 * c];
    const cy = coords[2 * c + 1];
    const area = ((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) / 2;
    if (Math.abs(area) < minArea) continue;
    // A sliver hugging the boundary has a tiny height over its longest edge.
    const longest = Math.max(
      Math.hypot(bx - ax, by - ay),
      Math.hypot(cx - bx, cy - by),
      Math.hypot(ax - cx, ay - cy),
    );
    if ((2 * Math.abs(area)) / longest < 0.08 * longest) continue;
    if (!pointInPolygon(boundary, (ax + bx + cx) / 3, (ay + by + cy) / 3)) continue;
    if (area > 0) keep.push(a, b, c);
    else keep.push(a, c, b);
  }
  return Int32Array.from(keep);
}

function compact(coords: Float64Array, tris: Int32Array, size: number): Mesh {
  const count = coords.length / 2;
  const remap = new Int32Array(count).fill(-1);
  let next = 0;
  for (let i = 0; i < tris.length; i++) if (remap[tris[i]] < 0) remap[tris[i]] = next++;
  const nodes = new Float64Array(2 * next);
  for (let i = 0; i < count; i++) {
    if (remap[i] < 0) continue;
    nodes[2 * remap[i]] = coords[2 * i];
    nodes[2 * remap[i] + 1] = coords[2 * i + 1];
  }
  const out = new Int32Array(tris.length);
  for (let i = 0; i < tris.length; i++) out[i] = remap[tris[i]];
  return { nodes, tris: out, boundaryEdges: findBoundaryEdges(out, next), size };
}

export function findBoundaryEdges(tris: Int32Array, nodeCount: number): Int32Array {
  const seen = new Map<number, number>();
  for (let t = 0; t < tris.length; t += 3) {
    for (let e = 0; e < 3; e++) {
      const a = tris[t + e];
      const b = tris[t + ((e + 1) % 3)];
      const key = a < b ? a * nodeCount + b : b * nodeCount + a;
      seen.set(key, (seen.get(key) ?? 0) + 1);
    }
  }
  const edges: number[] = [];
  for (let t = 0; t < tris.length; t += 3) {
    for (let e = 0; e < 3; e++) {
      const a = tris[t + e];
      const b = tris[t + ((e + 1) % 3)];
      const key = a < b ? a * nodeCount + b : b * nodeCount + a;
      if (seen.get(key) === 1) edges.push(a, b);
    }
  }
  return Int32Array.from(edges);
}

export function meshArea(mesh: Mesh): number {
  let a = 0;
  const { nodes, tris } = mesh;
  for (let t = 0; t < tris.length; t += 3) {
    const i = tris[t];
    const j = tris[t + 1];
    const k = tris[t + 2];
    a +=
      ((nodes[2 * j] - nodes[2 * i]) * (nodes[2 * k + 1] - nodes[2 * i + 1]) -
        (nodes[2 * j + 1] - nodes[2 * i + 1]) * (nodes[2 * k] - nodes[2 * i])) /
      2;
  }
  return a;
}
