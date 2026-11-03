# Ledger

The single list of everything open in frond, and of everything closed, which is marked rather than deleted. It replaces `open-items.md` (2026-11-03); IDs carried over from that file keep their meaning.

Rules:
- Add an entry whenever something is deferred, a gap is found, or an idea comes up. Change an entry in the same commit as the change that affects it.
- Close an entry with its resolution: a commit hash, a PR, a document section or a decision (`decisions.md`).
- A commit cannot name its own hash. Write "(this commit)", and let the next commit that touches this file put the hash in.

Statuses:
- next: in the current work order (see `now.md`);
- open: not scheduled yet;
- blocked: waiting on another entry;
- deferred: postponed, with the reason;
- closed: done, with its resolution.

The ID prefix gives the kind:

| Prefix | Kind |
|---|---|
| REQ | request to the owner |
| E | experiment |
| B | build |
| N | rename |
| U, Q | question |
| V | unverified claim |
| R | requirement (`design.md`) |
| G | gap |
| A | assumption |
| K | calibration |
| P, I | entries carried over from `open-items.md` |
| PR | pull request |

Hypotheses H1–H6 are defined in `research.md`.

## Requests to the owner

Only what the agent cannot get itself (D16).

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| REQ-1 | An Anthropic API key in this cloud environment, with a $100 spend cap for now | the key is visible to a session, and frond completes one TB 4.0 task | closed: PR #27 | the owner added it to the environment's variables as `CLAUDE_API_KEY`; environment changes reach new sessions only, so the session after 2026-11-03's first sees it. Never print it: check it with `${#CLAUDE_API_KEY}`. The runner hands it to Harbor as `ANTHROPIC_API_KEY` (`matrix.with_aliases`), and `bench/budget.toml` holds the $100 cap (D43). Closes when the smoke run completes a task. 2026-11-03, second session: `GET /v1/models` returned 200 from the VM and from a task container; the second paid smoke completed a TB 4.0 task (`layout-config-recreation2`, 3 steps, status done, $0.70), and the key's value appears in no file under `jobs/` |
| REQ-2 | Docker or Daytona for benchmark runs | Harbor runs a TB 4.0 task | closed: not needed | `dockerd` runs in the VM (D23); oracle run passed 2026-11-03 |
| REQ-3 | Devin's security findings that Devin did not post: three on PR #2, three on #11, one on #12, one on #23 | each copied here, then fixed or declined | open, low priority | needs the owner's Devin account (was I3); the review pages are `app.devin.ai/review/ethan-wickstrom/experiments/pull/<n>` |

