# Checkpoint controls

This addition was requested after the C2 feedback results were available. It is frozen before running either control on the splice projects. Retain the collected C2 arms byte-for-byte. Use the editor at `afc72ae`, evaluator and protocol at `35323bc`, and unchanged fixture from `85d3f22`. Run the following feedback-enabled arms in order on fresh lineage workspaces using the same Bun Docker image, single-slot CPU llama.cpp b6602 server settings, seeds, grammar, eight calls per turn, context limits, and stopping, grading, and selection rules. Servers differ only in port and loaded adapter.

| Arm | Model on Q8 base              | Port |
| --- | ----------------------------- | ---- |
| A   | Released weights alone        | 8097 |
| B2  | Coding adapter from `528437e` | 8099 |

Verified base SHA-256 `0dc7638539067268774c275a14a6ec9c7e01f7eeb2cff606c8590361fa527e4c`, B2 adapter `59ca775a59293b551206d7f7ff500b9b2a403792e617076cdfb62a3900a0096b`, and C2 adapter `55a828fd72c3d1520e8d3668313c0b50dfbad48b99e8729ec251cf9ed44682cb`.

Compare the three feedback-enabled checkpoints on selected cumulative passes, candidate coverage and selection misses. Compare feedback omission only within C2. Initial generation shares decoding settings, with later prompts and reachable workspaces depending on each checkpoint's own proposals and visible test results. Any observed successful edit is mediated by the AST constraints and visible-test search. Four turns from two projects provide limited evidence about checkpoint differences.
