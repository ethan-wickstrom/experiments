import { Matrix } from "ml-matrix";
import type { Example, Forecast, Input } from "./types.ts";

function tokens(x: Input) {
  return [
    ["setup", x.setup],
    ["write", x.write],
    ["signal", x.signal],
    ["index", x.index],
    ["shape", x.before.map((row) => row.length)],
    ...x.before.flatMap((row, i) => row.map((v, j) => ["element", i, j, v])),
  ].map((t) => JSON.stringify(t));
}

function softmax(rows: Matrix) {
  for (let i = 0; i < rows.rows; i++) {
    const row = rows.getRow(i),
      max = Math.max(...row);
    const exp = row.map((v) => Math.exp(v - max)),
      sum = exp.reduce((a, b) => a + b, 0);
    rows.setRow(
      i,
      exp.map((v) => v / sum),
    );
  }
  return rows;
}

/** Same observed inputs, but one joint softmax over entire observed delta tensors. */
export function fitJoint(train: Example[], seed: number): Forecast {
  if (!train.length) return () => [];
  const vocabulary = new Map<string, number>(),
    labels = new Map<string, number>(),
    deltas: number[][][] = [];
  const rows = train.flatMap((e) => [e, { ...e, input: { ...e.input, signal: null } }]);
  for (const { input } of rows)
    for (const token of tokens(input))
      if (!vocabulary.has(token)) vocabulary.set(token, vocabulary.size);
  function encode(x: Input) {
    const row = Array<number>(vocabulary.size + 1).fill(0);
    row[vocabulary.size] = 1;
    for (const token of tokens(x)) {
      const i = vocabulary.get(token);
      if (i !== undefined) row[i] = 1;
    }
    return row;
  }
  const X = new Matrix(rows.map((r) => encode(r.input)));
  const target = rows.map(({ input, after }) => {
    if (
      input.before.length !== after.length ||
      after.some((v, i) => v.length !== input.before[i]!.length)
    )
      throw new Error("Shape-changing writes are outside the delta vocabulary");
    const delta = after.map((v, i) => v.map((n, j) => n - input.before[i]![j]!));
    const key = JSON.stringify(delta);
    if (!labels.has(key)) {
      labels.set(key, deltas.length);
      deltas.push(delta);
    }
    return labels.get(key)!;
  });
  function weights(n: number, m: number) {
    const scale = Math.sqrt(6 / (n + m));
    return Matrix.zeros(n, m).apply(function (i, j) {
      seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
      this.set(i, j, scale * ((2 * seed) / 2 ** 32 - 1));
    });
  }
  const W = weights(X.columns, 32),
    V = weights(W.columns, labels.size),
    bias = Matrix.zeros(1, labels.size);
  const forward = (hidden: Matrix) => softmax(hidden.mmul(V).addRowVector(bias));
  const XT = X.transpose();
  for (let t = 0; t < 600; t++) {
    const H = X.mmul(W).tanh(),
      D = forward(H);
    for (const [i, k] of target.entries()) D.set(i, k, D.get(i, k) - 1);
    D.mul(0.15 / rows.length);
    const back = D.mmul(V.transpose()).mul(Matrix.pow(H, 2).mul(-1).add(1));
    W.sub(XT.mmul(back));
    V.sub(H.transpose().mmul(D));
    bias.subRowVector(D.sum("column"));
  }
  return (x) => {
    const p = forward(Matrix.rowVector(encode(x)).mmul(W).tanh()).getRow(0);
    const compatible = deltas.flatMap((d, k) =>
      d.length === x.before.length && d.every((row, i) => row.length === x.before[i]!.length)
        ? [k]
        : [],
    );
    const mass = compatible.reduce((s, k) => s + p[k]!, 0);
    return compatible.map((k) => ({
      prob: p[k]! / mass,
      state: deltas[k]!.map((row, i) => row.map((v, j) => v + x.before[i]![j]!)),
    }));
  };
}