## Experiments

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| E0 | Pilot (was P0): 10 TB 4.0 tasks × 1 trial on each of Haiku 5.5, Sonnet 5.5 and Opus 5.5, cheapest first, to pick the screening model and measure cost and protocol adherence | report in `bench/results/` with per-call cache reads, protocol violations (D46), failed edits, cost per trial and pass rate per model | next: runs from PR #27's merge | spec `bench/experiments/e0-pilot.toml`; restructured before its first trial (D48): the Opus arm had 3 trials per task, which at a measured $5 per trial would have taken the whole grant. It runs #27's merge, so sub-agents' protocol counts are missing from it (F51) |
| E0a | Oracle sweep: Harbor's reference solutions on all 66 TB 4.0 tasks in this VM, so that infrastructure failures (TLS, resources, disk) are known before any model is blamed | pass list in `bench/results/` | closed 7b3fb7e | 53 of the 55 tasks that start pass under Harbor's reference solutions (0.964); `cad-model` (broken image) and `vba-userform-port` (G23) fail, and `medical-claims-processing` cannot start (G25). These three are the final exclusion list, `bench/results/2026-11-03-e0a-oracle/oracle-failures.txt`, with the report beside it. The four runs found G7, G8, G20, G23, G25 and G26; the third run's report (void, umask 0) is in `first-sweep-umask0/`. With 53 tasks, E1–E3's batch size went from 13 to 14 before any trial, so they keep four looks (D44) |
| E0b | Variance: 2 more trials per task on E0's 10 tasks with the screening model E0 picks, for the within- and between-task variance that sizes E1–E6 | the analysis's variance report, and sample sizes in `research.md` | blocked: E0, and the budget left after it | D48; a spec is committed once E0 has named the model, before its first trial |
| E1 | H1: RLM against ReAct, same tools | paired test per `research.md` | blocked: E0 | `research.md`; arms `--arm rlm` (40 steps) and `--arm react` (100 steps), D33; spec `bench/experiments/e1-action-space.toml` |
| E2 | H2: fork k=3 with verifier selection | paired test; cost ratio | blocked: E0 | `research.md`; arms `--fork 1` and `--fork 3` (B7); spec `bench/experiments/e2-fork.toml` |
| E3 | H3: freshness marks | failed edits and stale actions per task, pass rate | blocked: E0 | `research.md`; the arms are `--freshness on` and `off` (B5); spec `bench/experiments/e3-freshness.toml` |
| E4 | H4: fold against summary on LHTB 2.0 | paired test | blocked: E0 | `research.md`; arms `--context fold` and `--context summary` (B10); spec `bench/experiments/e4-context.toml` |
| E5 | H5: scopes as savepoints on LHTB 2.0 | paired test; tests A1–A4 and A10 | blocked: E0 | `research.md`; arms `--scopes off` and `--scopes on` (B9); spec `bench/experiments/e5-scopes.toml` |
| E6 | H6: cache layout | cost and pass rate; tests A9 | blocked: E0 | `research.md`; spec `bench/experiments/e6-layout.toml` |
| E7 | Offline prompt optimization (GEPA) with a regression gate (was I11) | gains hold on held-out tasks (A11) | blocked: E1–E6 infrastructure; a reward that does not reward shortcuts | [2607.14004](https://arxiv.org/abs/2607.14004) |
| E8 | `plan()` ablation (was I10) | pass rate with and without `plan()` | blocked: E0 | Amp [dropped its TODO tool](https://ampcode.com/news/todos-are-done) |
| E9 | Sub-model choice: Haiku 5.5 against the main model for `llm_query` | pass rate and cost | blocked: E0 | D24 |
| E10 | Effort sweep: medium, high, xhigh | pass rate and cost per solved task | blocked: E0 | D24 |
| E11 | External references: Claude Code and Terminus 2 on Opus 5.5 | pass rate and cost on TB 4.0 | blocked: G33 | D21; spec `e11-references.toml`, which adds Harbor's stock `dspy-rlm` agent: frond's mechanisms against the same paradigm without them. Smoke-tested 2026-11-03 with a dummy key: all four arms install, run and reach the API (401) |
| E12 | Native tool-call rendering of past steps, for provenance | pass rate, plus an injection test set (A13) | blocked: E0 | D14 |

## Build

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| B1 | Claude 5.5 compatibility and effort: send no sampling parameters, set `output_config.effort` from `--effort` (default high) | a payload test on `claude-opus-5-5` shows no temperature, no disabled thinking, and the chosen effort | closed 2605fb3 | `build_lm(effort=…)`, `tests/test_lm.py`; D26 |
| B2 | Measurement: per-call input, cache read, cache write and output tokens; protocol violations; failed edits; stale actions | `--export` writes them; tests cover each counter | closed 63d52f8 | `--export` now also writes `calls.jsonl` (raw and normalized usage per model call) and `metrics.json` (parse failures, code that did not compile, tool calls and failures, failed edits); `tests/test_metrics.py`. Stale actions move to B5, which defines staleness |
| B3 | Arms and runner: arm flags passed through Harbor options; `bench/matrix.py` (tasks × arms × trials, resumable); `bench/analyze.py` (Wilcoxon, bootstrap, Holm, cost per solved) | a dry run of the matrix, and analysis on synthetic results | closed (this commit) | D28. Pre-registered TOML specs (`bench/experiments/`); ABBA batches; resume; retries only before the agent starts; first k valid trials; per-call pricing (`bench/prices.toml`); exact Wilcoxon, bootstrap, Holm, and betting confidence sequences for early stopping; `tests/test_bench.py`. Flags: `--layout` (H6) now; each later arm's flag comes with its build item (B5, B7, B8, B9, B10). E0a ran through it |
| B4a | Worlds core: a content-addressed store with nested Merkle trees, incremental snapshots (stat cache, racy-edit rehash), checkout, diff, line-level merge3, and revert | `tests/test_world.py`: exact round trips (modes, links, type changes, empty directories), excluded caches untouched, racy edits seen, and a later edit by someone else surviving a revert | closed 72818da | `src/frond/world/`; D22 |
| B4b | Wire worlds into frond: a snapshot around each action, undo as a revert of the turn's steps, a net turn diff, non-git workspaces; delete `Checkpoints` and `GitSnapshots` | the undo tests (`test_command_undo`, `UndoFidelity`) pass on worlds, plus a concurrent-edit test through `/undo` | closed (this commit) | D29. `world/timeline.py`: a world at turn start and after every step (each step-log record names its world); `/undo` reverts the latest changed turn by three-way merge; `/diff` and `Agent.turn_diff` show a turn's net change; per-command diffs come from worlds too, in any directory. The tools keep no journal; `checkpoints.py` and `snapshots.py` are deleted |
| B5 | Freshness: observations carry content hashes, and the prompt marks stale ones | a test where a file changes after a read and the next prompt marks it | closed (this commit) | D30. `agent/freshness.py`: each `view`/`read` records the blob id the model saw; a volatile `stale_reads` field names reads gone stale; a whole-file write or delete over a stale read is refused until the file is read again; a stale edit applies where it matches, with a note. `--freshness off` keeps only the count (`stale_actions` in `metrics.json`). `tests/test_freshness.py` |
| B6 | Forkable REPL: the worker forks when idle (`os.fork`, pipes passed with `socket.send_fds`) | a child keeps the namespace, both run independently, and they are confined like the parent | closed (this commit) | D31. `ReplSession.fork()`: the host passes a socketpair end over the worker's fork channel (SCM_RIGHTS); the copy runs in its own session with its own scratch directory and speaks the protocol on that socket; the original reaps it. `tests/test_fork.py`, including the confinement checks run inside a copy under namespaces and under Landlock |
| B7 | Fork, select, merge: a `fork(options)` REPL function, a branch runner, verifier hooks, selection, merge | a scripted three-branch test that keeps the branch whose tests pass | closed (this commit) | D32. `FORK(options, check, steps)` ends the step; each branch runs in a fork of the REPL, from the world at FORK, continuing the main history (shared cache prefix); the check scores it; the passing branch with the fewest steps is kept, or the world at FORK when none passes. `--fork K` (default 1, off). Branch calls are tagged in `calls.jsonl`, and each FORK's outcomes are in `metrics.json`. `tests/test_branches.py` |
| B8 | ReAct arm: `dspy.ReAct` with frond's tools | runs the demo task headless | closed (this commit) | D33: not `dspy.ReAct` but a tools action space in frond's own loop (`--arm react`): each step is `tool` plus JSON `args`, called host-side, with the same tools, documentation, turns layout, cache marks, freshness and step log as the RLM arm. `tests/test_tools_arm.py` |
| B9 | Scopes as savepoints (was P5), after N2 | collapse, rewind and cache-prefix tests | closed (this commit) | D35. `open_scope`, `close_scope`, `abandon_scope` (`agent/scopes.py`): closing collapses the scope's steps to goal → result; abandoning reverts its workspace changes by three-way merge, cuts the context back with the reason as a note, and lists stale REPL names; the open scopes are a volatile field. `--scopes on` (default off). Counts in `metrics.json`. `tests/test_scopes.py` |
| B10 | Summary-compaction arm, rebuilt from the removed `_compact` | runs; the context-policy flag picks it | closed (this commit) | D34. `--context summary`: past the budget, the main model summarises the early steps (and any earlier summary, and the user's mid-turn messages); no index points back, and `history_search`/`history_step` are not offered. Both arms count compactions (`metrics.json`), which also tests A5. `tests/test_summary_arm.py`. Amended by D38 (G27–G29) |
| B11 | Pin DSPy and check at startup (was P6b) | a changed signature gives a clear startup error | closed (this commit) | `dspy==3.4.1` in pyproject; `agent/compat.py` checks the private DSPy parts frond overrides or calls (names and parameters) when the CLI starts, and names what changed; `tests/test_compat.py` |
| B12 | Redact secrets from exported records before results are committed (was I4) | exported records hold no credential values from the environment | closed (this commit) | `agent/redact.py`: the values of credential-named variables (by name), common API key shapes and URL passwords are replaced in every `--export` file and in `-p` output, which Harbor stores and may upload; `tests/test_redact.py` |
| B13 | A TUI world view: branches as a live tree, with per-branch diffs and verifier status | headless render test | open | delight; follows B7 |
| B14 | The truncation note suggests how to narrow (was I6) | test checks the hint | closed (this commit) | [TurnCost](https://arxiv.org/abs/2610.15093): 76.9% against 44%. A cut step output names `history_step(seq)` where the history tools exist, and how to narrow for the arm (a slice or count in code; a narrower range or grep with tools); a cut command output names its log and how to search it. `NarrowingHintTest` |
| B15 | `scripts/dev-env.sh`: dockerd plus the Docker Hub mirror | runs and prints `docker info` | closed 362cc49 | D23; G10 fixed its handling of an existing `daemon.json` |
| B16 | Stop hook: committed, pushed and on `origin/main` before a turn ends | a dirty tree blocks once | closed 362cc49 | D19; G9 made it fail closed |
| B17 | Stop latency measured in the scripted harness (R4) | P95 ≤ 1 s, and no tool runs after the stop | open, low | R4 |
| B18 | A spending guard for the owner's $100 grant | a job that could pass the cap does not start | closed (this commit) | D43: before each Harbor job, `bench.matrix` adds what every trial under `jobs/` cost to the most the job could cost and stops at the cap in `bench/budget.toml`; preflight refuses a model with no price or no per-trial guess. E0's plan is $70.50 on the guesses, under the cap. From the review of #23 (Devin, Codex): every agent's costliest trial counts, by the model Harbor gave it; trials are found anywhere below `jobs/` and the run's jobs directory; a trial whose cost cannot be told stops the run; a frond arm's sub-model needs a price too; a provider failure is counted once. `BudgetTest` |

## Renames

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| N1 | `Compacted` → `Folded` (event and hook) | no `Compacted` or `compacted` identifiers remain; tests pass | closed (this commit) | renamed throughout |
| N2 | `Record.scope` → `Record.agent`, before B9 | logs write `agent`, readers accept `scope`, and the Harbor adapter reads the new name | closed (this commit) | `test_a_log_written_before_the_rename_still_loads`; the adapter reads either |
| N3 | `Checkpoints` → absorbed into worlds (B4) | the class is gone | closed | removed in B4b (D29) |

## Questions, unknowns, unverified claims

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| U1 | Daily driver or research vehicle? | answered | closed | research vehicle: D16 (owner, 2026-11-03) |
| U2 | Which providers and models? | chosen | closed | D24: Anthropic, with Opus 5.5 primary |
| U3 | How long the owner pauses between turns, which decides the cache TTL | — | closed: not applicable | research runs have no human pauses; A7 deferred |
| U4 | Does the owner edit files during turns? | — | closed: moot | B4's revert-by-merge handles concurrent edits for anyone |
| U5 | Evaluation budget | — | closed | became REQ-1 |
| U6 | Does the sandbox work in task containers? | probe in default Docker | closed | 2026-11-03: user namespaces refused (EPERM), Landlock works (`confined=landlock`) |
| ORDER | Work order | — | closed | D16: the research order |
| Q1 | The OpenAI and Gemini default model IDs in `lm.py` are unverified (was I8) | each confirmed or replaced from the provider's model list | open, low | Anthropic IDs confirmed (D24) |
| Q2 | Does GPT-5.4-mini write literal `\n` into scripts? (was I9) | measured if an OpenAI arm runs | deferred: no OpenAI arm planned | [2608.06370](https://arxiv.org/abs/2608.06370) |
| V1 | No turn has run on a live model | E0 completes a task | blocked: REQ-1 | — |
| V2 | frond has never run a real Terminal-Bench task | E0 | closed: PR #27 | 2026-11-03: Harbor plus Docker verified with the oracle agent; and `bench/experiments/smoke.toml` ran frond in a TB 4.0 container through the matrix runner with every arm flag set and a dummy key: install, flags, the API reached through the egress CA (401 from Anthropic), export, trajectory and verifier all worked. 2026-11-03: the paid smoke ran frond on a real task end to end with Opus 5.5; the first attempt found G34 |
| V3 | The macOS Seatbelt profile has never run | — | closed: won't do | D25 (the program is Linux-only) |
| V4 | The cache savings are simulated | E0 measures `cache_read_input_tokens` | blocked: REQ-1 | — |
| V5 | Devin (PR #3): the latest-step cache breakpoint never matches, because the volatile fields change the last user message | the cache simulator | closed: refuted | the breakpoint sits on the latest assistant reply, before the volatile fields, which go last; `tests/test_caching.py` shows every step after the first reads its predecessor's prefix (reads grow with history, above 70% of input). Real reads: V4 |
| V6 | Devin (PR #5): the Stop hook does not check that work reached `main` through a merge commit | — | closed: declined | D15 is applied at merge time (the merge call names the method); a hook check would add a failure mode without a failure seen |

## Requirements not met (`design.md` has every requirement's status)

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| R1 | frond against external harnesses on the same model | E11, E1 | blocked: REQ-1 | D21 recasts R1 for research |
| R2 | A turn's net change is reviewable | net diff between two worlds | closed (this commit) | `/diff`, `Agent.turn_diff`; `TurnRecord.files` is the net change; `test_the_turns_net_change_is_reviewable` |
| R3 | Undo keeps later edits made by others | B4b: the concurrent-edit test through `/undo` | closed (this commit) | `test_an_edit_someone_makes_after_the_turn_survives_undo`, and same-line edits are kept and reported; was P2 |
| R4 | Stopping is prompt and final | B17 | open, low | — |
| R5 | The user's words cannot be forged | — | closed | 3c188c9 (D14) |
| R6 | No unapproved writes, network use or credentials | the main agent's commands remain | deferred | worker and read-only agents done (3c188c9, D13). The main agent's command sandbox (was P4) is daily-driver work (D16). Benchmark runs are already isolated by the container |
| R7 | The agent can rewind context and workspace together | B4b, then B9 | closed (this commit) | `abandon_scope` returns the context and the workspace to the scope's savepoint together (B9); the REPL is not rewound, and its changed names are listed as stale |
| R8 | Most input is served from cache | E0 | blocked: REQ-1 | — |
| R9 | An incompatible DSPy fails at startup | B11 | closed (this commit) | B11 |
| R11 | macOS | — | closed: won't do | D25 |

## Gaps

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| G1 | Under Landlock alone, the worker can read frond's environment through `/proc` and send it over UDP using ctypes (was I13) | decided | deferred | In research containers the key already sits in frond's own environment, and the container is the boundary. Revisit for daily use, with `PR_SET_DUMPABLE` as the candidate fix |
| G2 | In TB containers the worker runs under Landlock, not namespaces | — | closed: accepted | U6 |
| G3 | frond never sets reasoning effort, so Opus 5.5 would run at `medium` | B1 | closed 2605fb3 | D26 |
| G4 | DSPy sends any provider whose `<PREFIX>_BASE_URL` is set through LiteLLM, which cannot carry `prompt_cache`. Hosted sessions set `ANTHROPIC_BASE_URL` to the public endpoint, so every frond call from such a VM failed | payload test | closed 2605fb3 | D26 |
| G5 | Harbor may forward `ANTHROPIC_BASE_URL` into task containers | E0's first run shows the container environment | open, low | frond handles the variable either way (D26) |
| G6 | This VM's egress re-terminates TLS, so task containers must trust its CA, or installs and API calls fail | an install-only run in a TB 4.0 container | closed 63d52f8, superseded by G7 | the Harbor adapter carried the host's CA bundle into the container for frond's own processes. Verified 2026-11-03: frond 0.1.0 installed in `layout-config-recreation2`. G7 moved the fix to the environment layer and removed the adapter's copy |
| G7 | The CA fix reached only frond's processes. The oracle agent's solutions, any other agent, and the task's own commands still failed TLS: E0a's oracle failed `fin-saccr-rwa` and `satb-audio-transcription` on `pip install` | both pass with the oracle | closed (this commit) | `bench/compose/egress-ca.yaml` mounts the CA into every task's `main` service and sets the CA variables (D27). Both tasks scored 1.0 with it (2026-11-03). TB 4.0's separate verifier containers do not get the overlay (Harbor warns); their dependencies are baked in, and E0a shows whether any verifier needs the network |
| G8 | `docker image prune -af` beside a sweep removed layers that concurrent pulls were extracting: E0a lost `formal-crypto` and `lake-temp-glm` before their agents started | the E0a rerun has no layer-extraction failures | closed eed4a55 | `bench/prune.py` removes only images unused at two passes in a row, one `docker rmi` at a time. In the rerun both images pulled and extracted; the two tasks then failed on their CPU requests (G20) |
| G9 | The Stop hook let a turn end when `origin/main` could not be resolved (Devin, PR #5) | `tests/test_stop_guard.py` | closed (this commit) | it now blocks once with the reason; `stop_hook_active` still lets the next stop through |
| G10 | `dev-env.sh` left an existing `daemon.json` without the mirror, did not report a running daemon without it, and could not start `dockerd` as a non-root user (Devin, PR #5) | runs in this VM | closed (this commit) | it merges the mirror into the file, warns when the running daemon lacks it, and uses `sudo` when not root |
| G11 | `research.md` and `design.md` cited P0 for the pilot that the ledger calls E0 (Devin, PR #5) | — | closed (this commit) | renamed; `research.md`'s run command now starts from `frond/`, like the checks (the other PR #5 note) |
| G12 | A crash mid-write left a partial last line in the step log, and the next record was appended to it, losing both (PR #3) | `test_a_line_cut_short_by_a_crash_does_not_swallow_the_next_record` | closed (this commit) | `StepLog.attach` ends a cut-short line before appending |
| G13 | `--export` after `--continue` wrote every earlier session's steps but only this process's token usage (PR #3) | `test_a_continued_run_exports_only_what_it_did` | closed (this commit) | the export covers this process: its calls, and the steps after those it loaded (`continued_after_seq` in `metrics.json`) |
| G14 | `usage_totals` read only OpenAI-style keys, so Anthropic-native usage counted zero tokens in `usage.json` (PR #3) | `UsageTotalsTest` | closed (this commit) | it sums `metrics.normalize_usage`, one normalizer for every export |
| G15 | `/new` left the old conversation searchable through `history_search`, and the next save overwrote the old conversation's session file, so `--continue` could not reach it (PR #3; the overwrite was found while fixing it) | `test_a_new_conversation_cannot_search_the_old_one` | closed (this commit) | `/new` starts a new session file and step log (`Agent.new_log`, `StepLog.restart`); the old files stay |
| G16 | Code that did not compile cleared the names digest, so the next step showed no variables (PR #3) | `test_code_that_does_not_compile_leaves_the_names_as_they_were` | closed (this commit) | the digest changes only when the worker reports one |
| G17 | The step log is described as lossless but cuts outputs over 200,000 characters (PR #3) | — | closed (this commit) | documented in `steplog.py` |
| G18 | File changes made by background jobs are not covered by `/undo` (PR #3) | B4b: a background job's write is reverted by `/undo` | closed (this commit) | worlds snapshot the directory, whoever wrote to it; `test_a_background_jobs_writes_during_the_turn_are_undone`. Writes after the turn ends count as someone else's, and undo keeps them |
| G22 | A run that ended because the model provider failed (rate limit, outage, auth) exited 1 and was scored as the agent's failure, which would bias pass rates down under a capped key | `ProviderFailureTest` | closed (this commit) | such turns record `error_kind: provider`; headless frond exits 75; `metrics.json` carries it, and the analysis reports the trial as an infrastructure failure, unscored. A context overflow or an invalid request stays the harness's failure. Not retried by Harbor, whose retry would also rerun genuine agent crashes. The reference agents' provider failures, which Harbor reports as its own exception types (`ApiRateLimitError`, `AgentAuthenticationError`, ...), are left unscored the same way |
| G23 | TB 4.0 tasks with a separate verifier container do not get the egress-CA overlay (Harbor applies it to the agent's container only), so a verifier that downloads packages fails here for every agent: `vba-userform-port` | E0a | closed: accepted | excluded through E0a's oracle-failure list (`bench/results/2026-11-03-e0a-oracle/oracle-failures.txt`), which every spec reads. A VM without TLS interception would bring it back |
| G24 | Harbor 0.25.0's own `dspy-rlm` agent, E11's stock-RLM reference, failed in two ways: Harbor's environment lacked DSPy, and with it, the agent passes `max_iterations`, which DSPy renamed in 3.3 | the smoke test reaches the model with `dspy-rlm` | closed (this commit) | the runner starts Harbor as `uvx --from harbor[dspy]==0.25.0 --with 'dspy>=3.1.3,<3.3'`. frond is unaffected: it installs its own pinned DSPy in the container. Caveat for E11's mechanisms claim: the stock reference runs DSPy 3.2, frond 3.4.1 |
| G25 | `medical-claims-processing` never starts here: its `playwright-mcp` sidecar runs `npx @playwright/mcp` at startup, which fetches from npm and fails with `SELF_SIGNED_CERT_IN_CHAIN`, because, like G23's verifiers, the sidecar does not get the egress-CA overlay | ran the sidecar image alone | closed: accepted (this commit) | excluded through E0a's oracle-failure list. The overlay is job-wide, so it can only name services every task has; a VM without TLS interception would bring the task back |
| G26 | `docker exec` processes ran with umask 0000 in this VM, so every file the agent, the reference solution or the tests created was world-writable: `rs-archive-clone`'s oracle failed 41 of 57 tests on file modes (0666, expected 0644). dockerd 29.9.2 sets its own umask to 0 whatever it is started with, and containerd, the shims and runc's exec inherit it; `docker run` processes get 0022 from runc's init, which hid it | `test_preflight_refuses_a_daemon_whose_exec_umask_is_not_022`; `docker exec … umask` prints 0022 | closed (this commit) | D39: `scripts/dev-env.sh` makes runc behind a umask-022 wrapper Docker's default runtime and warns otherwise; the matrix runner refuses to start unless it measures 0022 for `docker exec`, and refuses when it cannot measure it; the script's probe is plain shell, so it needs only Docker (both from Devin, PR #22). E0a's third run is void for this reason; under the fix, the fourth run's `rs-archive-clone` passes |
| G27 | Under `--context summary`, sub-agents and FORK branches were still given `history_search` and `history_step`, so the control arm could search back the steps it had summarised by delegating; sub-agents also folded with an index pointing at those tools (Devin, PR #17) | `EveryLoopTest` | closed (this commit) | D38: the arm's policy covers every loop. One `Agent.memory` (the step log under the fold, none under the summary) feeds every toolbox; sub-agents run the arm's context policy; the conversation preview and the sub-agents' truncation notes name `history_search` only where it exists |
| G28 | FORK branches under `--context summary` never got a summary: their hooks lacked `summarize`, so past the budget a branch kept only a clipped trace (Devin, PR #17) | `test_a_branch_past_the_budget_is_summarised_by_the_model` | closed (this commit) | branch and sub-agent hooks summarise with their loop's model (branches: the main model, billed to the branch; sub-agents: the sub-model), and count their compactions |
| G29 | When the summary call failed, the stand-in trace dropped the earlier summary and the user's mid-turn messages; and when it succeeded, the user's messages survived only as the summariser restated them (Devin, PR #17) | `SummaryCompactionTest` | closed (this commit) | D38: the user's messages stay verbatim ahead of the summary, as Codex keeps them; a failed call keeps the earlier summaries plus a trace of the steps since; nothing is compacted again when only notes and the user's words are left. Headless runs have no mid-turn messages, so E4 was not affected by the message part |
| G30 | `RunMetrics` counters were bumped with bare `+=` from parallel sub-agent threads, which can lose an update | — | closed (this commit) | `RunMetrics.bump` and the tool counters take a lock |
| G31 | The adapter installed frond's wheel with a plain `uv tool install`, which resolves every dependency but DSPy (pinned exactly) from PyPI when each container starts, so trials of one experiment could run different versions of litellm and the rest | a constrained install in a scratch tool directory runs `frond --version` with DSPy 3.4.1 | closed: fixed (this commit) | D42: the adapter exports `uv.lock` as constraints beside the wheel and installs with `--constraints`, so every trial gets the locked versions |
| G32 | `uvx` installs Harbor's environment on first use with no timeout on a stalled download: on 2026-11-03 the paid smoke run's job sat for minutes on a numpy wheel, with no bytes arriving, before Harbor started | `test_a_stalled_harbor_install_is_retried_then_refused` | closed (this commit) | the runner's preflight runs `harbor --version` through the same `uvx` line, up to 3 times with a 300 s timeout each, and refuses to start if none succeeds (`matrix.harbor_ready`); the environment is cached afterwards |
| G33 | With a real key, E11's reference agents have no per-trial cost bound: Claude Code and Terminus 2 run until the task's 8-hour limit, while the spending guard assumes $2 per trial before one is measured (D43), so one trial could pass the guard's estimate by an unknown amount | E11's spec bounds every arm per trial, and the budget's guess for each covers its bound | open: before E11's first trial | Harbor 0.25.0 offers the bounds: Claude Code's `max_budget_usd` (its `--max-budget-usd`), Terminus 2's `max_turns`; Harbor's `dspy-rlm` already stops at 20 iterations and 50 LLM calls. A bound that binds changes the reference, so set it above leaderboard-typical spend and report how often it binds. D45 |
| G34 | frond's first real model call (the paid smoke, 2026-11-03) ended the run: Opus 5.5 at high effort opened with a line of narration and wrote its code as a native tool call (`<invoke name="python"><parameter name="code">…`), with no `[[ ## code ## ]]` marker, and an unparseable reply ended the turn with `AdapterParseError` after 1 of 3 steps. Six replays of the same first request: every reply opened with narration, 3 of 6 skipped the markers for a bare fenced block | `ParseFailureTest`, `UnparsedStepTest`; the seven real replies all parse; the second paid smoke | closed (this commit) | D46: `FrondAdapter.parse` recovers a reply that names exactly one action (one `<invoke>`, or for the code arm one fenced block), with the text before it as the reasoning; a reply that still cannot be read becomes an error step that shows the model its words and the format, at the cost of a step. `metrics.json` counts `parse_failures` (every reply off the protocol), `parse_recovered` and `unparsed_steps`, so E0 still measures adherence |
| G35 | The runner checked frond's source digest only when resuming a jobs directory, but each Harbor job builds frond's wheel when it starts, so a source edited while a multi-job run (E0's three arms) was going on would reach the later arms unrecorded | `test_a_source_edited_during_the_run_stops_it_before_the_next_job` | closed (this commit) | before each job the runner compares the digest with the run's and stops if it changed, unless `--allow-changed-source`; experiments run from a frozen worktree besides (D47) |
| G21 | The world store keeps every version of every file it has seen, for all of a workspace's sessions, and nothing removes old objects | a store past a size bound drops objects no session file or step record reaches | closed (this commit) | D37: past 2 GB, at startup in the background, a mark-and-sweep keeps every object reachable from the worlds of sessions touched in the last 30 days and every object used in the last hour; `Store.put` marks reused objects in use, and each turn's first world is logged at once. `CollectionTest` |
| G20 | 10 of TB 4.0's 66 tasks declare more than 4 CPUs or a GPU for their agent or verifier container, and Docker refuses to start them in this 4-CPU VM ("range of CPUs is from 0.01 to 4.00") | — | closed: accepted (this commit) | D28: the population is the 56 tasks that fit, keeping every task's declared limits; the list is `bench/datasets/terminal-bench@4.0.0-exceeds-4cpu-nogpu.txt`. Three more ask for 16 GB of memory, which Docker accepts; they risk only running out of memory. A bigger VM would bring the 10 back |
| G19 | `GitSnapshots`: a nested workspace's objects path, CRLF and filter conversions, and file-to-directory changes in undo (PR #3) | — | closed (this commit) | B4b deletes `GitSnapshots` in favour of worlds, which store raw bytes and handle kind changes (`test_world`) |

## Review findings (Devin on PRs #9–#21)

Devin reviewed every PR from #9 to #21 after it had merged, and nobody read the reviews until 2026-11-03 (D40). Each finding is a claim to verify: closed as fixed with its test, or as refuted or declined with what was traced. Codex found nothing on these PRs. Devin's unposted security findings are REQ-3.

| ID | PR | Finding | Status | Resolution |
|---|---|---|---|---|
| F1 | [#9](https://github.com/ethan-wickstrom/experiments/pull/9#discussion_r4452527152) | 🔴 `/new` in the same second as a saved turn reuses the session path (one-second timestamp plus PID), so the next save overwrites the earlier conversation and its step log | closed: fixed (this commit) | session files are named to the microsecond and never reuse one that exists. In `test_sessions_name_their_worlds_and_old_sessions_let_go` |
| F2 | [#9](https://github.com/ethan-wickstrom/experiments/pull/9#discussion_r4452527344) | 🔴 The pruner removes an image after two idle polls, which does not show that no pending trial will use it: a trial starting on a reused task image can lose it | closed: fixed (this commit) | the pruner learns each image's task from the compose project of the containers created from it (`<task>__<id>__env`) and keeps the images of tasks the job has yet to finish; tags could not name the task, since images pulled by digest list theirs as `<none>`. Docker's event log since the previous pass covers containers created and removed between passes (Devin, #23). `test_the_pruner_keeps_images_of_tasks_with_trials_pending`, `test_the_pruner_learns_owners_from_containers_it_never_saw` |
| F3 | [#9](https://github.com/ethan-wickstrom/experiments/pull/9#discussion_r4452527507) | 🟡 The CA overlay requires `FROND_EGRESS_CA`, though `dev-env.sh` and the runner accept `SSL_CERT_FILE` as a fallback | closed: fixed (this commit) | the overlay takes `FROND_EGRESS_CA`, else `SSL_CERT_FILE`, like the runner; `docker compose config` checked with both, one and neither set |
| F4 | [#9](https://github.com/ethan-wickstrom/experiments/pull/9#discussion_r4452527662) | 🔍 Check that the runner mounts the CA overlay itself (the runner did not exist then) | closed: verified | `matrix.command` adds the overlay whenever a CA is set, and only then (`test_arms_alternate_by_batch_and_commands_carry_the_arm`) |
| F5 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452665160) | 🔴 A ratio claim's p-value bootstraps the observed pairs, so it is not computed under the null: any ratio just under the bound gets the minimum p, whatever n | closed: fixed (this commit) | D41: the claim is tested on per-task values treated − bound × control with a studentized bootstrap that imposes the null. On skewed null data (20 tasks), the old test rejected 14% of the time at a nominal 5%, the new one 6.7%. `BootstrapTTest` |
| F6 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452665313) | 🔴 A Harbor job that fails is recorded, but the runner exits 0 and the analysis uses its partial results | closed: fixed (this commit) | Harbor exits 0 whenever a job finishes, so a nonzero exit is the job's own failure: the runner now runs the remaining jobs and exits 1, and the report names every task short of its planned trials. An early stop reads only a batch whose jobs all finished every trial (Devin, #23). `test_a_failed_harbor_job_fails_the_run`, `test_tasks_short_of_their_trials_are_reported`, `test_no_early_stop_on_a_batch_with_a_failed_job` |
| F7 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452665491) | 🔴 Duplicate claim IDs collapse in a dict, so a hypothesis disappears and Holm's family shrinks | closed: fixed (this commit) | `spec.load` refuses repeated claim ids. `test_repeated_claim_ids_are_refused` |
| F8 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452665655) | 🔴 Resuming after the spec changed mixes jobs from the old and new spec, and the report labels all of them with the new hash | closed: fixed (this commit) | D42: a jobs directory is bound to its spec's digest and to a digest of frond's source (`src/`, the adapter, `pyproject.toml`, `uv.lock`); resuming after either changed is refused, unless `--allow-changed-source`, which each run records. Each job is recorded before Harbor starts, so a run killed midway still binds the directory (Devin, #23). `test_jobs_of_another_spec_or_source_are_not_resumed`, `test_a_job_is_recorded_before_harbor_starts` |
| F9 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452665960) | 🔍 The report lists the configurations it saw but never checks them against the spec | closed: fixed (this commit) | D41: every trial's recorded configuration is checked against its arm's model and options; a trial that contradicts them is unscored and listed, and the next valid trial takes its place. `test_a_trial_that_did_not_run_its_arm_is_not_scored` |
| F10 | [#10](https://github.com/ethan-wickstrom/experiments/pull/10#discussion_r4452666070) | 🔍 After an early stop on a confidence sequence, the final claims use a fixed-n Wilcoxon test (optional stopping) | closed: fixed (this commit) | D41: a spec that may stop early decides pass-rate claims by their confidence sequences and any other claim by p × planned looks × claims; both are valid at a stopping time the data choose. The test case: the fixed-size p is 0.016, Holm would accept it, and the open sequence does not. `test_a_spec_that_may_stop_early_decides_by_rules_valid_at_any_stop` |
| F11 | [#11](https://github.com/ethan-wickstrom/experiments/pull/11#discussion_r4452693525) | 🟡 Redacting a numeric credential equal to a serialized number leaves invalid JSON in an export | closed: fixed (this commit) | worse than reported: redacting serialized JSON also missed secrets that JSON escapes (a quote, a backslash, non-ASCII), in exports and in `-p --json`. `Redactor.json` redacts the data's strings, keys included, before serializing. `test_data_is_redacted_before_it_becomes_json`, `test_the_headless_log_and_answer_are_redacted` |
| F12 | [#12](https://github.com/ethan-wickstrom/experiments/pull/12#discussion_r4452808264) | 🔴 Where a directory became a file, revert restores the children before removing the file, so `/undo` fails | closed: fixed (this commit) | revert applies removals first, as checkout does, so the file goes before the directory's files come back; the report lists paths in order whatever the order applied. `test_a_directory_replaced_by_a_file_comes_back` |
| F13 | [#12](https://github.com/ethan-wickstrom/experiments/pull/12#discussion_r4452808352) | 🔴 The turn's last snapshot runs outside `run_turn`'s error handling (and `begin_turn`'s first), so an unreadable file strands the turn without `TurnFinished` | closed: fixed (this commit) | an unreadable file or directory is kept by its signature, like a large file, and never restored; any other failure turns snapshots off with its reason instead of failing the turn, and a turn whose last snapshot failed reports no net change rather than a wrong one. A failed snapshot's empty id is refused by checkout and revert, which would have read it as an empty tree and deleted every tracked file, and FORK, abandoning a scope, undo and command diffs stop cleanly on it (Devin, #25; the too-large case had the same hazard). `UnreadableTest`, `test_an_empty_world_id_is_never_checked_out_or_reverted`, `test_a_fork_whose_snapshot_fails_changes_nothing` |
| F14 | [#12](https://github.com/ethan-wickstrom/experiments/pull/12#discussion_r4452808541) | 🟡 The ignored set is refreshed only after foreground commands, so a background job's new ignored output counts as a change and `/undo` deletes it | closed: fixed (this commit) | every snapshot takes in the paths git began ignoring since the previous one, whoever made them. `test_a_background_jobs_new_ignored_output_survives_undo` |
| F15 | [#12](https://github.com/ethan-wickstrom/experiments/pull/12#discussion_r4452808750) | 🟡 A mode-only change appears in the net change with an empty diff | closed: fixed (this commit) | a mode change shows as `(mode 644 → 755)`, alone or after the diff. `test_a_mode_change_alone_shows_in_the_net_change` |
| F16 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452868097) | 🔴 A recursive delete skips the stale check | closed: fixed (this commit) | before a directory goes, every read inside it is checked: stale ones are counted and, with freshness on, refuse the delete as they would for each file; the model's own delete then records them absent. `test_deleting_a_directory_checks_every_read_inside_it` |
| F17 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452868283) | 🔴 Observations are keyed by the path as named, so a symlink alias bypasses the stale check | closed: fixed (this commit) | observations are keyed by the file's real path, so every name of a file shares one read; a read through a symlink also remembers where the name led, so a name retargeted since counts as unseen, and moving a link leaves its target's read alone (review of #24). `test_a_symlink_and_its_target_share_one_read`, `test_a_symlink_retargeted_since_the_read_is_stale`, `test_moving_a_link_leaves_its_targets_read_alone` |
| F18 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452868603) | 🔴 After delete, a patch delete or move, the old observation stays, and a later write to that path is refused for the rest of the turn | closed: fixed (this commit) | worse than reported: a file deleted by a shell command after a read could never be written again in that turn either, since `read` fails on a missing file. The model's own delete or move now records the file absent (a move carries each read, fresh or stale, to the new place), a whole-file write over a file that is gone goes ahead, counted and noted, since nothing can be lost, and a child already gone counts but does not block deleting its directory (review of #24). `test_the_models_own_delete_or_move_leaves_its_picture_true`, `test_a_file_deleted_behind_the_models_back_can_be_written_again` |
| F19 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452868755) | 🔍 A stale edit whose old text no longer matches fails before it is counted (`stale_actions` undercounts) | closed: fixed (this commit) | an edit counts its stale read before matching. `test_a_stale_edit_that_no_longer_matches_is_still_counted` |
| F20 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452868923) | 🔍 Writing a file never read records it as read, so later outside changes count as stale reads | closed: declined | by D30's definition the model knows a file's content after writing it, as after reading it: an outside change after that is one it has not seen, and a later whole-file write would overwrite it, which is the stale action H3 counts |
| F21 | [#13](https://github.com/ethan-wickstrom/experiments/pull/13#discussion_r4452869085) | 🔍 Approved files under `~` outside the workspace look stale | closed: fixed (this commit) | with real-path keys, a `~/` file is checked where it is. `test_a_file_under_home_is_checked_where_it_is` |
| F22 | [#14](https://github.com/ethan-wickstrom/experiments/pull/14#discussion_r4452923676) | 🔴 Forked REPL copies have their own process groups, so shutting down the original leaves running copies alive | open | — |
| F23 | [#14](https://github.com/ethan-wickstrom/experiments/pull/14#discussion_r4452923810) | 🟡 Finished copies' scratch directories accumulate until the original closes | open | — |
| F24 | [#14](https://github.com/ethan-wickstrom/experiments/pull/14#discussion_r4452923930) | 🔍 A daemon thread holding a lock at fork leaves it locked in the copy | open | — |
| F25 | [#14](https://github.com/ethan-wickstrom/experiments/pull/14#discussion_r4452924080) | 🔍 A failed `os.fork` leaks the received descriptor | open | — |
| F26 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011055) | 🔴 Worlds exclude `.git`, so a branch's commit or checkout leaves HEAD, refs and the index changed for later branches and the kept result | open | — |
| F27 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011233) | 🔴 Files over 16 MB cannot be restored, so the reset between branches fails | open | — |
| F28 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011401) | 🔴 Main-line background jobs keep writing during FORK, and the resets between branches erase their writes | open | — |
| F29 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011580) | 🟡 A branch's job log directory does not exist, so background jobs in a branch fail | open | — |
| F30 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011791) | 🔍 With different main and sub models, a branch's `llm_query` calls are not billed to the branch | open | — |
| F31 | [#15](https://github.com/ethan-wickstrom/experiments/pull/15#discussion_r4453011945) | 🔍 Branch prompts offer FORK, which a forked REPL refuses | open | — |
| F32 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453077955) | 🔴 The tools arm keeps only the last 12,000 characters of history and drops earlier user requests, which the RLM arm keeps (an arm asymmetry in H1) | open | — |
| F33 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453078116) | 🔴 The tools arm renders a background job as a finished command and drops its id | open | — |
| F34 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453078263) | 🟡 A tools-arm `submit` with wrong field names ends the turn with empty fields instead of an error | open | — |
| F35 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453078446) | 🔍 Trajectories export tools-arm steps as Python calls | open | — |
| F36 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453078585) | 🔍 Tools-arm `grep` results are verbose JSON, unlike the REPL's grouped matches | open | — |
| F37 | [#16](https://github.com/ethan-wickstrom/experiments/pull/16#discussion_r4453078687) | 🔍 `--arm react --script` builds code-only steps | open | — |
| F38 | [#18](https://github.com/ethan-wickstrom/experiments/pull/18#discussion_r4453173871) | 🔴 The savepoint is taken mid-step at `open_scope`, but abandoning cuts the whole opening step, so its earlier edits survive with no record | open | — |
| F39 | [#18](https://github.com/ethan-wickstrom/experiments/pull/18#discussion_r4453174075) | 🔴 With snapshots off or over the limit, abandoning cuts the history but reverts nothing | open | — |
| F40 | [#18](https://github.com/ethan-wickstrom/experiments/pull/18#discussion_r4453174270) | 🔴 Abandoning does not report files it could not restore (over 16 MB) | open | — |
| F41 | [#19](https://github.com/ethan-wickstrom/experiments/pull/19#discussion_r4453204676) | 🟡 The startup check tests that DSPy's helpers exist, not that they are callable | closed: fixed (this commit) | every entry declares what frond assumes; a helper frond calls must be callable, and `field_header_pattern` a compiled pattern. `test_a_helper_that_is_no_longer_callable_is_named`, `test_the_pattern_reply_recovery_matches_with_is_checked` |
| F42 | [#19](https://github.com/ethan-wickstrom/experiments/pull/19#discussion_r4453204810) | 🟡 The startup check compares parameter names only, not their kinds | closed: fixed (this commit) | parameters are compared by name and kind: frond passes them by position or keyword, so a parameter made keyword-only breaks its calls even under the same name. `test_a_parameter_that_changed_kind_is_named` |
| F43 | [#19](https://github.com/ethan-wickstrom/experiments/pull/19#discussion_r4453204934) | 🟡 `now.md` listed B11 after it closed | closed: verified | `now.md` was rewritten at the end of the first session and no longer lists B11 |
| F44 | [#19](https://github.com/ethan-wickstrom/experiments/pull/19#discussion_r4453205080) | 🔍 Only the CLI runs the startup check; library use does not | closed: fixed (this commit) | `Agent.__init__` runs the check too; it costs a few lookups per agent. `test_library_use_is_checked_too` |
| F45 | [#20](https://github.com/ethan-wickstrom/experiments/pull/20#discussion_r4453377445) | 🔴 A sweep can delete a blob that `put` reused between the sweep's stat and its delete | closed: fixed (this commit) | the sweep renames a candidate aside first, so a `put` from then on writes it anew, and deletes it only if it still shows no use once aside; one marked in between goes back. Leftovers of an interrupted sweep are put back by hard link, which never replaces a fresh copy a `put` wrote meanwhile (Devin, #25). `test_an_object_reused_while_the_sweep_runs_stays`, `test_an_interrupted_sweep_puts_its_objects_back`, `test_a_fresh_copy_written_while_set_aside_is_kept` |
| F46 | [#20](https://github.com/ethan-wickstrom/experiments/pull/20#discussion_r4453377571) | 🔴 Continuing a session untouched for 30 days: the startup collection can remove its worlds | closed: fixed (this commit) | the session being continued is always a root, however old. In `test_sessions_name_their_worlds_and_old_sessions_let_go` |
| F47 | [#20](https://github.com/ethan-wickstrom/experiments/pull/20#discussion_r4453377762) | 🔍 Provider failures inside sub-agents and `llm_query` are not classified as provider failures | closed: fixed (this commit) | such failures are counted as `provider_errors` in `metrics.json` and the report; the trials stay scored, since the agent ran and coped, but an arm that leans on sub-calls is more exposed to a capped key's limits, which the count shows. `test_a_provider_failure_the_turn_survives_is_counted` |
| F48 | [#21](https://github.com/ethan-wickstrom/experiments/pull/21#discussion_r4453392862) | 🟡 In the tools arm, the truncation hint points at `history_step`, whose output the same limit cuts | open | — |
| F49 | [#21](https://github.com/ethan-wickstrom/experiments/pull/21#discussion_r4453393011) | 📝 A continued session's command-log hint names a temporary log deleted at close | open | — |
| F50 | [#27](https://github.com/ethan-wickstrom/experiments/pull/27#discussion_r4454565240) | 🟡 An `<invoke>` that repeats its `code` parameter was recovered with the last value only, dropping the first action | closed: fixed (this commit) | a repeated parameter, or text inside the call that is no parameter, refuses recovery, so the reply becomes an error step. In `test_a_reply_that_could_mean_more_than_one_action_is_not_guessed` |
| F51 | [#27](https://github.com/ethan-wickstrom/experiments/pull/27#discussion_r4454565403) | 🟡 Sub-agents' replies off the protocol were not counted: `_SubHooks` had no `reply_unparsed`, and the sub-adapter no metrics | closed: fixed (this commit) | counted under `sub_parse_failures`, `sub_parse_recovered` and `sub_unparsed_steps`, apart from the main model's, since sub-agents run the sub-model. `test_a_sub_agents_replies_count_apart_from_the_main_models`. E0 runs #27's merge, so its sub-agent replies go uncounted; its main-line and branch counts are complete |
| F52 | [#28](https://github.com/ethan-wickstrom/experiments/pull/28#discussion_r4454598122) | 🟡 The startup check rejects a parameter made positional-only, though frond's own calls pass it by position | closed: declined | DSPy also calls frond's overrides of these methods, and a check per call site and direction would be more code for a release frond pins exactly. The check errs strict: a false alarm is a clear startup error naming the pinned version, a missed change is a turn that misbehaves |
| F53 | [#28](https://github.com/ethan-wickstrom/experiments/pull/28#discussion_r4454598548) | 🔍 A checked method whose signature cannot be read passed unchecked | closed: fixed (this commit) | it is reported as a problem. `test_a_signature_that_cannot_be_read_fails_closed` |

## Assumptions to test

| ID | Item | Tested by | Status |
|---|---|---|---|
| A1 | The model opens and closes scopes without being told each time | E5: `scopes` counts in `metrics.json` | blocked |
| A2 | Collapsing a closed scope hides nothing needed later | E5: `history_step` calls on collapsed steps | blocked |
| A3 | Listing stale names after an abandon keeps the model off discarded values | E5, B9 tests | blocked |
| A4 | Rewinds need a verifier signal | E5: split by whether the task has tests | blocked |
| A5 | TB turns rarely reach the fold budget, so long-horizon sets are needed for H4 and H5 | E0: `compactions` per run in `metrics.json` | blocked |
| A6 | Editing through string literals costs extra tokens and failed edits | E0: failed edits per edit, output tokens per changed line | blocked |
| A7 | A 1-hour cache TTL pays when more than about 0.65·T/H of gaps between turns last 5–60 min | — | deferred: no human pauses in research runs |
| A8 | The need behind "Enter→stop" was halting promptly | — | closed: D09 |
| A9 | The per-step layout does not lower pass rate | E6 | blocked |
| A10 | Inline scopes can replace sub-agents for sequential subtasks | E5 | blocked |
| A11 | GEPA gains hold on held-out tasks | E7 | blocked |
| A12 | Confining the worker costs no capability | E0; half done: the whole suite passes confined (3c188c9) | blocked |
| A13 | Native tool-call rendering changes what the model imitates | E12 | blocked |

## Calibrations

Every row is blocked on E0's logs. Each is done when its measurement is recorded here and the value is kept or changed with a reason.

| ID | Number | Where | Measurement |
|---|---|---|---|
| K1 | 40 REPL steps per turn | `src/frond/agent/session.py:78` | share of turns that hit it |
| K2 | 16 steps per sub-agent | `src/frond/agent/session.py:84` | share of sub-agent runs that hit it |
| K3 | 16,000 characters of step output shown | `src/frond/agent/session.py:83` | how often output is cut, and whether the next step re-reads it |
| K4 | 24,000 characters of command output shown | `src/frond/agent/tools.py:50` | the same, for commands |
| K5 | 300-line view window | `src/frond/agent/tools.py:47` | how often consecutive views page through one file |
| K6 | 32,000 output tokens per reply | `src/frond/agent/lm.py:66` | how often a reply hits the limit |
| K7 | fold budget: 45% of the window, at most 150,000 tokens | `src/frond/agent/session.py:204` | fold frequency, and `history_step` use after folds |
| K8 | 3.6 characters per token | `src/frond/agent/session.py:206` | characters per token from provider usage |
| K9 | last 4 steps kept unfolded | `src/frond/agent/rlm.py:111` | how often folded steps are re-read |
| K10 | 8,000 characters of earlier user messages shown | `src/frond/agent/session.py:127` | how often earlier messages fall out |
| K11 | 20 diffs shown per command | `src/frond/agent/tools.py:51` | how often one command changes more than 20 files |
| K12 | per-command diffs switched off when a snapshot takes over 2 s | `src/frond/world/timeline.py` (`SLOW_SECONDS`) | snapshot times on large repositories |
| K13 | 40 REPL names listed | `src/frond/agent/_worker.py:49` | names a REPL typically holds |
| K14 | BM25 k1 = 1.2, b = 0.75 | `src/frond/agent/steplog.py:30` | whether `history_search` hits answer real queries |
| K16 | world snapshots: 2 s racy window, excluded cache directories; in sessions a 16 MB blob cap and a 200,000-file limit | `src/frond/world/store.py`, `src/frond/world/timeline.py` | snapshot time and store size in real workspaces. Measured 2026-11-03 on 11,897 files (239 MB): 13.6 s cold, 0.16 s warm, 96 MB stored. E0 measures the per-step cost in TB containers |
| K15 | resource guards (listed below) | `session.py`, `tools.py`, `steplog.py`, `world/timeline.py`, `tui/app.py` | which of them bind in practice |

K15's guards:
- attachments: 120k characters;
- stored output: 200k characters;
- world snapshots: files over 16 MB kept by signature only, and none past 200,000 files;
- step timeout: 600 s;
- LLM calls: 80 per turn, 40 per sub-agent;
- preview limits: 20k, 24k, 12k and 6k for the main agent; 8k, 8k and 16k for sub-agents;
- mentions: 400 kB.

## Entries carried over from `open-items.md`

| ID | Item | Status | Resolution |
|---|---|---|---|
| P0 | Live pilot | closed | became E0 |
| P1 | Confine the REPL worker and mark the user's messages | closed | 3c188c9 |
| P2 | Undo leaves later edits alone | closed | superseded by B4 (revert by merge) |
| P3 | Paired comparison against Codex | closed | superseded by E1 and E11 (D21) |
| P4 | Sandbox the main agent's commands | deferred | daily-driver work (D16); see R6 |
| P5 | Scopes as savepoints | closed | became B9 |
| P6a | Back up state outside the workspace before known commands | deferred | daily-driver work (D16); [RegretBench](https://arxiv.org/abs/2610.28934) |
| P6b | DSPy startup check | closed | became B11 |
| I1 | ACP support | closed | D25 |
| I2 | Upstream the layout and hooks to DSPy | deferred | until E6 has results |
| I3 | Devin's findings | closed | became REQ-3 |
| I4 | Redact secrets in persisted logs | closed | became B12 |
| I5 | "esc stops the command" hint | deferred | daily-driver UX |
| I6 | Narrowing hint after truncation | closed | became B14 |
| I7 | Inline rendering option | deferred | daily-driver UX (D03) |
| I8 | Stale default model IDs | closed | Anthropic: D24; the rest became Q1 |
| I9 | GPT-5.4-mini `\n` | closed | became Q2 |
| I10 | `plan()` ablation | closed | became E8 |
| I11 | Self-improvement with a regression gate | closed | became E7 |
| I12 | Load the rules at launch | closed | D18: root `CLAUDE.md` |
| I13 | Landlock-only environment leak | closed | became G1 |
| PR2 | PR #2 | closed | merged as 29e00ab |
| PR3 | PR #3 | closed | merged as 376dd3e |
