# Preregistered regime stress test

Freeze the scalar learner at 9f5da21. Use the arrays and blinding dictionary in `regime-stress.ts` unchanged: all four training pairs have disjoint set bits, all seven test pairs have overlapping bits, and the five acquisition-pool pairs are disjoint from both sets as input pairs. Collect `const m = x OP y; return m;` on V8. Labels are the observed scalar bound to `m`, not the final outcome. Only the oracle adapter sees the original token; pass an opaque key and two scalar operands to predictors.

**Protocol fixed before labels.** Compare the frozen learner's polynomial version space to that version space plus exactly three shared functions (bitwise AND, OR, XOR). No key gets a preferred function. Retain only candidates matching all labels for that key. Predict only on unanimous output; empty or divided committees abstain. Use the enlarged survivors after the initial training set for acquisition. Among the unlabeled pool, maximize the number of unordered candidate pairs predicting different outputs. Break ties by first pool index. Choose and persist both queries before acquiring either label; then collect only the two selected labels, fit again, and collect separate held-out labels for scoring. Both learners receive the same acquired label for each key. Never inspect test inputs or outputs in acquisition.

For each key report candidate survivors, chosen input and disagreement, and exact/wrong/abstained first-store predictions on the untouched test set before/after acquisition. This tests prediction of one atomic scalar store, not raw-frame or composition accuracy. A unanimous wrong answer falsifies any claim of identifiability beyond the chosen hypothesis class.

## Result

[Split and rule frozen](https://github.com/ethan-wickstrom/experiments/commit/8d5ad90913cc8e69b88553f557600062a2a46429); [implementation frozen](https://github.com/ethan-wickstrom/experiments/commit/f46176de1746f9455ef48628da28c3985fa3a5ab) before collection. Each key independently retained one polynomial (addition); the shared extra candidates retained OR and XOR but not AND. The disagreement scores in pool order were `[0,3,0,3,3]` for both keys. The first maximum, `(3,5)`, separated the three votes: addition = 8, OR = 7, XOR = 6. Only then did V8 provide the selected labels.

| Key | Acquired store | Original before → after | Enlarged before → after | Sole enlarged survivor |
| --- | -------------: | ----------------------- | ----------------------- | ---------------------- |
| k17 |              6 | 0/7/0 → 0/0/7           | 0/0/7 → 7/0/0           | XOR                    |
| k42 |              7 | 0/7/0 → 0/0/7           | 0/0/7 → 7/0/0           | OR                     |

Cells are **exact / wrong / abstained** held-out stores. Before acquisition every polynomial prediction was unanimous and wrong; afterward neither token had a consistent polynomial. The extra prior changed wrong answers into abstentions, and one distinguishing label resolved those abstentions. This does not establish that the expanded library contains the true law on other regimes, or that active selection beats random: three of the five pool pairs tied for maximum disagreement.

From `cwm/` with Bun 1.4.4 and Node 24.19.0 on PATH:

```sh
bun bench/composition/regime-stress.ts collect fresh-regime-dir
bun bench/composition/regime-stress.ts score fresh-regime-dir
```

Collection persists the chosen queries before asking V8 for either label. Offline scoring needs no Node executable; it rebuilds the choice from the eight training traces and checks it against the receipt. Both models' predictions are fixed before loading the 14 held-out labels. Report SHA-256 (stdout including newline): `29964dfc78e8ea8bda6d47799dbcfa065c61819d53299799df1168e23ec573ff`.
