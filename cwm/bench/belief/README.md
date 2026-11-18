# Can history distinguish arrays that look identical?

At the pre-write pause in `b = flag ? a : [...a]; flag = false; a[index]++`, both runs show **the same stack, locals and arrays**. At index zero the written array becomes `[3,5]` in both runs; the other array becomes `[3,5]` in one and stays `[2,5]` in the other. Both return 7. A current-only predictor cannot know which successor occurred. The earlier flag is observable; object identity is not.

[Preselected fixtures](https://github.com/ethan-wickstrom/experiments/commit/9ad9a45539c7eb005795e0c226dc4ddfc8e2b4f8) cross four setup expressions with four writes. A checkerboard holds out eight entire sources; every primitive appears twice per split. Each source runs with both historical signals and indices. The [projector](cases.ts) finds the write's **unique exit by source span**, checks adjacent V8 frames, permits no unexpected changes, and fails on inexact labels. Whitespace-normalized expression keys, named array roles, breakpoint alignment and the selection of one past flag are supplied. No alias labels, entry arguments, expected arrays or return values go to the model.

## Results on 32 held-out writes

A decision requires a unique most likely **joint** state; a tie counts as abstaining. Brier is the multiclass sum of squares; an empty forecast assigns all mass to an extra abstention outcome. Each of the eight cells must get all four trials right to count as perfect.

| Predictor                                  | Exact / wrong / abstain | Perfect cells |       Brier | Natural-log loss |
| ------------------------------------------ | ----------------------- | ------------: | ----------: | ---------------: |
| Sparse patch + history belief, 32 labels   | 32 / 0 / 0              |             8 |           0 |                0 |
| Same, minimum-cover 8 labels               | 32 / 0 / 0              |             8 |           0 |                0 |
| Same, uniform 8 labels, 20 seeds           | 12–21 / 0 / 11–20       |           0–4 | 0.688–1.250 |                ∞ |
| Same, history masked                       | 0 / 0 / 32              |             0 |       0.500 |             ln 2 |
| Same, training signal inverted             | 0 / 32 / 0              |             0 |           2 |                ∞ |
| No labels / joint lookup (each)            | 0 / 0 / 32              |             0 |           2 |                ∞ |
| Persist both arrays                        | 0 / 32 / 0              |             0 |           2 |                ∞ |
| Joint neural delta classifier, three seeds | 12–17 / 15–20 / 0       |             0 | 0.512–0.544 |      0.839–0.916 |
| Same, history masked                       | 16 / 16 / 0             |             0 | 0.519–0.537 |      0.847–0.911 |

The factor model predicts both members of all 16 test twin pairs. Interchanging **only** the historical signal switches the predicted response of the second array and leaves the directly written array unchanged. Removing the signal gives exactly the optimal 50:50 distribution, not 32 correct point predictions. Flipping the signal in training reverses all 32 decisions: the correspondence is learned, not supplied by a JavaScript interpreter.

**What an extra label buys.** From input contexts alone, the minimum edge cover selects eight training observations: each covers a (setup, signal) and a (write, index). Eight rather than 32 labels suffice _for this factorization on this dataset_. Twenty fixed random subsets of eight average 16 correct and 16 abstentions. This is offline label efficiency, not 4× measured collection throughput.

**Neural optimization check.** The 32-unit tanh classifier uses the same inputs, trains on full and masked rows, and predicts a softmax over observed joint deltas. Its three primary fits got 25, 28 and 28 of 32 training states right. In the [disclosed exploratory rerun](protocol.md), 10× the updates fit every training state on every seed; the held-out counts became **1, 18 and 25**, with 0, 0 and 2 perfect cells. Training fit is not a transfer test; this small classifier is not a stand-in for a frontier model.

**Raw-frame controls.** At exactly these write pauses, source, filename-blind, syntax, syntax+operands and terminal-readout predictors _all abstained on every trial_. Across all 232 raw transitions the source baseline scored 168 exact (136 nonterminal) and readout scored 32 exact (all terminal). None completed a raw rollout. The new belief model predicts the changed **and unchanged arrays at a supplied breakpoint**, not the next program counter, other guest frames, or a complete program. These scores must not be added.

## Replay

From `cwm/`, with Bun 1.4.4 and Node 24.19.0:

```sh
bun install --frozen-lockfile
bun bench/belief/prepare.ts belief-cache belief-data    # new output directory; raw shards resumable
bun bench/belief/predict.ts belief-data/train.json belief-data/inputs.json > forecasts.json
bun bench/belief/score.ts belief-data/inputs.json forecasts.json belief-data/labels.json > scores.json
```

Only preparation calls the oracle. The prediction command needs neither raw traces nor test labels; its strict Effect input schema rejects extra fields. Ordered input digests bind every forecast bundle and label sidecar to the same batch. Scores include every seed and cell. The fixture is deliberately narrow: two numeric arrays of fixed length, one indexed write, a known history feature, two indices, previously seen primitive spellings and no unrelated side effects. Tested on 64 closed executions, not a random sample of TypeScript. See the [frozen protocol](protocol.md).
