# Frozen before collection or scoring

Train on the three one-operation sources and six ordered input pairs in
`cases.ts`. Test each of the six other bodies on all four disjoint pairs;
no held-out body or label participates in fitting. Score the untrained-token
body separately as a negative control. The last two compositions have
opposite first stores and equal final results on every test input. Check
each pair jointly; a learned return shortcut must not get credit.

Target: prediction at **semantic boundaries** in straight-line safe-integer
code. Start at the first function frame with observed parameters. Each
declaration adds one observable local and advances the statement index.
Use the first observed store at the subsequent statement, and the oracle
outcome at return. No labels for expression microsteps. A nonterminal hit
requires the exact whole store *and* next index after a declaration; count
wrong and abstained too. A complete rollout must self-feed from entry
through every store and final value without an oracle restart. Report raw
V8 adjacent frames as a separate, unsupported target, not implied hits.

Primary candidate: learn a per-token relation in a fixed small bilinear
integer basis using only observed atomic transitions. Use it recursively
on the held-out syntax tree with no built-in operator dispatch. If no
evidence fits, candidates disagree at query, or an intermediate is outside
the supported numeric domain, abstain. Control 1: same learned rules but
only use them for a whole expression shape seen in training (including
operand roles). Control 2: cyclically permute the three fitted token
tables at prediction. All models share binding, copying and straight-line
control; those are supplied, not learned.

No source execution, runtime debugger, oracle helper, oracle arguments,
successor site list or expected outcome in the predictor. Keep collection
and offline scoring separate. Do not change the split after seeing scores.
