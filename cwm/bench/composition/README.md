# Can atomic stores predict unseen expression trees?

**Yes on these six straight-line integer programs, at statement boundaries.** Fitting three token relations from 18 V8-observed stores sufficed for all 24 self-fed rollouts. Matching entire expression trees did not complete one. This experiment does not predict V8 frames or establish general JavaScript arithmetic.

## Frozen test

[Commit e9bfb7b](https://github.com/ethan-wickstrom/experiments/commit/e9bfb7bc96b45215f00918d9c3ec612f7782d969) fixed the sources, input pairs, controls and [protocol](protocol.md) before scoring. [Commit caf3edb](https://github.com/ethan-wickstrom/experiments/commit/caf3edb9df47ecb5a1c9632ab30fdc8c344a362a) froze the predictor and scorer before the first held-out collection. Training has six pairs per token; the test has four disjoint pairs for each new program. The file contains 18 training, 24 composition and four untrained-token runs. Splits are by whole source, not frames.

| Fresh program                       | Exact stores / possible | Exact rollouts / runs |
| ----------------------------------- | ----------------------: | --------------------: |
| Right-nested, depth 2               |                     4/4 |                   4/4 |
| Balanced, depth 2                   |                     4/4 |                   4/4 |
| Left-nested, depth 4 with literals  |                     4/4 |                   4/4 |
| Three statements with reused locals |                     8/8 |                   4/4 |
| Forward subtraction then square     |                     8/8 |                   4/4 |
| Reversed subtraction then square    |                     8/8 |                   4/4 |

| Model                                           | Exact / wrong / abstained nonterminal stores | Full semantic rollouts | Both first stores and rollouts in equal-return pair |
| ----------------------------------------------- | -------------------------------------------: | ---------------------: | --------------------------------------------------: |
| Recursive learned relation                      |                                   36 / 0 / 0 |                  24/24 |                                                 4/4 |
| Whole expression must have appeared in training |                                   8 / 0 / 28 |                   0/24 |                                                 0/4 |
| Fitted token tables cyclically permuted         |                                   0 / 36 / 0 |                   0/24 |                                                 0/4 |

For input `(-7,3)`, the contrast programs bind `p` to −10 and 10, then both return 100. The whole-expression control can predict the familiar `x-y` store from new operands, but not the unseen `p*p` expression. All models abstained at the first store of all four untrained remainder programs; these negatives are outside the fresh-program denominators.

## What was learned

Like [Synantic](https://doi.org/10.1145/3689724), fit a reusable rule per syntax constructor rather than one rule per entire program. Here the finite prior is 81 integer polynomials `a + bx + cy + dxy` with coefficients in `{-1,0,1}`. All binary tokens start without a rule. For each observed atomic store, keep only polynomials giving the observed value from the two observed operands. The sole survivors in coefficient order were `+`: (0,1,1,0), `-`: (0,1,−1,0), `*`: (0,0,0,1). These are **results**, not dispatch entries. An automated test relabels `+` to mean subtraction and checks a nested prediction changes accordingly.

At query time the parser provides lexical slots and ordered expression children. The model recursively combines operands using only retained rules; BigInt keeps the polynomial calculation exact. No examples, an empty version space, conflicting candidate values, or unsafe/noninteger intermediates mean abstention. Binary applications to a zero operand are conservatively unsupported because the integer algebra lacks signed zero. Uncertainty is **relative to the chosen basis**: an unmodeled coercion or piecewise rule can agree with all six examples. Slot lookup, literal copying, appending a new binding, statement order and returning are supplied scaffolding, not learned semantics.

## What was scored

`project.ts` selects the first mapped function pause on each statement line by location, not by result. Every live binding must be an exact observed scalar. An as-yet-unbound local is not a zero. A nonterminal is correct only if the entire visible store and next statement index match. The initial store comes from the observed entry frame, not from the oracle's arguments field. One-step store counts are teacher-forced; a rollout gets credit only if all self-fed predictions through the returned value are exact. Fitting reads the store of the next statement, not the return payload.

There are **88 raw adjacent transitions** across the fresh traces, including module initialization and final outcomes. No model emits raw event kind, stack, columns or unavailable-scope snapshots: **zero raw predictions**, not 24 successful raw rollouts. This is a different target from the [raw first-write witness](../first-write/README.md).

## Replay

From `cwm/` with the frozen dependencies installed:

```sh
bun bench/composition/score.ts bench/composition/traces.jsonl
bun test bench/composition
```

The first command is entirely offline. No oracle helper is called; scoring also reproduced with no Node executable on PATH. To independently regenerate the checked-in observations (Bun 1.4.4, Node 24.19.0):

```sh
bun bench/composition/collect.ts fresh-composition.jsonl
cmp fresh-composition.jsonl bench/composition/traces.jsonl
```

The collector refuses an existing output. Two independent collections produced identical JSONL (SHA-256 `f45387aedd6aa6b02e6f4df87c19c3a62df2681fa662b73299ab149c9727ad2b`). The scorer validates all records against the ordered manifest and reports fitted coefficients, per-shape counts, controls and contrasts.

**Limit.** One synchronous function, one statement per line, simple parameters, fresh `const` bindings and a final return. No effects, aliasing, branches, exceptions, strings, overflow or floating-point semantics. The grammar was chosen to contain the training operations. In the [frozen off-regime falsification](regime.md), all 14 confident polynomial predictions were wrong. Enlarging the shared hypothesis class and acquiring one distinguishing observation per token recovered the held-out stores.
