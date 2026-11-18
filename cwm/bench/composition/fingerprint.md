# Identifying a bounded operator with one observation

**Predeclared follow-up to the published scalar experiment.** Freeze its fitted learner, 81-element basis and known structural results. Generate the input from the hypothesis class, not the token or any V8 label. For each of the original tokens and the two bitwise negative controls collect just one training store. Fit as usual. Before collecting an independent check at (14,6), predict its stored value; report all actual/predicted values and remaining candidate counts, whether or not they agree. The check is not part of the single-label fit. This is a test of experimental design under a specified mathematical prior, not a new blind estimate on the six previously published programs.

For a multilinear polynomial in n arguments with integer coefficients bounded in magnitude by K, put B=2K+1 and choose x_j = B^(2^j), starting at j=0. The product for a subset of variables is a different power of B for every subset. Consequently one exact store is a signed-digit encoding of the entire coefficient vector. Two distinct vectors cannot give the same integer: divide their difference by the lowest differing power; the low digit is nonzero with magnitude less than B, and all other terms vanish modulo B. This is a bounded-integer application of [Kronecker substitution](https://arxiv.org/abs/1710.01301), not a claim to identify arbitrary programs.

Refuse a probe when K times the product of (1+x_j) exceeds JavaScript's safe-integer range. Probe magnitude grows very quickly with arity. The experiment uses the existing binary learner; the argument-design function does not depend on arity two. Almost every apparent success here can also be explained by a function outside the class. A second _falsification_ query can reject some such explanations, not prove class membership.

## Result

The generated pair (3,9) gives the coefficient weights (1,3,9,27). V8's five observed stores all select exactly one polynomial, including the two operators outside the class:

| Token | Training store | Predicted at (14,6) | Observed | Candidates after check |
| ----- | -------------: | ------------------: | -------: | ---------------------: |
| `+`   |             12 |                  20 |       20 |                      1 |
| `-`   |             −6 |                   8 |        8 |                      1 |
| `*`   |             27 |                  84 |       84 |                      1 |
| OR    |             11 |                  19 |       14 |                      0 |
| XOR   |             10 |                   7 |        8 |                      0 |

The first three fitted coefficient vectors exactly match the previous 18-label fit; their predictions coincide for every supported expression in that model, not just the published test set. OR selected −1+x+y; XOR selected 1+y. Neither law survived the independent check. This is a controlled reduction in training observations, not a general sample-complexity or inference-speed claim.

From `cwm/` with Bun 1.4.4 and Node 24.19.0: `bun bench/composition/fingerprint.ts collect probe-cache`, then `bun bench/composition/fingerprint.ts score probe-cache`. The score mode loads validated cached observations without guest execution; it uses the installed Node version to locate the versioned cache.
