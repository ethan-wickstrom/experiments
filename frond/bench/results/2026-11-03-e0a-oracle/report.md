# E0a: Which TB 4.0 tasks can pass at all in this VM

Spec `bench/experiments/e0a-oracle.toml` (sha256 6970c8f4ca19), alpha 0.05.
Excluded before the run: distributed-dedup, formal-crypto, fp8-rmsnorm-gemm, jax-speedrun-gpu, lake-temp-glm, live-database-cutover, math-eval-grader, payments-pipeline-fix, shadow-relay, wdm-design.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| oracle | 55 | 55 | 0.964 (0.909–1.000) | – | – | – | – |

Incomplete: oracle has 55 of 56 planned valid trials; 1 tasks are short: medical-claims-processing.

Infrastructure failures and misconfigured trials in oracle, not scored: medical-claims-processing (RuntimeError).

Never passed in oracle: cad-model, vba-userform-port.
