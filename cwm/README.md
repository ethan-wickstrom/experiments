# A code world model for TypeScript

Given a paused TypeScript program, what will its next observable state be? The **oracle** runs the program once to collect labels. The **model** learns from those labels and predicts without running the program. These are separate operations. This is a small, CPU-only testbed inspired by [Meta's CWM](https://github.com/facebookresearch/cwm), not its weights, tokenizer, or benchmark results.

For the experimental design and measured results beyond the raw-frame baseline, see [Learning compositional updates under partial observation](RESEARCH.md).

The [recurrent raw-frame experiment](bench/recurrent/README.md) adds a source-held-out predictor for scalar assignments, branches and loops. It includes frozen oracle observations and commands to replay training, controls and independent falsification.

## Run

Use Bun 1.4+ and Node 24.11+ on PATH. Bun runs the library, CLI and tests. Node is only the debuggee: a worker connects to its [V8 inspector](https://nodejs.org/api/inspector.html#support-of-breakpoints) without opening a network port.

```sh
cd cwm
bun install --frozen-lockfile
echo '{"files":{"main.ts":"export function run(x: number) { return x + 1; }"},"entry":"main.ts","fn":"run","args":[4]}' | bun cwm.ts
```

Input and output are JSONL, one program or trace per line. A trace carries its input source and arguments, debugger frames, and the awaited entry outcome. Redirect stdout to keep a dataset. To fit and score, use **different** inputs for the two datasets:

```sh
bun cwm.ts < train-programs.jsonl > train.jsonl
bun cwm.ts < held-out-programs.jsonl > held-out.jsonl
bun cwm.ts score train.jsonl held-out.jsonl
```

`total` counts adjacent observation pairs including the final outcome; `predicted` excludes abstentions; `correct` requires an exact match to the whole next observation, not just its source location. This is teacher-forced, one-step scoring. Splitting by arguments measures input generalization; split by source to test transfer. The model stores training examples in memory.

### Compare predictors on identical observations

The small [evaluation corpus](corpus.ts) emits programs, not labels. Collect both splits once, then run each predictor's score command against the **same files**. To isolate a family, append its name (e.g. `recursion`) to both generator commands.

```sh
bun corpus.ts train | bun cwm.ts > train.jsonl
bun corpus.ts held-out | bun cwm.ts > held-out.jsonl
bun cwm.ts score train.jsonl held-out.jsonl
```

Report correct, wrong (`predicted - correct`), and abstained (`total - predicted`) together. These eight small families share source between splits; they diagnose arithmetic, coupled inputs, branches, array mutation and recursion, not general TypeScript reasoning. Scoring reads held-out traces one record at a time.

For a larger experiment, run the [1,024-run source-transfer benchmark](bench/README.md). It includes a resumable four-process collector, a whole-program holdout, and a control that can get terminal observations right without predicting a single instruction.

## Predict multiple steps

```ts
import { trace, WorldModel } from "./cwm.ts";

const code = {
  files: { "math.ts": "export function sum(x: number, y: number) { return x + y; }" },
  entry: "math.ts",
  fn: "sum",
};
const train = await Promise.all(
  [
    [1, 0],
    [0, 1],
    [2, 3],
    [-1, 2],
  ].map((args) => trace({ ...code, args })),
);
const model = new WorldModel().fit(train);
const heldOut = await trace({ ...code, args: [8, 5] });
const start = heldOut.frames.find((frame) => frame.stack[0]?.fn === "sum")!;
console.log([...model.rollout(code.files, start, 8)].at(-1));
// { kind: "returned", result: { value: 13, exact: true } }
```

Only the starting frame is observed. Subsequent inputs to `rollout` are its own predictions. It stops at a predicted terminal, an abstention (`unseen`), or the step budget. At a known action the model retrieves the closest frames and carries unchanged locals forward. It returns a successor only if the tied candidates agree on the whole prediction. This matters when the same visible frame precedes different hidden state or entry arguments.

Each control-flow edge can learn scalar affine updates. Independent observations determine the coefficients; remaining examples check them. Coupled variables need not determine unique coefficients: when training always has `i === a`, a prediction at `(7, 7)` may still be identifiable, whereas `(7, 8)` is not. The model refuses to apply that fit outside the observed affine subspace (up to numerical tolerance). It never rounds a predicted value to an integer. It cannot in general infer unseen branches, algorithms or heap effects. The list-insertion test checks the **oracle**, not model generalization.

## Repository edits

```ts
import { mutations, repair } from "./cwm.ts";

const program = {
  files: { "main.ts": "export function sum(a: number, b: number) { return a + b; }" },
  entry: "main.ts",
  fn: "sum",
  args: [6, 2],
};
const [edit] = await mutations(program);
const history = await repair(program, edit!, 8);
// Run mutant (fail), apply its exact inverse, run original (pass).
```

`episode(initial, actions, expected)` also accepts arbitrary guarded edits and runs. Rejected edits leave the source unchanged. A run is graded only on the entry outcome; a nested return is not success. Failed edits, errors, wrong answers and inconclusive comparisons remain in the history.

## What the oracle observes

- [Oxc](https://oxc.rs/docs/guide/usage/transformer.html) erases TypeScript and emits source maps. V8 executes native ESM, including live bindings and cycles. Use explicit relative `.ts` or `.js` imports within the supplied files. No packages, dynamic imports, import metadata, eval, timers or host I/O. Guest code is transpiled, not type-checked.
- A step is an executed, source-mapped V8 break location, **not** every textual line. One line can contain several stops. Line and column are one-based. The innermost site comes first. Locals are visible debugger bindings of that frame; module/global state, heap identity and asynchronous parent stacks are not reconstructed.
- Return stops may belong to inner calls; exception stops can be caught. The separate terminal outcome is the actual awaited entry result or thrown value, including module-initialization throws.
- To read scopes, the debugger calls a private projection function initialized before module evaluation. It uses host intrinsics and own data descriptors, not guest property reads, coercions or serialization. A local or nested native Error or Proxy is opaque. If V8 has already exposed a native Error in a pause's exception, receiver or return value, collection fails rather than trusting a possibly altered execution. Thus throwing or directly returning an Error is not generally supported; a caught primitive exception still is. This is a tested observation contract, not a proof of noninterference for all V8 behavior.
- JSON snapshots are detached. Unavailable bindings, accessors, non-JSON values and bounded projections carry `exact: false`. Each snapshot is limited to 256 visited values, six levels and 4,096 characters per string. No placeholder can earn a passing grade. Duplicate frame values are retained because repeats can be real loop iterations.
- By default an execution has a ten-second deadline, a 2,048-frame budget and a 192 MiB V8 old-space ceiling. A failed collection yields an error, never invented frames. Use **trusted programs only**: [node:vm is not a security boundary](https://nodejs.org/api/vm.html). The limits are not an OS memory or security sandbox.

See [decisions](DECISIONS.md) for the tradeoffs and [checks](CLAUDE.md) for reproduction.
