# Research program

frond is a research vehicle. Its question: which harness mechanisms make a coding agent solve more terminal tasks per dollar, on the same model? It tests RLM-style code actions over a persistent REPL against conventional tool calling. Within the RLM, it tests the mechanisms frond adds: worlds, forking with verifier selection, freshness tracking, lossless folding, scopes and the cache layout. Each mechanism is an arm, and each hypothesis has a pre-registered comparison. The ledger tracks status; this file is the protocol.

## Benchmarks (D20)

| Set | Harbor id | Tasks | Use |
|---|---|---|---|
| Terminal-Bench 4.0.0 | `terminal-bench/terminal-bench@4.0.0` | 66 | primary; H1–H3, H6 |
| Long-horizon TB 2.0 | `silrlab/long-horizon-terminal-bench-2.0` | 77 | context mechanisms; H4, H5 |

The pipeline is verified locally. Harbor's oracle agent solved `layout-config-recreation2` from TB 4.0.0 in Docker in this VM, scoring 1.0 in 1m43s on 2026-11-03.

## Hypotheses and arms

Each hypothesis compares arms on the same tasks, model, effort and budget.

| ID | Hypothesis | Arms (flag) | Set | Primary metric |
|---|---|---|---|---|
| H1 | Code actions in a persistent REPL solve at least as many tasks as JSON tool calling with identical tools, at lower cost | `--arm rlm` vs `--arm react` | TB 4.0 | pass rate (non-inferiority, 5 points); cost per solved task |
| H2 | Forking k=3 branches at the model's request and keeping the one verifiers prefer raises pass rate. Prefix caching keeps cost under 2× | `--fork 1` vs `--fork 3` | TB 4.0 | pass rate (superiority); cost ratio |
| H3 | Marking stale observations, meaning files changed since the model read them, cuts failed edits and wrong-state actions | `--freshness off` vs `on` | TB 4.0 | failed edits per task; pass rate |
| H4 | A lossless log with index folds beats LLM summary compaction on long tasks | `--context fold` vs `--context summary` | LHTB 2.0 | pass rate |
| H5 | Scopes as savepoints, collapsing finished subtasks and rewinding abandoned ones, raise long-horizon pass rate and cut cost | `--scopes off` vs `on` | LHTB 2.0 | pass rate; cost |
| H6 | The per-step cache layout cuts cost at least 3× on Anthropic without lowering pass rate | `--layout chat` vs `--layout frond` | TB 4.0 subset | cost per task; pass rate (non-inferiority) |

External references (D21) are Claude Code and Terminus 2 on the same model, run through Harbor's built-in agents. Leaderboard values on Opus 5.5 are about 65% ([Vals AI](https://www.vals.ai/benchmarks/terminal-bench-4)).

## Measurements per run

Each run records, in `frond -p --export` and on to Harbor:
- pass, the verifier's reward;
- tokens per model call: input, cache read, cache write and output, as the provider reports them (`cache_read_input_tokens` on Anthropic);
- cost at list prices;
- steps and wall-clock time;
- protocol violations: replies that failed to parse into reasoning and code;
- failed edits: edit or patch calls that raised;
- stale actions: edits to files changed since they were last read;
- forks and the verifier scores of each branch.

## Statistics

- The task is the pairing unit. Each arm runs k trials per task, giving a per-task pass fraction.
- The comparison is the paired Wilcoxon signed-rank test on per-task differences, as in [AgentRewind](https://arxiv.org/abs/2608.14380), with bootstrap 95% intervals on the mean difference. Holm correction applies across H1–H6.
- Non-inferiority margin: 5 points. Superiority means the interval excludes 0.
- Sample size comes from P0's per-task variance. Before P0, the estimate at 66 tasks × 3 trials is a 95% half-width of about 5 points on a paired difference.
- Runs go in batches of 22 tasks, so the program can stop early on clear success or futility, at the cost of the error control a single fixed-size test would give.

## Cost model and screening

List prices per million tokens (D24):

| Model | Input | Output | Cache read | Cache write (5 min) |
|---|---|---|---|---|
| Opus 5.5 | $4 | $20 | $0.20 | $5 |
| Sonnet 5.5 | $2 | $10 | $0.20 | $2.50 |
| Haiku 5.5 | $0.10 | $0.50 | about $0.01 | about $0.13 |

An estimated TB 4.0 run takes 25 steps. Each step reads about 30k cached tokens, writes about 1.5k and outputs about 2k. That is about $1.50 per run on Opus 5.5, $0.80 on Sonnet 5.5 and under $0.05 on Haiku 5.5. P0 replaces these estimates with measurements.

Screening protocol: run each hypothesis first on the cheapest model whose TB 4.0 pass rate sits between 20% and 80%, where differences are visible. Confirm the winners on Opus 5.5. P0 measures pass rates for all three models on a 10-task subset to choose the screening model.

## Running

```sh
frond/scripts/dev-env.sh                    # dockerd + the Docker Hub mirror (D23)
cd frond && PYTHONPATH=bench uvx --from harbor harbor run -d terminal-bench/terminal-bench@4.0.0 \
  -a frond_harbor:Frond -m anthropic/claude-opus-5-5 -e docker -n 1 -k 3 -o jobs
```

Results, as summaries rather than raw trajectories, go under `frond/bench/results/<date>-<experiment>/`, with secrets redacted (ledger B12).
