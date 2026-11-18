# Predicting complete V8 frames on unfamiliar source

A predictor trained on 54 scalar TypeScript invocations predicted all 28 function entries on seven independently written programs and completed 25 raw rollouts from the call arguments through the terminal outcome. Across 204 teacher-forced nonterminal transitions it predicted 201 exact frames and abstained three times. Each abstention occurred while evaluating a return expression with a zero operand. This is a result on single-function integer programs under one observer and compiler.

## From invocation to outcome

The oracle observes the module before the harness calls its export. Four different calls to each of 14 held sources had identical observations before that external action and four different entry frames. Even an optimal deterministic predictor given source and that history can get at most 14/56 entries right on these examples. `start(call)` receives source, export and arguments at invocation. `predict(files, frame)` receives only source and the current observation. A rollout feeds each predicted frame into the next step. The outcome, future sites, function arguments after entry, and number of remaining pauses are unavailable to the predictor.

The experimental `fitStructured` builds a graph of parameter writes, braced conditionals, nonempty while loops and explicit returns. The oracle supplies training labels for scalar operations and predicates. At inference the graph supplies possible successors, binding slots, and source-relative anchors. Consistent bounded bilinear rules evaluate expressions recursively. Consistent comparison rules select a successor. A separately fitted transducer chooses an event kind and coordinate jointly for that edge. A step on a return can emit another observation within the statement. An assignment followed by a return can instead land directly on its payload. Candidate context partitions maximize training coverage, then minimize the number of features. Tied partitions and surviving anchors must agree on the prediction. Static CFG and operator hypothesis classes are supplied inductive biases.

## Three prospective tests and one intervention

1. **Source and layout transfer.** Freeze eight training bodies and seven held bodies. Each curriculum costs 48 invocations. Each held body has four inputs and two new layouts. The original adjacent-frame learner with AST anchors yielded 338 exact, zero wrong and 16 abstained nonterminal frames on either curriculum. It completed 40/56 rollouts, including both members of all eight equal-return/opposite-write pairs. The eight Euclid programs encountered an unsupervised incoming edge. The eight XOR programs used an untrained operator. The compiler-mapped return prior tied the AST model. Fixed-layout training with character offsets yielded 296 exact, 42 wrong and 16 abstained frames and 8/56 paths. With varied training, offsets gave 282 exact, zero wrong, 72 abstained and 0/56 paths.
2. **Explicit invocation.** Reuse the first pause of each training call as an additional landing label. On four fresh functions, entry prediction yielded 15 exact and five abstentions. Twelve of 20 complete paths succeeded from the predicted entry. From observed entry the original fit completed 5/20 and the augmented fit completed 12/20. All five unsupported `for` invocations remain in the denominator. In the other three failed invocations, V8 stepped at a return reached through a control-flow join.
3. **Matched invocation budget at joins.** Augment the same 48 runs with six new calls. One arm repeats familiar programs. The other exposes ambiguous landing behavior at joins. Cross both arms with a feature indicating multiple reachable CFG predecessors. Fresh evaluation has three bodies and four calls per body.
4. **Independent author.** Freeze the targeted fit with the join feature, then take all 28 invocations from a separate author. The author had neither collected these labels nor queried the predictor. All 28 first frames were exact. Paths by source in manifest order were 4/4, 3/4, 4/4, 4/4, 4/4, 4/4 and 2/4. The fit abstained once on `x * y` with `x = 0` and twice on `x + (y - x) * y` with `x = y`. Multiplication encounters a zero in each case. The integer hypothesis class conservatively abstains on zero operands because its algebra lacks signed zero. All other function transitions, including 28 terminal readouts, were exact. These 28 calls are repeated observations on seven bodies.

| Additional training | Join feature | Exact / wrong / abstained nonterminal | Complete paths |
| ------------------- | ------------ | ------------------------------------- | -------------- |
| Familiar programs   | Off          | 51 / 7 / 0                            | 5/12           |
| Familiar programs   | On           | 51 / 7 / 0                            | 5/12           |
| Join programs       | Off          | 49 / 0 / 9                            | 3/12           |
| Join programs       | On           | 58 / 0 / 0                            | 12/12          |

The extra six calls yielded 12 observed function frames in the familiar arm and 22 in the join arm. The intervention held the number of calls fixed. Comparing feature on/off _within_ an arm also holds the labels fixed. Reuse of the earlier test sets is a development diagnostic. After the targeted intervention the model completed 48/56 on the original and 15/20 on confirmation.

## Controls and observability

On the original 354 nonterminal targets, persistence copied the right locals 184 times and predicted zero full frames. Permuting the learned arithmetic labels preserved the event and stack 332 times on varied training, yet produced 190 wrong full frames and zero complete paths. Both syntax retrieval and the source-keyed model abstained on every nonterminal frame. Terminal readout got all 56 observed outcomes right and completed zero paths. Survival from observed entry for the original AST model was 44/56 at one step, 44/56 at two, 22/26 at four, 14/14 at eight, 6/6 at sixteen and 2/2 at thirty-two. Later horizons condition on a sufficiently long reference path.

All 224 declared split records collected successfully on the pinned stack. Every module frame has an inexact projection of undefined. Five confirmation root frames contain an unavailable loop binding. All terminal outcomes were exact. The mask audit counts each projected snapshot at the granularity the oracle actually observes.

## Replay or recollect

From `cwm/` use Bun 1.4.4 and Node 24.19.0. Every benchmark command checks the source and arguments against the split manifest and hashes the entire schema-decoded ordered trajectory before consuming its labels. All eight fingerprints matched an independent collection from empty caches. Keeping just the initial module frame and the final return would give terminal readout 56/56 paths under an unsealed scorer. The regression exercises that exact corruption.

```sh
d=bench/recurrent/data
bun bench/recurrent/replay.ts audit "$d"
bun bench/recurrent/replay.ts score "$d/fixed.jsonl.gz" "$d/varied.jsonl.gz" "$d/held.jsonl.gz"
bun bench/recurrent/replay.ts confirm "$d/varied.jsonl.gz" "$d/confirm.jsonl.gz"
bun bench/recurrent/replay.ts junctions "$d"
bun bench/recurrent/replay.ts blind "$d"
```

For an independent oracle reproduction, use a new cache directory for each split.

```sh
out=$(mktemp -d)
for split in fixed varied held confirm repeated targeted junction blind; do
  bun bench/recurrent/replay.ts collect "$split" "$out/$split" "$out/$split.jsonl" || exit 1
done
bun bench/recurrent/replay.ts audit "$out"
```

The [protocol](protocol.md) records the order of hypotheses and freezes. The [research design](../../RESEARCH.md) describes how to extend the observer model to histories, uncertain state and unseen source families. Heap effects, multiple frames, exceptions, async scheduling, compiler shifts and general repository code require separate tests.
