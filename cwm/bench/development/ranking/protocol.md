# Frozen experiment

Use only the ten frozen C2 training families. Build 30 matched reversal blocks from the observed Bun exits. Each block has the same two complete candidate files tested twice, with opposing goals and visible checks. Each requirement supplies two candidates and exactly one passes. Keep both forks and every turn from a family together when holding it out. Score preferences and both-forks-correct counts. Make no selection on the separate reversal or project suites.

Compare the original cached forecast margin and final hidden state with current-state-only, single-user candidate-last and candidate-first prompts. The archived history prompt has extra observed history, so evaluate an order-only ablation at equal information as well. Candidate-first permits a causal language model to predict the visible requirement and check text after reading the proposed file. Measure token log likelihood over those spans. Also present both alternatives to a forced-choice critic in both orders, correcting answer-position bias by antisymmetrization.

Fit a regularized pairwise logistic head to within-request score differences. Include a second logistic term for the average signed difference across both forks, encouraging conditional reversals. Use full-batch deterministic optimization, equal mass per family, fixed regularization 0.1, no search. The released head combines the candidate-first final state, mean contextual goal state, goal and visible check likelihoods, first-token pass/fail margin, and order-corrected two-candidate margin. Report all ablations without choosing a winner after scoring. Candidate bytes, visible tests, original files and current request are available at inference. Past or candidate test outcomes, family IDs, fork IDs and future source are excluded.

Score leave-one-family-out heads for three frozen encoders: unchanged A, policy-only B2, and joint C2. A has no experiment-specific backbone training. The released B2 and C2 backbones previously saw all ten families, including their passing source. Their fold results measure readout transfer conditional on these backbones. The independently held external suite is needed to establish full-system generalization. Refit each released head on the 30 blocks once the fold protocol is fixed. C2's original generator and weights supply complete candidate writes unchanged.

Persistent CPU command from repo root:

```sh
CWM_MODEL_PATH=/path/to/release python cwm/bench/development/ranking/rank.py --serve --arm C2
```

Each UTF-8 NDJSON request contains `goal`, `path`, a `files` array of visible `{path,text}` objects, and a `candidates` array of exactly two `{op:"write",path,text}` actions for the host-selected path. Responses have `scores` in submitted order and zero-based `choice`, or null on a tie. The same interface serves A and B2. This call reads observations supplied by the caller and executes no submitted code.
