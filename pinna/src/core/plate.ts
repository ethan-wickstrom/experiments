import { Csr, Skyline, denseGeneralizedEigen, reverseCuthillMcKee } from "./linalg.ts";
import type { Material } from "./materials.ts";
import type { Mesh } from "./mesh.ts";

/**
 * Free vibration of a moderately thick plate of varying thickness.
 *
 * The plate follows Reissner-Mindlin theory: each point of the midsurface has a
 * deflection w and two rotations β of its normal, so transverse shear and rotary
 * inertia are included. These matter for instrument bars, whose upper partials
 * have wavelengths only a few thicknesses long. The element is the three-node
 * MITC triangle: w and β are linear, and the shear strain γ = ∇w − β is
 * re-interpolated from its tangential component on each edge (the lowest-order
 * Nédélec space), which removes shear locking as the plate becomes thin.
 */

/** Shear correction factor for a homogeneous section. */
const SHEAR_CORRECTION = 5 / 6;

/** Constants of the stabilised shear term: the shear stiffness is scaled by h²/(h² + α·hK²). */
export const SHEAR_STABILISATION = 0.1;

export interface Mode {
  /** Frequency in Hz. */
  readonly frequency: number;
  /** Eigenvalue ω², rad²/s². */
  readonly lambda: number;
  /** Deflection at each mesh node, for a mode of unit modal mass (units kg^-1/2). */
  readonly shape: Float32Array;
  /** dλ/dh for each element's thickness, 1/(s²·m). */
  readonly thicknessSensitivity: Float32Array;
}

export interface SolveResult {
  readonly modes: ReadonlyArray<Mode>;
  readonly iterations: number;
  /** The converged subspace, to warm-start a solve of a nearby plate. */
  readonly subspace: Float64Array;
}

interface ElementScratch {
  readonly kb: Float64Array;
  readonly ks: Float64Array;
  /** Scale of the shear stabilisation, s = h²/(h² + α hK²). */
  shearScale: number;
  area: number;
}

export class PlateSystem {
  readonly mesh: Mesh;
  readonly material: Material;
  readonly grainAngle: number;
  readonly nodeCount: number;
  readonly dofCount: number;
  private readonly perm: Int32Array;
  private readonly first: Int32Array;
  private readonly csrStart: Int32Array;
  private readonly csrCol: Int32Array;
  private readonly bending: Float64Array;
  private readonly shear: Float64Array;
  private mass: Csr | null = null;
  private factor: Skyline | null = null;
  private thickness: Float64Array | null = null;
  private sigma = 0;

