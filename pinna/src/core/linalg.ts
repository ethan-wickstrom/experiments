/**
 * Symmetric positive definite matrix in skyline (variable band) storage: row i
 * keeps columns first[i]..i of the lower triangle.
 */
export class Skyline {
  readonly n: number;
  readonly first: Int32Array;
  readonly start: Int32Array;
  readonly data: Float64Array;

  constructor(first: Int32Array) {
    this.n = first.length;
    this.first = first;
    this.start = new Int32Array(this.n + 1);
    for (let i = 0; i < this.n; i++) this.start[i + 1] = this.start[i] + (i - first[i] + 1);
    this.data = new Float64Array(this.start[this.n]);
  }

  add(i: number, j: number, v: number): void {
    if (j > i) return;
    this.data[this.start[i] + (j - this.first[i])] += v;
  }

  /** Replace the matrix by its Cholesky factor L, in place. Returns false if not positive definite. */
  factor(): boolean {
    const { n, first, start, data } = this;
    for (let i = 0; i < n; i++) {
      const fi = first[i];
      const si = start[i] - fi;
      for (let j = fi; j <= i; j++) {
        const fj = first[j];
        const sj = start[j] - fj;
        let s = data[si + j];
        for (let k = fi > fj ? fi : fj; k < j; k++) s -= data[si + k] * data[sj + k];
        if (j < i) {
          data[si + j] = s / data[sj + j];
        } else {
          if (!(s > 0)) return false;
          data[si + i] = Math.sqrt(s);
        }
      }
    }
    return true;
  }

  /** Solve L Lᵀ x = b in place, after factor(). */
  solve(x: Float64Array, offset = 0): void {
    const { n, first, start, data } = this;
    for (let i = 0; i < n; i++) {
      const si = start[i] - first[i];
      let s = x[offset + i];
      for (let k = first[i]; k < i; k++) s -= data[si + k] * x[offset + k];
      x[offset + i] = s / data[si + i];
    }
    for (let i = n - 1; i >= 0; i--) {
      const si = start[i] - first[i];
      const xi = x[offset + i] / data[si + i];
      x[offset + i] = xi;
      for (let k = first[i]; k < i; k++) x[offset + k] -= data[si + k] * xi;
    }
  }
}

/** Symmetric sparse matrix in compressed rows with the full pattern, for products. */
export class Csr {
  readonly n: number;
  readonly rowStart: Int32Array;
  readonly col: Int32Array;
  readonly val: Float64Array;

  constructor(n: number, rowStart: Int32Array, col: Int32Array) {
    this.n = n;
    this.rowStart = rowStart;
    this.col = col;
    this.val = new Float64Array(col.length);
  }

  add(i: number, j: number, v: number): void {
    let lo = this.rowStart[i];
    let hi = this.rowStart[i + 1] - 1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const c = this.col[mid];
      if (c === j) {
        this.val[mid] += v;
        return;
      }
      if (c < j) lo = mid + 1;
      else hi = mid - 1;
    }
    throw new Error("entry outside the sparsity pattern");
  }

  multiply(x: Float64Array, xo: number, y: Float64Array, yo: number): void {
    const { n, rowStart, col, val } = this;
    for (let i = 0; i < n; i++) {
      let s = 0;
      for (let p = rowStart[i]; p < rowStart[i + 1]; p++) s += val[p] * x[xo + col[p]];
      y[yo + i] = s;
    }
  }
}

/** Reverse Cuthill-McKee ordering. Returns perm with perm[old] = new. */
export function reverseCuthillMcKee(adjStart: Int32Array, adj: Int32Array): Int32Array {
  const n = adjStart.length - 1;
  const degree = (i: number) => adjStart[i + 1] - adjStart[i];
  const order = new Int32Array(n);
  const visited = new Uint8Array(n);
  let filled = 0;
  const bfs = (root: number, mark: Uint8Array, out: Int32Array, from: number): number => {
    let head = from;
    let tail = from;
    out[tail++] = root;
    mark[root] = 1;
    while (head < tail) {
      const v = out[head++];
      const begin = tail;
      for (let p = adjStart[v]; p < adjStart[v + 1]; p++) {
        const u = adj[p];
        if (!mark[u]) {
          mark[u] = 1;
          out[tail++] = u;
        }
      }
      // Visit lower-degree neighbours first.
      for (let a = begin + 1; a < tail; a++) {
        const u = out[a];
        let b = a - 1;
        while (b >= begin && degree(out[b]) > degree(u)) {
          out[b + 1] = out[b];
          b--;
        }
        out[b + 1] = u;
      }
    }
    return tail;
  };
  const scratch = new Int32Array(n);
  for (let seed = 0; seed < n; seed++) {
    if (visited[seed]) continue;
    // Find a pseudo-peripheral start by repeated breadth-first search.
    let root = seed;
    for (let iter = 0; iter < 4; iter++) {
      const mark = visited.slice();
      const end = bfs(root, mark, scratch, 0);
      const last = scratch[end - 1];
      if (last === root) break;
      root = last;
    }
    filled = bfs(root, visited, order, filled);
  }
  const perm = new Int32Array(n);
  for (let k = 0; k < n; k++) perm[order[k]] = n - 1 - k;
  return perm;
}

