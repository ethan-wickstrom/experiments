# E0a: Which TB 4.0 tasks can pass at all in this VM

Spec `bench/experiments/e0a-oracle.toml` (sha256 6970c8f4ca19), alpha 0.05.
Excluded before the run: distributed-dedup, formal-crypto, fp8-rmsnorm-gemm, jax-speedrun-gpu, lake-temp-glm, live-database-cutover, math-eval-grader, payments-pipeline-fix, shadow-relay, wdm-design.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| oracle | 55 | 55 | 0.945 (0.873–1.000) | – | – | – | – |

Infrastructure failures in oracle, not scored: medical-claims-processing (RuntimeError).

Never passed in oracle: cad-model, rs-archive-clone, vba-userform-port.
