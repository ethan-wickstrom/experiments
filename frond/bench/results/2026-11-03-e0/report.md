# E0: Pilot: protocol adherence, cache reads, cost, and the screening model

Spec `bench/experiments/e0-pilot.toml` (sha256 74b135a6bd5c), alpha 0.05.
Excluded before the run: cad-model, distributed-dedup, formal-crypto, fp8-rmsnorm-gemm, jax-speedrun-gpu, lake-temp-glm, live-database-cutover, math-eval-grader, medical-claims-processing, payments-pipeline-fix, shadow-relay, vba-userform-port, wdm-design.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| haiku | 10 | 10 | 0.000 (0.000–0.000) | 0.04 | – | 0.92 | 0.00 |
| sonnet | 7 | 7 | 0.143 (0.000–0.429) | 0.91 | 6.40 | 0.90 | 0.14 |
| opus | 7 | 7 | 0.429 (0.143–0.857) | 1.55 | 3.61 | 0.89 | 0.00 |

| Arm | Steps/trial (with branches) | Off protocol | Recovered | Unparsed | Cut off | Syntax errors | Sub-agents |
|---|---|---|---|---|---|---|---|
| haiku | 32.5 | 0.003 | 0.000 | 0.003 | 0.003 | 0.006 | 0.00/trial |
| sonnet | 23.1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.00/trial |
| opus | 20.7 | 0.000 | 0.000 | 0.000 | 0.000 | 0.007 | 0.00/trial |

Never passed in haiku: biped-contact-dynamics, glycan-ms2-elucidation, hof-topology-interpenetration, kv-live-surgery, layout-config-recreation, layout-config-recreation2, mvcc-lsm-compaction, nextjs-performance, ontology-kg-querying, uefi-bootkit.

Incomplete: sonnet has 7 of 10 planned valid trials; 3 tasks are short: biped-contact-dynamics, kv-live-surgery, uefi-bootkit.

Infrastructure failures and misconfigured trials in sonnet, not scored: biped-contact-dynamics (provider failure), kv-live-surgery (provider failure), uefi-bootkit (provider failure).

Never passed in sonnet: glycan-ms2-elucidation, layout-config-recreation, layout-config-recreation2, mvcc-lsm-compaction, nextjs-performance, ontology-kg-querying.

Incomplete: opus has 7 of 10 planned valid trials; 3 tasks are short: biped-contact-dynamics, kv-live-surgery, uefi-bootkit.

Infrastructure failures and misconfigured trials in opus, not scored: biped-contact-dynamics (provider failure), kv-live-surgery (provider failure), uefi-bootkit (provider failure).

Never passed in opus: glycan-ms2-elucidation, layout-config-recreation, mvcc-lsm-compaction, ontology-kg-querying.
