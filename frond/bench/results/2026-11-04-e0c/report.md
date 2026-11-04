# E0c: Effort on the screening model: medium, against E0b's high

Spec `bench/experiments/e0c-effort.toml` (sha256 fd326b7c5177), alpha 0.05.

| Arm | Tasks | Trials | Pass rate (95% CI) | Cost/trial | Cost/solved | Cache share | Failed edits/trial |
|---|---|---|---|---|---|---|---|
| medium | 5 | 10 | 0.500 (0.100–0.900) | 1.35 | 2.69 | 0.86 | 0.00 |

| Arm | Steps/trial (with branches) | Off protocol | Recovered | Unparsed | Cut off | Syntax errors | Sub-agents |
|---|---|---|---|---|---|---|---|
| medium | 21.9 | 0.000 | 0.000 | 0.000 | 0.000 | 0.014 | 0.00/trial |

Incomplete: medium has 10 of 16 planned valid trials; 3 tasks are short: biped-contact-dynamics, glycan-ms2-elucidation, hof-topology-interpenetration.

Infrastructure failures and misconfigured trials in medium, not scored: biped-contact-dynamics (provider failure), glycan-ms2-elucidation (provider failure), hof-topology-interpenetration (provider failure), biped-contact-dynamics (provider failure), glycan-ms2-elucidation (provider failure), hof-topology-interpenetration (provider failure).

Never passed in medium: layout-config-recreation, ontology-kg-querying.
