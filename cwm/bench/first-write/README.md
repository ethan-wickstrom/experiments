# Can the baseline predict one array write?

**No on this witness. It never reached the write and still abstained when given the exact pre-write frame.** The first failure is retrieval, not an incorrect arithmetic operation: the [frozen lookup key](https://github.com/ethan-wickstrom/experiments/blob/531db2a65abf90aa2547e9c4e5ca9ac524bb9f8a/cwm/cwm.ts#L488-L491) includes the filename. None of the training traces contains `histogram.ts`, so [lookup returns before consulting any learned update](https://github.com/ethan-wickstrom/experiments/blob/531db2a65abf90aa2547e9c4e5ca9ac524bb9f8a/cwm/cwm.ts#L588-L619). This is **not** evidence that a changed key alone would learn the write.

## Witness

Call `run(1, -2)`:

```ts
export function run(x: number, y: number) {
  const a = [0, 0];
  for (const n of [x, y]) a[Math.abs(n) % 2]++;
  return a;
}
```

Change **only** the index to `1-(Math.abs(n)%2)`. Both versions visit one even and one odd input, so the final histogram cannot distinguish which bin was incremented first. Two loop iterations are enough to expose and then erase that distinction. The third program is the original with two leading newlines: a position-only control.

[Meta's trace guide](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/PROMPTING_GUIDE.md#L105-L118) distinguishes a frame's **action** (Python source line) from its **observation** (locals). Score their analogues separately here: next mapped V8 site and next exact array. A correct site alone cannot identify the write: both variants return to the same loop header.

| Version         | TS site, before → after | Emitted JS site, before → after | Array observed, before → after | One-step site / array | Plain Node return |
| --------------- | ----------------------- | ------------------------------- | ------------------------------ | --------------------- | ----------------- |
| Original        | 3:30 → 3:11             | 3:33 → 3:13                     | [0,0] → [0,1]                  | abstained / abstained | [1,1]             |
| Two blank lines | 5:30 → 5:11             | 3:33 → 3:13                     | [0,0] → [0,1]                  | abstained / abstained | [1,1]             |
| Opposite bin    | 3:33 → 3:11             | 3:37 → 3:13                     | [0,0] → [1,0]                  | abstained / abstained | [1,1]             |

**Rollout:** from the actual first `run` frame (pause 1), no predicted frame in any version. **One-step:** queried again at pause 5, with `x=1, y=-2, n=1, a=[0,0]`; no prediction. The table's successor comes from V8 pause 6, not from the model. The frozen predictor did not even copy the return. A separate **return readout** can copy the exact `[1,1]` already present at the last return frame in all three cases. It has no return value to copy at the write. This mirrors the distinction between [Meta's parsing of locals, source line and return argument](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/demos/cwmdbg.py#L218-L255). No Meta checkpoint was evaluated.

## Chain of evidence

1. Oxc emits `a[Math.abs(n) % 2]++` or `a[1 - Math.abs(n) % 2]++`; the missing parentheses do not change JS operator precedence. The recorded [Inspector script hash](https://chromedevtools.github.io/devtools-protocol/tot/Debugger/#event-scriptParsed) matches the emitted bytes.
2. Map each entry-function pause from zero-based Inspector coordinates through Oxc's source map. Find the **first exit from the sole update expression** in execution order, without looking at the successor values. No breakpoint on a made-up "write instruction": the store occurs **between** two pauses. [Meta's demo resolves generated source text to a line](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/demos/cwmdbg.py#L255-L274); that granularity would collapse these sites onto one line.
3. In each pause, follow the block/local scope's `Runtime.getProperties` descriptor for `a` to that pause's array descriptor. Read the own data values of `0`, `1` and `length`; compare with the normalized exact snapshots. Do not compare object handles across pauses. At entry the `a` binding is unavailable; earlier in the loop `n` is unavailable. Neither is evidence of a particular value. The snapshots establish array contents, not heap identity or an exact machine instruction.
4. Fit the unchanged baseline on the **previous** benchmark's 576 ordered training records before querying any variant. Check both hashes and the absence of the guest filename. Unlike [Meta's debugger, which conditions on source plus prior frames](https://github.com/facebookresearch/cwm/blob/7930e0298bf32aae28cc0e35e18a54c772603364/demos/cwmdbg.py#L159-L180), each call here sees only source and the current frame. Query all observed frames without passing successor, arguments separately, or outcome. A second fresh debuggee logs raw protocol traffic and must reproduce the entire normalized execution. A third ordinary Node process runs the original TypeScript without Oxc or Inspector to check the **final** value only.
5. [Jane Street's positional-encoding article](https://blog.janestreet.com/using-group-theory-to-explore-positional-encodings-attention/) motivates an invariance question: does translating both locations matter? The whitespace control shifts both TS lines by two, while the emitted JS, next-site displacement and array change stay the same. This checks oracle alignment, **not** learned invariance: identical abstentions are not successes. No RoPE or representation change was tested.

## Replay

From the repository root, use Bun 1.4.4 and Node 24.19.0 on PATH. Use a fresh output path; the runner refuses to overwrite evidence.

```sh
cd cwm
bun install --frozen-lockfile
bun bench/first-write/replay.ts first-write-evidence
```

The replay includes the compressed training split from the [original experiment](../README.md); it neither grows the corpus nor recollects training data. It checks the model source and uncompressed training bytes against SHA-256 and fails if the frozen experiment has changed. The output includes the comparison (`witness.json`) and, per version, the TypeScript, emitted ESM, source map, raw Inspector events/property responses and normalized trace. Protocol handles are session-local; compare the witness, not the raw JSONL bytes, across replays.

This pair was disclosed before this experiment. It localizes a failure; it does not estimate generalization. Any claim of a fix needs a fresh pair scored after freezing that fix.
