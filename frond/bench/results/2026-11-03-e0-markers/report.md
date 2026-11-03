# E0: Pilot: protocol adherence, cache reads, cost, and the screening model

Spec `bench/experiments/e0-pilot.toml at f10dd98, before D53 (the field markers)` (sha256 a8313cd4ee9d), alpha 0.05.
Excluded before the run: cad-model, distributed-dedup, formal-crypto, fp8-rmsnorm-gemm, jax-speedrun-gpu, lake-temp-glm, live-database-cutover, math-eval-grader, medical-claims-processing, payments-pipeline-fix, shadow-relay, vba-userform-port, wdm-design.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| haiku | 10 | 10 | 0.000 (0.000–0.000) | 0.06 | – | 0.87 | 0.00 |
| sonnet | 8 | 8 | 0.125 (0.000–0.375) | 1.08 | 8.61 | 0.89 | 0.00 |
| opus | 0 | 0 | – | – | – | – | – |

| Arm | Steps/trial (with branches) | Off protocol | Recovered | Unparsed | Cut off | Syntax errors | Sub-agents |
|---|---|---|---|---|---|---|---|
| haiku | 25.6 | 0.293 | 0.211 | 0.082 | 0.027 | 0.004 | 0.00/trial |
| sonnet | 26.4 | 0.318 | 0.213 | 0.104 | 0.005 | 0.009 | 0.00/trial |

Never passed in haiku: biped-contact-dynamics, glycan-ms2-elucidation, hof-topology-interpenetration, kv-live-surgery, layout-config-recreation, layout-config-recreation2, mvcc-lsm-compaction, nextjs-performance, ontology-kg-querying, uefi-bootkit.

Incomplete: sonnet has 8 of 10 planned valid trials; 2 tasks are short: biped-contact-dynamics, kv-live-surgery.

Infrastructure failures and misconfigured trials in sonnet, not scored: biped-contact-dynamics (provider failure), kv-live-surgery (provider failure).

Never passed in sonnet: glycan-ms2-elucidation, layout-config-recreation, layout-config-recreation2, mvcc-lsm-compaction, nextjs-performance, ontology-kg-querying, uefi-bootkit.

Incomplete: opus has 0 of 10 planned valid trials; 10 tasks are short: biped-contact-dynamics, glycan-ms2-elucidation, hof-topology-interpenetration, kv-live-surgery, layout-config-recreation, layout-config-recreation2, mvcc-lsm-compaction, nextjs-performance, ontology-kg-querying, uefi-bootkit.