/** Eigen-decomposition of a dense symmetric matrix by cyclic Jacobi rotations. a is destroyed. */
export function jacobiEigen(
  a: Float64Array,
  n: number,
): { values: Float64Array; vectors: Float64Array } {
  const v = new Float64Array(n * n);
  for (let i = 0; i < n; i++) v[i * n + i] = 1;
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0;
    let diag = 0;
    for (let i = 0; i < n; i++) {
      diag += a[i * n + i] * a[i * n + i];
      for (let j = i + 1; j < n; j++) off += a[i * n + j] * a[i * n + j];
    }
    if (off <= 1e-30 * diag) break;
    for (let p = 0; p < n - 1; p++) {
      for (let q = p + 1; q < n; q++) {
        const apq = a[p * n + q];
        if (apq === 0) continue;
        const theta = (a[q * n + q] - a[p * n + p]) / (2 * apq);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1);
        const s = t * c;
        for (let k = 0; k < n; k++) {
          const akp = a[k * n + p];
          const akq = a[k * n + q];
          a[k * n + p] = c * akp - s * akq;
          a[k * n + q] = s * akp + c * akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = a[p * n + k];
          const aqk = a[q * n + k];
          a[p * n + k] = c * apk - s * aqk;
          a[q * n + k] = s * apk + c * aqk;
        }
        for (let k = 0; k < n; k++) {
          const vkp = v[k * n + p];
          const vkq = v[k * n + q];
          v[k * n + p] = c * vkp - s * vkq;
          v[k * n + q] = s * vkp + c * vkq;
        }
      }
    }
  }
  const values = new Float64Array(n);
  for (let i = 0; i < n; i++) values[i] = a[i * n + i];
  return { values, vectors: v };
}

/**
 * Solve the dense generalized symmetric problem A q = θ B q with B positive definite.
 * Returns eigenvalues ascending and B-orthonormal eigenvectors as columns of a row-major n×n matrix.
 */
export function denseGeneralizedEigen(
  a: Float64Array,
  b: Float64Array,
  n: number,
): { values: Float64Array; vectors: Float64Array } {
  // Cholesky B = L Lᵀ.
  const l = new Float64Array(n * n);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let s = b[i * n + j];
      for (let k = 0; k < j; k++) s -= l[i * n + k] * l[j * n + k];
      if (i === j) {
        if (!(s > 0)) throw new Error("projected mass matrix is not positive definite");
        l[i * n + i] = Math.sqrt(s);
      } else {
        l[i * n + j] = s / l[j * n + j];
      }
    }
  }
  // C = L⁻¹ A L⁻ᵀ.
  const c = Float64Array.from(a);
  for (let col = 0; col < n; col++) {
    for (let i = 0; i < n; i++) {
      let s = c[i * n + col];
      for (let k = 0; k < i; k++) s -= l[i * n + k] * c[k * n + col];
      c[i * n + col] = s / l[i * n + i];
    }
  }
  for (let row = 0; row < n; row++) {
    for (let i = 0; i < n; i++) {
      let s = c[row * n + i];
      for (let k = 0; k < i; k++) s -= l[i * n + k] * c[row * n + k];
      c[row * n + i] = s / l[i * n + i];
    }
  }
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const m = (c[i * n + j] + c[j * n + i]) / 2;
      c[i * n + j] = m;
      c[j * n + i] = m;
    }
  }
  const { values, vectors } = jacobiEigen(c, n);
  const order = Array.from({ length: n }, (_, i) => i).sort((x, y) => values[x] - values[y]);
  const outValues = new Float64Array(n);
  const outVectors = new Float64Array(n * n);
  for (let k = 0; k < n; k++) {
    const src = order[k];
    outValues[k] = values[src];
    // q = L⁻ᵀ v
    for (let i = n - 1; i >= 0; i--) {
      let s = vectors[i * n + src];
      for (let j = i + 1; j < n; j++) s -= l[j * n + i] * outVectors[j * n + k];
      outVectors[i * n + k] = s / l[i * n + i];
    }
  }
  return { values: outValues, vectors: outVectors };
}
