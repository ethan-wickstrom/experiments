# E0b: Variance on the screening model: two trials per task

Spec `bench/experiments/e0b-variance.toml` (sha256 c57bc572c32b), alpha 0.05.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| opus | 7 | 13 | 0.357 (0.071–0.714) | 1.73 | 4.51 | 0.85 | 0.00 |

| Arm | Steps/trial (with branches) | Off protocol | Recovered | Unparsed | Cut off | Syntax errors | Sub-agents |
|---|---|---|---|---|---|---|---|
| opus | 19.2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.016 | 0.00/trial |

Incomplete: opus has 13 of 16 planned valid trials; 2 tasks are short: biped-contact-dynamics, glycan-ms2-elucidation.

Infrastructure failures and misconfigured trials in opus, not scored: biped-contact-dynamics (provider failure), biped-contact-dynamics (provider failure), glycan-ms2-elucidation (provider failure).

Never passed in opus: glycan-ms2-elucidation, layout-config-recreation, layout-config-recreation2, ontology-kg-querying.