  constructor(mesh: Mesh, material: Material, grainAngle = 0) {
    this.mesh = mesh;
    this.material = material;
    this.grainAngle = grainAngle;
    const n = mesh.nodes.length / 2;
    this.nodeCount = n;
    this.dofCount = 3 * n;

    // Node adjacency.
    const sets: Array<Set<number>> = Array.from({ length: n }, () => new Set<number>());
    const { tris } = mesh;
    for (let t = 0; t < tris.length; t += 3) {
      for (let a = 0; a < 3; a++)
        for (let b = 0; b < 3; b++) if (a !== b) sets[tris[t + a]].add(tris[t + b]);
    }
    const adjStart = new Int32Array(n + 1);
    for (let i = 0; i < n; i++) adjStart[i + 1] = adjStart[i] + sets[i].size;
    const adj = new Int32Array(adjStart[n]);
    for (let i = 0; i < n; i++) {
      let p = adjStart[i];
      for (const j of sets[i]) adj[p++] = j;
    }
    this.perm = reverseCuthillMcKee(adjStart, adj);

    // Skyline profile and CSR pattern in the permuted numbering, 3×3 blocks per node pair.
    const first = new Int32Array(3 * n);
    const rowNodes: number[][] = Array.from({ length: n }, () => []);
    for (let i = 0; i < n; i++) {
      const pi = this.perm[i];
      let lowest = pi;
      const row = rowNodes[pi];
      row.push(pi);
      for (let p = adjStart[i]; p < adjStart[i + 1]; p++) {
        const pj = this.perm[adj[p]];
        row.push(pj);
        if (pj < lowest) lowest = pj;
      }
      row.sort((a, b) => a - b);
      for (let c = 0; c < 3; c++) first[3 * pi + c] = 3 * lowest;
    }
    this.first = first;
    const csrStart = new Int32Array(3 * n + 1);
    for (let pi = 0; pi < n; pi++)
      for (let c = 0; c < 3; c++)
        csrStart[3 * pi + c + 1] = csrStart[3 * pi + c] + 3 * rowNodes[pi].length;
    const csrCol = new Int32Array(csrStart[3 * n]);
    for (let pi = 0; pi < n; pi++) {
      for (let c = 0; c < 3; c++) {
        let p = csrStart[3 * pi + c];
        for (const pj of rowNodes[pi]) for (let d = 0; d < 3; d++) csrCol[p++] = 3 * pj + d;
      }
    }
    this.csrStart = csrStart;
    this.csrCol = csrCol;

    // Constitutive matrices per unit thickness, rotated from the material axes.
    const m = material;
    const c = Math.cos(grainAngle);
    const s = Math.sin(grainAngle);
    const nu21 = (m.nu12 * m.E2) / m.E1;
    const den = 1 - m.nu12 * nu21;
    const q = [
      m.E1 / den,
      (m.nu12 * m.E2) / den,
      0,
      (m.nu12 * m.E2) / den,
      m.E2 / den,
      0,
      0,
      0,
      m.G12,
    ];
    // Engineering strain transformation, global to material.
    const t = [c * c, s * s, c * s, s * s, c * c, -c * s, -2 * c * s, 2 * c * s, c * c - s * s];
    const qt = new Float64Array(9);
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++)
        for (let k = 0; k < 3; k++) qt[3 * i + j] += q[3 * i + k] * t[3 * k + j];
    this.bending = new Float64Array(9);
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++)
        for (let k = 0; k < 3; k++) this.bending[3 * i + j] += t[3 * k + i] * qt[3 * k + j];
    this.shear = Float64Array.of(
      m.G13 * c * c + m.G23 * s * s,
      (m.G13 - m.G23) * c * s,
      (m.G13 - m.G23) * c * s,
      m.G13 * s * s + m.G23 * c * c,
    );
  }

  /** Element stiffness for element `e` with thickness `h`, split into bending and shear parts. */
  private element(e: number, h: number, out: ElementScratch): void {
    const { nodes, tris } = this.mesh;
    const n0 = tris[3 * e];
    const n1 = tris[3 * e + 1];
    const n2 = tris[3 * e + 2];
    const x = [nodes[2 * n0], nodes[2 * n1], nodes[2 * n2]];
    const y = [nodes[2 * n0 + 1], nodes[2 * n1 + 1], nodes[2 * n2 + 1]];
    const area = ((x[1] - x[0]) * (y[2] - y[0]) - (y[1] - y[0]) * (x[2] - x[0])) / 2;
    out.area = area;
    // Gradients of the barycentric coordinates.
    const gx = [(y[1] - y[2]) / (2 * area), (y[2] - y[0]) / (2 * area), (y[0] - y[1]) / (2 * area)];
    const gy = [(x[2] - x[1]) / (2 * area), (x[0] - x[2]) / (2 * area), (x[1] - x[0]) / (2 * area)];

    // Bending: curvature κ = (βx,x  βy,y  βx,y + βy,x) is constant.
    const b = new Float64Array(27);
    for (let i = 0; i < 3; i++) {
      b[3 * i + 1] = gx[i];
      b[1 * 9 + 3 * i + 2] = gy[i];
      b[2 * 9 + 3 * i + 1] = gy[i];
      b[2 * 9 + 3 * i + 2] = gx[i];
    }
    const { kb, ks } = out;
    kb.fill(0);
    ks.fill(0);
    const dScale = (h * h * h * area) / 12;
    const db = new Float64Array(27);
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 9; j++)
        for (let k = 0; k < 3; k++) db[9 * i + j] += this.bending[3 * i + k] * b[9 * k + j];
    for (let i = 0; i < 9; i++)
      for (let j = 0; j < 9; j++)
        for (let k = 0; k < 3; k++) kb[9 * i + j] += dScale * b[9 * k + i] * db[9 * k + j];

    // Shear: tangential strain integrated along each edge (i → j).
    const cmat = new Float64Array(27);
    let longest = 0;
    for (let ed = 0; ed < 3; ed++) {
      const i = ed;
      const j = (ed + 1) % 3;
      const ex = x[j] - x[i];
      const ey = y[j] - y[i];
      longest = Math.max(longest, Math.hypot(ex, ey));
      cmat[9 * ed + 3 * i] = -1;
      cmat[9 * ed + 3 * j] = 1;
      cmat[9 * ed + 3 * i + 1] = -ex / 2;
      cmat[9 * ed + 3 * j + 1] = -ex / 2;
      cmat[9 * ed + 3 * i + 2] = -ey / 2;
      cmat[9 * ed + 3 * j + 2] = -ey / 2;
    }
    const shearScale = (h * h) / (h * h + SHEAR_STABILISATION * longest * longest);
    out.shearScale = shearScale;
    const sScale = (SHEAR_CORRECTION * h * shearScale * area) / 3;
    const g = new Float64Array(18);
    for (let mid = 0; mid < 3; mid++) {
      // Barycentric coordinates of the midpoint of edge (mid, mid+1).
      const lam = [0, 0, 0];
      lam[mid] = 0.5;
      lam[(mid + 1) % 3] = 0.5;
      g.fill(0);
      for (let ed = 0; ed < 3; ed++) {
        const i = ed;
        const j = (ed + 1) % 3;
        const nx = lam[i] * gx[j] - lam[j] * gx[i];
        const ny = lam[i] * gy[j] - lam[j] * gy[i];
        for (let k = 0; k < 9; k++) {
          g[k] += nx * cmat[9 * ed + k];
          g[9 + k] += ny * cmat[9 * ed + k];
        }
      }
      const s = this.shear;
      for (let i = 0; i < 9; i++) {
        const sx = s[0] * g[i] + s[2] * g[9 + i];
        const sy = s[1] * g[i] + s[3] * g[9 + i];
        for (let j = 0; j < 9; j++) ks[9 * i + j] += sScale * (sx * g[j] + sy * g[9 + j]);
      }
    }
  }

  /**
   * Assemble and factor K + σM for the given element thicknesses. `sigmaHz` is
   * the frequency of the shift that makes the free plate's stiffness invertible;
   * it should sit below the first elastic mode.
   */
  assemble(thickness: Float64Array, sigmaHz: number): void {
    const { tris } = this.mesh;
    const elements = tris.length / 3;
    if (thickness.length !== elements) throw new Error("one thickness per element is required");
    const sigma = (2 * Math.PI * sigmaHz) ** 2;
    const sky = new Skyline(this.first);
    const mass = new Csr(this.dofCount, this.csrStart, this.csrCol);
    const scratch: ElementScratch = {
      kb: new Float64Array(81),
      ks: new Float64Array(81),
      shearScale: 1,
      area: 0,
    };
    const rho = this.material.rho;
    const dofs = new Int32Array(9);
    for (let e = 0; e < elements; e++) {
      const h = thickness[e];
      this.element(e, h, scratch);
      for (let a = 0; a < 3; a++)
        for (let c = 0; c < 3; c++) dofs[3 * a + c] = 3 * this.perm[tris[3 * e + a]] + c;
      const mw = (rho * h * scratch.area) / 12;
      const mr = (rho * h * h * h * scratch.area) / 144;
      for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
          let m = 0;
          if (i % 3 === j % 3) m = (i % 3 === 0 ? mw : mr) * (i === j ? 2 : 1);
          if (m !== 0) mass.add(dofs[i], dofs[j], m);
          sky.add(dofs[i], dofs[j], scratch.kb[9 * i + j] + scratch.ks[9 * i + j] + sigma * m);
        }
      }
    }
    if (!sky.factor())
      throw new Error(
        "The plate's stiffness could not be factored; check the outline and thickness.",
      );
    this.factor = sky;
    this.mass = mass;
    this.thickness = thickness;
    this.sigma = sigma;
  }

  /**
   * The `count` lowest elastic modes by subspace iteration with Rayleigh-Ritz
   * projection. The three rigid-body motions of the free plate are discarded.
   */
  solve(
    count: number,
    warmStart?: Float64Array,
    tolerance = 1e-9,
    maxIterations = 80,
  ): SolveResult {
    const factor = this.factor;
    const mass = this.mass;
    const thickness = this.thickness;
    if (!factor || !mass || !thickness) throw new Error("assemble() first");
    const n = this.dofCount;
    const wanted = count + 3;
    const m = Math.min(n, Math.max(wanted + 8, Math.ceil(1.6 * wanted)));
    let x = new Float64Array(m * n);
    if (warmStart && warmStart.length === x.length) {
      x.set(warmStart);
    } else {
      let seed = 0x9e3779b9;
      for (let i = 0; i < x.length; i++) {
        seed = (Math.imul(seed ^ (seed >>> 15), 0x2c1b3c6d) + 0x297a2d39) | 0;
        x[i] = ((seed >>> 0) / 4294967296) * 2 - 1;
      }
    }
    let y = new Float64Array(m * n);
    for (let k = 0; k < m; k++) mass.multiply(x, k * n, y, k * n);
    let z = new Float64Array(m * n);
    let w = new Float64Array(m * n);
    const kr = new Float64Array(m * m);
    const mr = new Float64Array(m * m);
    let previous: Float64Array = new Float64Array(m);
    let theta: Float64Array = new Float64Array(m);
    let iterations = 0;
    for (; iterations < maxIterations; iterations++) {
      z.set(y);
      for (let k = 0; k < m; k++) factor.solve(z, k * n);
      for (let k = 0; k < m; k++) mass.multiply(z, k * n, w, k * n);
      for (let a = 0; a < m; a++) {
        for (let b = a; b < m; b++) {
          let sk = 0;
          let sm = 0;
          const ao = a * n;
          const bo = b * n;
          for (let i = 0; i < n; i++) {
            sk += z[ao + i] * y[bo + i] + z[bo + i] * y[ao + i];
            sm += z[ao + i] * w[bo + i];
          }
          kr[a * m + b] = kr[b * m + a] = sk / 2;
          mr[a * m + b] = mr[b * m + a] = sm;
        }
      }
      const eig = denseGeneralizedEigen(kr, mr, m);
      theta = eig.values;
      // Rotate: X = Z Q, Y = W Q.
      rotate(z, x, eig.vectors, n, m);
      rotate(w, y, eig.vectors, n, m);
      let worst = 0;
      for (let k = 0; k < wanted; k++)
        worst = Math.max(worst, Math.abs(theta[k] - previous[k]) / Math.abs(theta[k]));
      previous = theta;
      if (worst < tolerance) {
        iterations++;
        break;
      }
    }

    const { tris } = this.mesh;
    const elements = tris.length / 3;
    const scratch: ElementScratch = {
      kb: new Float64Array(81),
      ks: new Float64Array(81),
      shearScale: 1,
      area: 0,
    };
    const rho = this.material.rho;
    const modes: Mode[] = [];
    const local = new Float64Array(9);
    const sens: Float32Array[] = [];
    const lambdas: number[] = [];
    for (let k = 3; k < wanted; k++) {
      lambdas.push(Math.max(theta[k] - this.sigma, 0));
      sens.push(new Float32Array(elements));
    }
    for (let e = 0; e < elements; e++) {
      const h = thickness[e];
      this.element(e, h, scratch);
      const mw = (rho * h * scratch.area) / 12;
      const mrot = (rho * h * h * h * scratch.area) / 144;
      for (let k = 0; k < count; k++) {
        const off = (k + 3) * n;
        for (let a = 0; a < 3; a++)
          for (let c = 0; c < 3; c++)
            local[3 * a + c] = x[off + 3 * this.perm[tris[3 * e + a]] + c];
        let eb = 0;
        let es = 0;
        for (let i = 0; i < 9; i++) {
          let rb = 0;
          let rs = 0;
          for (let j = 0; j < 9; j++) {
            rb += scratch.kb[9 * i + j] * local[j];
            rs += scratch.ks[9 * i + j] * local[j];
          }
          eb += local[i] * rb;
          es += local[i] * rs;
        }
        let ew = 0;
        let er = 0;
        for (let c = 0; c < 3; c++) {
          const u0 = local[c];
          const u1 = local[3 + c];
          const u2 = local[6 + c];
          const quad = 2 * (u0 * u0 + u1 * u1 + u2 * u2) + 2 * (u0 * u1 + u1 * u2 + u2 * u0);
          if (c === 0) ew += mw * quad;
          else er += mrot * quad;
        }
        // K_b ∝ h³, K_s ∝ h·s(h) with s'/s = 2(1 − s)/h, M_w ∝ h, M_r ∝ h³.
        sens[k][e] =
          (3 * eb + es * (1 + 2 * (1 - scratch.shearScale)) - lambdas[k] * (ew + 3 * er)) / h;
      }
    }
    for (let k = 0; k < count; k++) {
      const off = (k + 3) * n;
      const shape = new Float32Array(this.nodeCount);
      for (let i = 0; i < this.nodeCount; i++) shape[i] = x[off + 3 * this.perm[i]];
      modes.push({
        frequency: Math.sqrt(lambdas[k]) / (2 * Math.PI),
        lambda: lambdas[k],
        shape,
        thicknessSensitivity: sens[k],
      });
    }
    return { modes, iterations, subspace: x };
  }
}

function rotate(
  source: Float64Array,
  target: Float64Array,
  q: Float64Array,
  n: number,
  m: number,
): void {
  target.fill(0);
  for (let k = 0; k < m; k++) {
    const to = k * n;
    for (let j = 0; j < m; j++) {
      const f = q[j * m + k];
      if (f === 0) continue;
      const so = j * n;
      for (let i = 0; i < n; i++) target[to + i] += f * source[so + i];
    }
  }
}

/**
 * A frequency safely below the first elastic mode of a free plate, used as the
 * shift. It is the uniform free beam's fundamental for the plate's longest
 * dimension and softest direction, scaled down.
 */
export function shiftFrequency(material: Material, thickness: number, longest: number): number {
  const stiffness = Math.min(material.E1, material.E2);
  return 0.25 * 1.028 * (thickness / (longest * longest)) * Math.sqrt(stiffness / material.rho);
}
