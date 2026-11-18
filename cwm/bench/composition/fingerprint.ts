import assert from "node:assert/strict";
import { cache, collect, load } from "../collect.ts";
import { sourceOf } from "./cases.ts";
import { fit, type Atom } from "./model.ts";
import { example, project } from "./project.ts";

/** One injective query for all multilinear polynomials with coefficients in [-bound,bound]. */
export function fingerprintInput(arity: number, bound: number): number[] | undefined {
  if (!Number.isSafeInteger(arity) || arity < 1 || !Number.isSafeInteger(bound) || bound < 1)
    return;
  let power = 2n * BigInt(bound) + 1n,
    max = BigInt(bound);
  const args: number[] = [];
  for (let i = 0; i < arity; i++) {
    max *= 1n + power;
    if (max > BigInt(Number.MAX_SAFE_INTEGER)) return;
    args.push(Number(power));
    power *= power;
  }
  return args;
}

async function run(root: string, live: boolean) {
  const tokens = ["+", "-", "*", "|", "^"];
  const path = await cache(root);
  async function rows(args: number[]) {
    const programs = tokens.map((op, i) => {
      const entry = "atom" + i + ".ts";
      return {
        entry,
        fn: "run",
        args,
        files: { [entry]: sourceOf({ id: entry, body: [`const m = x ${op} y;`, "return m;"] }) },
      };
    });
    if (live) assert.equal((await collect(root, 4, programs)).failed, 0);
    return Promise.all(programs.map(async (p) => example(project(await load(path(p), p)))));
  }
  const args = fingerprintInput(2, 1)!;
  const training = await rows(args),
    model = fit(training),
    check = [14, 6];
  function predict({ expr }: Atom) {
    const plan = { names: ["x", "y", "m"], params: 2, code: [{ line: 2, expr, returns: false }] };
    const next = model.next(plan, { store: check, pc: 0 });
    return next && "store" in next ? next.store.at(-1) : null;
  }
  const predictions = training.map(predict); // No check labels have been requested.
  const checks = await rows(check),
    audited = fit([...training, ...checks]);
  return {
    args,
    check,
    operators: training.map(({ expr, z }, i) => ({
      token: expr.op,
      observed: z,
      fit: model.survivors[expr.op],
      predicted: predictions[i],
      actual: checks[i]!.z,
      consistentAfterCheck: audited.survivors[expr.op]!.length,
    })),
  };
}

if (import.meta.main) {
  const [mode, root] = process.argv.slice(2);
  if ((mode !== "collect" && mode !== "score") || !root)
    throw new Error("Usage: fingerprint.ts collect|score CACHE");
  console.log(JSON.stringify(await run(root, mode === "collect"), null, 2));
}
