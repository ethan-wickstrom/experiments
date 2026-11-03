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
| REQ-1 | An Anthropic API key in this cloud environment, with a $100 spend cap for now | `ANTHROPIC_API_KEY` set as an environment secret, and frond completes one TB 4.0 task | open, asked 2026-11-03 | Unblocks E0 (estimated $45–75: 30 Opus 5.5 runs plus model calibration), then V1, V2, V4 and R8. The full program is estimated at $2–6k and will be re-estimated from E0. Screening on a cheaper model (`research.md`) cuts it |
| REQ-2 | Docker or Daytona for benchmark runs | Harbor runs a TB 4.0 task | closed: not needed | `dockerd` runs in the VM (D23); oracle run passed 2026-11-03 |
| REQ-3 | Devin's three security findings on PR #2, which Devin did not post | each copied here, then fixed or declined | open, low priority | needs the owner's Devin account (was I3) |

## Experiments

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| E0 | Pilot (was P0): 10 TB 4.0 tasks × 3 trials on Opus 5.5, plus 10 × 1 on Sonnet 5.5 and Haiku 5.5 to pick the screening model | report in `bench/results/` with per-call cache reads, protocol violations, failed edits, per-task variance, and the trials H1–H6 need | blocked: REQ-1, B1, B2 | `research.md` |
| E0a | Oracle sweep: Harbor's reference solutions on all 66 TB 4.0 tasks in this VM, so that infrastructure failures (TLS, resources, disk) are known before any model is blamed | pass list in `bench/results/` | in progress: third run, through `bench/matrix.py` (`bench/experiments/e0a-oracle.toml`), started 2026-11-03 09:00 UTC | needs no key. The first run's first 10 trials found G7 (2 TLS failures) and G8 (2 layer-extraction failures); the second found G20 (CPU requests above the VM's 4). Each was fixed or accepted, then the sweep restarted on the 56 tasks that fit |
| E1 | H1: RLM against ReAct, same tools | paired test per `research.md` | blocked: E0, B3, B8 | `research.md` |
| E2 | H2: fork k=3 with verifier selection | paired test; cost ratio | blocked: E0, B4, B6, B7 | `research.md` |
| E3 | H3: freshness marks | failed edits and stale actions per task, pass rate | blocked: E0 | `research.md`; the arms are `--freshness on` and `off` (B5) |
| E4 | H4: fold against summary on LHTB 2.0 | paired test | blocked: E0, B10 | `research.md` |
| E5 | H5: scopes as savepoints on LHTB 2.0 | paired test; tests A1–A4 and A10 | blocked: E0, B9 | `research.md` |
| E6 | H6: cache layout | cost and pass rate; tests A9 | blocked: E0, B3 | `research.md` |
| E7 | Offline prompt optimization (GEPA) with a regression gate (was I11) | gains hold on held-out tasks (A11) | blocked: E1–E6 infrastructure; a reward that does not reward shortcuts | [2607.14004](https://arxiv.org/abs/2607.14004) |
| E8 | `plan()` ablation (was I10) | pass rate with and without `plan()` | blocked: E0 | Amp [dropped its TODO tool](https://ampcode.com/news/todos-are-done) |
| E9 | Sub-model choice: Haiku 5.5 against the main model for `llm_query` | pass rate and cost | blocked: E0 | D24 |
| E10 | Effort sweep: medium, high, xhigh | pass rate and cost per solved task | blocked: E0, B1 | D24 |
| E11 | External references: Claude Code and Terminus 2 on Opus 5.5 | pass rate and cost on TB 4.0 | blocked: REQ-1 | D21 |
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
| B7 | Fork, select, merge: a `fork(options)` REPL function, a branch runner, verifier hooks, selection, merge | a scripted three-branch test that keeps the branch whose tests pass | open | H2 |
| B8 | ReAct arm: `dspy.ReAct` with frond's tools | runs the demo task headless | open | H1 |
| B9 | Scopes as savepoints (was P5), after N2 | collapse, rewind and cache-prefix tests | open | H5, D22 |
| B10 | Summary-compaction arm, rebuilt from the removed `_compact` | runs; the context-policy flag picks it | open | H4 |
| B11 | Pin DSPy and check at startup (was P6b) | a changed signature gives a clear startup error | open | R9 |
| B12 | Redact secrets from exported records before results are committed (was I4) | exported records hold no credential values from the environment | closed (this commit) | `agent/redact.py`: the values of credential-named variables (by name), common API key shapes and URL passwords are replaced in every `--export` file and in `-p` output, which Harbor stores and may upload; `tests/test_redact.py` |
| B13 | A TUI world view: branches as a live tree, with per-branch diffs and verifier status | headless render test | open | delight; follows B7 |
| B14 | The truncation note suggests how to narrow (was I6) | test checks the hint | open | [TurnCost](https://arxiv.org/abs/2610.15093): 76.9% against 44% |
| B15 | `scripts/dev-env.sh`: dockerd plus the Docker Hub mirror | runs and prints `docker info` | closed 362cc49 | D23; G10 fixed its handling of an existing `daemon.json` |
| B16 | Stop hook: committed, pushed and on `origin/main` before a turn ends | a dirty tree blocks once | closed 362cc49 | D19; G9 made it fail closed |
| B17 | Stop latency measured in the scripted harness (R4) | P95 ≤ 1 s, and no tool runs after the stop | open, low | R4 |

## Renames

| ID | Item | Check | Status | Resolution / source |
|---|---|---|---|---|
| N1 | `Compacted` → `Folded` (event and hook) | no `Compacted` or `compacted` identifiers remain; tests pass | open | design.md "Vocabulary" |
| N2 | `Record.scope` → `Record.agent`, before B9 | logs write `agent`, readers accept `scope`, and the Harbor adapter reads the new name | open | design.md "Vocabulary" |
| N3 | `Checkpoints` → absorbed into worlds (B4) | the class is gone | open | D22 |

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
| V2 | frond has never run a real Terminal-Bench task | E0 | blocked: REQ-1 | Harbor plus Docker verified with the oracle agent, and frond installs in a TB 4.0 container (install-only), 2026-11-03 |
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
| R7 | The agent can rewind context and workspace together | B4b, then B9 | open | the workspace half exists: every step-log record names its world (B4b). Rewinding the context with it is B9 |
| R8 | Most input is served from cache | E0 | blocked: REQ-1 | — |
| R9 | An incompatible DSPy fails at startup | B11 | open | — |
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
| G21 | The world store keeps every version of every file it has seen, for all of a workspace's sessions, and nothing removes old objects | a store past a size bound drops objects no session file or step record reaches | open, low | a mark-and-sweep from the session files' turn worlds and the step logs' worlds |
| G20 | 10 of TB 4.0's 66 tasks declare more than 4 CPUs or a GPU for their agent or verifier container, and Docker refuses to start them in this 4-CPU VM ("range of CPUs is from 0.01 to 4.00") | — | closed: accepted (this commit) | D28: the population is the 56 tasks that fit, keeping every task's declared limits; the list is `bench/datasets/terminal-bench@4.0.0-exceeds-4cpu-nogpu.txt`. Three more ask for 16 GB of memory, which Docker accepts; they risk only running out of memory. A bigger VM would bring the 10 back |
| G19 | `GitSnapshots`: a nested workspace's objects path, CRLF and filter conversions, and file-to-directory changes in undo (PR #3) | — | closed (this commit) | B4b deletes `GitSnapshots` in favour of worlds, which store raw bytes and handle kind changes (`test_world`) |

## Assumptions to test

| ID | Item | Tested by | Status |
|---|---|---|---|
| A1 | The model opens and closes scopes without being told each time | E5 | blocked |
| A2 | Collapsing a closed scope hides nothing needed later | E5: `history_step` calls on collapsed steps | blocked |
| A3 | Listing stale names after an abandon keeps the model off discarded values | E5, B9 tests | blocked |
| A4 | Rewinds need a verifier signal | E5: split by whether the task has tests | blocked |
| A5 | TB turns rarely reach the fold budget, so long-horizon sets are needed for H4 and H5 | E0 | blocked |
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
