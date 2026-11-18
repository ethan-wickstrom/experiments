# Can the predictor transfer to a different program?

For a single write traced from TypeScript to raw V8 descriptors, see the [first-write counterexample](first-write/README.md).

For a small controlled test of which actions a site representation distinguishes, see [operators, literals and bindings](actions.md). It does not reuse the source holdout as new evidence.

From `cwm/`, with the project's pinned dependencies installed:

```sh
bun bench/collect.ts ~/cwm-traces 4
bun bench/score.ts ~/cwm-traces > scores.json
```

The [manifest](cases.ts) fixes 32 short single-file programs, each run on the same 32 integer pairs. Of these, 24 programs contribute 24 training pairs and eight test pairs each. The remaining eight programs contribute **only** test runs. This gives 576 training, 192 new-input and 256 new-source traces. Each family has one source template. The small signed grid, shared entrypoint and parameter names make this a controlled diagnostic, not an estimate for arbitrary repositories.

The input holdout selects pairs whose sum is divisible by four; it is not stratified by outcome. In particular, all eight held-out parity calls return true (training has eight true and 16 false). That family's input-holdout score cannot establish generalization to both classes. The new-source split uses the entire grid.

**Collection.** The collector runs at most the requested number of fresh debuggees (default four). The cache key covers program contents, arguments, oracle source, lockfile, runtime versions, architecture and OS. Each completed shard is ordinary one-record trace JSONL, published with a same-directory rename. Run the command again to validate and reuse successes; collection failures are separate diagnostic files and are retried. A corrupt or mismatched shard stops the run rather than silently changing the dataset. Use one collector invocation per cache. Scores require every label and never execute guest code.

**Evaluation.** Count exact, wrong and abstained next observations over every adjacent pair, including module initialization. Report exact **nonterminal** predictions separately: a terminal observation often just copies a value already present in a return frame. A rollout counts only if, starting at the first observed entry-function frame, every self-fed prediction through the terminal matches the oracle. Predictors receive no original entry arguments, future frame, or outcome. Per-family counts are in the score command's JSON, so long programs need not dominate an analysis. For context on why one-step and rollout metrics can diverge, see [Debugging Code World Models](https://arxiv.org/abs/2602.07672).

### Experiment

Bun 1.4.4, Node 24.19.0, Linux x64. Cold four-way collection took 155 seconds (1,023 successes, one SIGABRT). Resuming filled only the missing record, in 0.81 seconds. A full cache validation took 0.29 seconds. These are single-run observations, not timing guarantees.

All models saw identical traces. **Source** is the existing predictor. **Filename-blind** uses a common filename but retains source lines and columns. **Statement** replaces matching V8 sites with Oxc statement/declaration boundaries (node kind, occurrence, first/last character); predictions must map back to a site in the query. Other sites remain file-specific. **Readout** does not train: it copies an exact, observed root entry return into a terminal observation and otherwise abstains.

**Operand** also considers expression, identifier and literal boundaries. It was added **after** scoring the first four models: a positive control showed V8 could stop at the returned operand, not the semicolon. It passes the shifted UTF-16/renamed-file control. Its scores below are exploratory, not an independent holdout.

| Split      | Model          | Exact | Wrong | Abstained | Exact nonterminal | Full rollouts |
| ---------- | -------------- | ----: | ----: | --------: | ----------------: | ------------: |
| New input  | Source         |   641 |     9 |       478 |               455 |        17/192 |
|            | Filename-blind |   642 |     6 |       480 |               456 |        17/192 |
|            | Statement      |   540 |     6 |       582 |               354 |         8/192 |
|            | Readout        |   183 |     0 |       945 |                 0 |         0/192 |
|            | Operand        |   456 |     7 |       665 |               270 |         8/192 |
| New source | Source         |     0 |     0 |     2,428 |                 0 |         0/256 |
|            | Filename-blind |    32 |    24 |     2,372 |                 0 |         0/256 |
|            | Statement      |     0 |    55 |     2,373 |                 0 |         0/256 |
|            | Readout        |   245 |     0 |     2,183 |                 0 |         0/256 |
|            | Operand        |   128 |   243 |     2,057 |                 0 |         0/256 |

**Decision:** keep the production model unchanged. Correctly copying an already-observed value is not evidence that a model inferred how the program produced it. Replacing source identity with syntactic position did not produce even one correct nonterminal prediction on the unseen programs. Further models should beat the readout control on fresh source families, not optimize this now-inspected split.
