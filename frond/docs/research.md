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
| H1 | Code actions in a persistent REPL solve at least as many tasks as JSON tool calling with identical tools, at lower cost | `--arm rlm` (40 steps) vs `--arm react` (100 steps; one call each) | TB 4.0 | pass rate (non-inferiority, 5 points); cost per solved task |
| H2 | Forking k=3 branches at the model's request and keeping the one verifiers prefer raises pass rate. Prefix caching keeps cost under 2× | `--fork 1` vs `--fork 3` | TB 4.0 | pass rate (superiority); cost ratio |
| H3 | Marking stale observations, meaning files changed since the model read them, cuts failed edits and wrong-state actions | `--freshness off` vs `on` | TB 4.0 | failed edits and stale actions per task; pass rate |
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
- stale actions: edits, writes and deletes of files changed since the model last read them (`stale_actions`; both freshness arms count them);
- forks: each FORK's branches with their steps, check result and which was kept (`metrics.json`), and each branch's model calls, tagged with the branch in `calls.jsonl`, so fork overhead is priced separately.

## Statistics

Every experiment is a spec in `bench/experiments/`, committed before its first trial: tasks, run order, arms, trials and claims, each claim with its test and margin. `bench/matrix.py` runs it and `bench/analyze.py` evaluates it from the same file (D28).

Pre-registered specs (2026-11-03): `e0-pilot`, `e1-action-space` (H1), `e2-fork` (H2), `e3-freshness` (H3), `e4-context` (H4), `e5-scopes` (H5), `e6-layout` (H6) and `e11-references` (Claude Code, Terminus 2 and Harbor's stock `dspy-rlm` on Opus 5.5). E1-E5 name Sonnet 5.5 provisionally: E0 picks the screening model by the rule below, and a change is recorded in `decisions.md` before their first trial. E4 and E5 run on a 20-task sample of Long-Horizon TB 2.0 with 150 steps per arm, since those tasks need far more than TB's 40 and the context mechanisms act only once a turn outgrows the budget.

- The population is the TB 4.0 tasks that can start in the VM: 56 of 66, since 10 declare more than 4 CPUs or a GPU (`bench/datasets/`, G20). Tasks the oracle fails in E0a are excluded too.
- The task is the pairing unit. Each arm runs k trials per task, giving a per-task pass fraction. Only the first k valid trials of a task count, in start order. Trials whose environment failed before the agent started are reported and not scored.
- Fixed-size test: the exact paired Wilcoxon signed-rank test on per-task differences (as in [AgentRewind](https://arxiv.org/abs/2608.14380)), one-sided against the claim's boundary, computed over all sign assignments so ties need no approximation. Effect sizes get bootstrap 95% intervals over tasks. Holm's correction applies across a spec's claims; a claim holds when its adjusted p is below 0.05.
- Non-inferiority margin: 5 points. Cost claims compare total cost between arms: the ratio of totals is below the bound b exactly when the mean over tasks of treated − b × control is below 0, which a one-sided studentized bootstrap tests (D41). The ratio's percentile interval describes it.
- Sequential decisions: after every batch, each pass-rate claim's betting confidence sequence ([Waudby-Smith and Ramdas](https://arxiv.org/abs/2010.09686)) is read. It holds at all looks at once, so stopping as soon as a claim is decided keeps the error below alpha. A fixed-size test read after every batch would not. Specs opt in with `stop_early = true`, and then every claim is decided by a rule valid at the stop (D41): a pass-rate claim by its sequence, any other claim by its fixed-size p-value times the planned looks times the claims; the sequences use alpha split across the claims.
- Validity: a trial whose recorded configuration contradicts its arm is not scored (D41). A jobs directory holds one version of its spec and of frond's source, and every trial installs the dependency versions in `uv.lock` (D42).
- Batches alternate the order of arms (ABBA), so drift in the API or the VM falls on every arm alike.
- Sample size comes from E0's within-task and between-task variance, which the analysis reports. Before E0, the estimate at 56 tasks × 3 trials is a 95% half-width of about 5 points on a paired difference.

## Cost model and screening

List prices per million tokens (D24):

| Model | Input | Output | Cache read | Cache write (5 min) |
|---|---|---|---|---|
| Opus 5.5 | $4 | $20 | $0.20 | $5 |
| Sonnet 5.5 | $2 | $10 | $0.20 | $2.50 |
| Haiku 5.5 | $0.10 | $0.50 | about $0.01 | about $0.13 |

An estimated TB 4.0 run takes 25 steps. Each step reads about 30k cached tokens, writes about 1.5k and outputs about 2k. That is about $1.50 per run on Opus 5.5, $0.80 on Sonnet 5.5 and under $0.05 on Haiku 5.5. E0 replaces these estimates with measurements.

Screening protocol: run each hypothesis first on the cheapest model whose TB 4.0 pass rate sits between 20% and 80%, where differences are visible. Confirm the winners on Opus 5.5. E0 measures pass rates for all three models on a 10-task subset to choose the screening model.

## Running

From `frond/`, like the checks:

```sh
scripts/dev-env.sh                                              # dockerd, the mirror (D23), the egress CA (D27)
export FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt
uv run python -m bench.matrix bench/experiments/<spec>.toml --dry-run   # each Harbor job and its command
uv run python -m bench.matrix bench/experiments/<spec>.toml             # runs, resumes, prunes images (G8)
uv run python -m bench.analyze bench/experiments/<spec>.toml --out bench/results/<date>-<id>
```

Before a paid run, `bench/experiments/smoke.toml` with `ANTHROPIC_API_KEY=<anything>` checks the whole pipeline at no cost: the first model call fails with 401, after frond has installed, parsed every arm flag, and written its export.

The runner adds the egress-CA overlay, without which every task whose agent, solution or tests reach the internet fails in this VM (G7). It retries only failures before the agent starts, because Harbor reruns a retried trial under the same name and would otherwise keep the better of two attempts. Jobs go to `jobs/<id>/` (ignored by git).

Results, as summaries rather than raw trajectories, go under `frond/bench/results/<date>-<experiment>/`. frond redacts credential values, key-shaped strings and URL passwords from its exports and headless output before they reach Harbor (ledger B12).
