# Branch successor probe: preregistration

Freeze the split in `cases.ts` before labels. Six training bodies isolate three scalar assignments and three two-way predicates. Less/greater see all three order relations; equality sees only left < right. Five fresh source bodies each get the same four new input pairs. They cover nested decisions, expression predicates/arms, branch writes followed by a join, partial evidence, and an unseen predicate token.

Supply a static CFG from Oxc (branch/next/return), lexical slots, literal copies and assignment destinations. Learn scalar operator tables from observed assignments using the unmodified composition learner. Learn predicate tokens from observed arms, retaining the constant true/false and six order/equality rules consistent with all training rows. Vote only when all survivors agree on the query. Compare a majority arm per token (ties false, unknown abstain), flipped predicate decisions, and no predicate training. All controls use the same scalar and raw-site training.

Freeze the models before collecting held-out sources. Score one-step exact semantic successor site **and** full parameter store, or terminal value, and uninterrupted semantic paths from parameters. For raw sites, learn parser-relative pause offsets and transition modes on training only. Score each pair of consecutive entry-function pauses (file/line/column/function), with no claim about the next stack, locals or event kind. Never use held-out possible-breakpoint lists or oracle successors to supply a prediction. Report exact/wrong/abstained counts by family and semantic source site; keep raw-site counts separate.

## Result

On [prespecified sources](https://github.com/ethan-wickstrom/experiments/commit/08b9aa2ae89b057483dfd46a24b4ceecbd081c6c), the [frozen model](https://github.com/ethan-wickstrom/experiments/commit/9d11e63e3be58259b06d617330d81387d0c30d7a) followed every path in the three families using identified predicates. Two of four partially covered paths were identifiable; none with the unseen token were. Columns below are **exact / wrong / abstained** one-step predictions. Raw sites and semantic boundaries are different targets; both happen to have 50 queries here.

| Model                 | Semantic successor | Next raw V8 site | Complete semantic paths |
| --------------------- | -----------------: | ---------------: | ----------------------: |
| Learned               |         43 / 0 / 7 |      16 / 28 / 6 |                   14/20 |
| Majority arm          |         37 / 8 / 5 |      10 / 36 / 4 |                    9/20 |
| Flipped decision      |        27 / 16 / 7 |       0 / 44 / 6 |                    0/20 |
| No predicate training |        27 / 0 / 23 |      0 / 28 / 22 |                    0/20 |

| Learned model by family | Semantic successor | Next raw V8 site | Complete semantic paths |
| ----------------------- | -----------------: | ---------------: | ----------------------: |
| Write and join          |         12 / 0 / 0 |        4 / 8 / 0 |                     4/4 |
| Nested decisions        |         10 / 0 / 0 |        6 / 4 / 0 |                     4/4 |
| Fallthrough             |         10 / 0 / 0 |        4 / 6 / 0 |                     4/4 |
| Partial equality        |          6 / 0 / 2 |        2 / 4 / 2 |                     2/4 |
| Unseen predicate        |          5 / 0 / 5 |        0 / 6 / 4 |                     0/4 |

**Where the misses are.** At decision sites the learned model had 16 exact and six abstentions for both targets. All eight assignment successors were semantically exact; all eight next raw sites were wrong. At returns 19 semantic values were exact and one abstained (the frozen scalar learner declines zero operands); all 20 next raw sites were wrong. For example the join program on `(8,3)` updates `x` to 10 and returns 7. From its return-statement pause at 7:1 the learned offset predicts 7:8, as in training's single-name returns. V8 pauses at 7:12 on `return x - y;`. This is a column error, not a wrong returned value.

**What supervision bought.** Of eight candidate predicate rules, training retained only LT for `<`, GT for `>`, and four candidates (constant false, GT, GE, EQ) for `===`. The arm label comes from the next observed training statement, not evaluating the predicate. Isolated assignments uniquely selected addition, subtraction and multiplication in the original scalar basis. AST paths (e.g. `b.0T.0`), branch targets, assignment slots, join edges and loop-free statement order are supplied. A rollout receives only the statically parsed source and parameter values. One-step scoring is teacher-forced; a correct return observed after a missed decision cannot repair a rollout.

**Raw mapper.** For each current statement kind, frame kind and column offset from statement start, learn whether a training pause stayed at another relative offset, crossed to the semantic successor, or ended. If it crossed, predict the landing offset from training source/destination statement kinds, falling back to the destination kind alone; disagreement abstains. Decode on the query AST. No held-out breakpoint list, history or successor map is supplied. Raw evaluation uses adjacent function pauses only (no module initialization or terminal) and predicts neither store nor stack. The projector checks that observed semantic edges exist in the static CFG and fails on skipped statements instead of imputing missing labels.

## Reproduce

From `cwm/`, Bun 1.4.4 and Node 24.19.0 on PATH; collection requires fresh output paths. The score command prints every source-site and family breakdown for all four models. Verification checks every observed training path, ambiguous-guard survivors, an untrained control, and reversal under swapped training labels.

```sh
bun bench/branch/replay.ts collect train branch-train.jsonl
bun bench/branch/replay.ts verify branch-train.jsonl
bun bench/branch/replay.ts collect held branch-held.jsonl
bun bench/branch/replay.ts score branch-train.jsonl branch-held.jsonl > branch-scores.json
```

The 32 training and 20 held-out traces are normalized V8 observations, not computed labels. Offline scoring reproduces without Node on PATH (stdout SHA-256 `cb30a0d1ac3461d99eb50ffe20e2656e2870ef976ff37b029006232cde713765`). The five small templates do not establish transfer to loops, exceptions, opaque values or arbitrary V8 pauses.
