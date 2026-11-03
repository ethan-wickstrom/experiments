# Decisions

Every decision frond rests on: what was chosen, what was rejected and why, and where it lives. The log is append-only. A reversed decision gets a new entry, and the old one is marked superseded rather than deleted. IDs are stable, and `ledger.md` and `design.md` cite them. Decisions D01–D21 were made in the first session (2026-11-02 and 2026-11-03). In that session the brief imposed two constraints: C1, `dspy.RLM` at the center; and C2, Python, DSPy and the CPython standard library only. Since the owner's standing orders of 2026-11-03, the agent owns every decision (D16).

## D01 · RLM at the center (2026-11-02, active)
- Decision: every step is a `dspy.RLM` iteration. The model writes Python in a persistent REPL, and the tools are functions in that REPL.
- Rejected: JSON tool calling (`dspy.ReAct`, native function calling). C1 required the RLM, and the evidence gave no reason to break it: code actions matched or beat JSON for 11 of 14 models ([2608.06370](https://arxiv.org/abs/2608.06370)), and pass rates stayed within 3 points across action interfaces ([2607.10569](https://arxiv.org/abs/2607.10569)). The rejected design survives as experiment arm H1, because it is the most direct test of the RLM premise.
- Where: `src/frond/agent/rlm.py`.

## D02 · frond's own CPython REPL worker (2026-11-02, active)
- Decision: a persistent CPython subprocess speaking JSON lines, with tools executed host-side over RPC.
- Rejected:
  - DSPy's Deno/Pyodide interpreter: it needs Deno (outside C2) and cannot import the project's own packages;
  - E2B or Modal interpreters: network round trips and third-party accounts.
- Consequence: frond must confine the worker itself (D13).
- Where: `src/frond/agent/repl.py`, `src/frond/agent/_worker.py`.

## D03 · Standard-library TUI on the alternate screen (2026-11-02, active)
- Decision: raw-mode input, a diffing cell renderer, themes from OSC 11, drawn on the alternate screen.
- Rejected:
  - Textual, rich and prompt_toolkit: outside C2;
  - inline rendering into scrollback: deferred, ledger I7.
- Where: `src/frond/tui/`.

## D04 · Approvals by policy; the audit hook is a guard rail (2026-11-02, active)
- Decision: risky commands, recursive deletes and writes outside the workspace ask for approval. A PEP 578 audit hook steers REPL code onto the tools.
- Rejected:
  - approving everything: approval fatigue;
  - trusting the hook as a boundary: [PEP 578](https://peps.python.org/pep-0578/) says it is not a sandbox (see D13).

## D05 · Per-turn undo journal for tool edits (2026-11-02, superseded by D10, then D22)
- Decision: journal each path's original bytes, mode and links before frond's tools change it.
- Superseded: it could not see shell commands' changes (D10) and is unsafe under concurrent edits; worlds replace it (D22).

## D06 · Read-only agents confined by the OS (2026-11-03, active, 5837329)
- Decision: read-only agents' commands run in `_sandbox.py`. The ladder is user and mount namespaces with every mount read-only and no network, then Landlock ABI ≥ 3, then Seatbelt on macOS. With none, there is no shell.
- Rejected:
  - command-text patterns (`MUTATING_COMMAND`): they cannot see effects;
  - a read-only command allowlist: it breaks running tests;
  - `bwrap`: not in C2 and not installed everywhere.

## D07 · Cache-friendly prompt layout (2026-11-03, active)
- Decision: each step is an assistant/user message pair, the cache breakpoint sits on the latest reply, and per-step fields come last.
- Rejected:
  - DSPy's single growing message: never cached on Anthropic;
  - system-only cache marks: lose the history;
  - a 1-hour TTL by default: open as A7.
- Evidence: the cached share of a 20-step turn rose from 20% to 85% in a simulator of Anthropic's rules (`tests/test_caching.py`); cost follows turn count ([TurnCost](https://arxiv.org/abs/2610.15093)).

## D08 · Lossless step log with index folds (2026-11-03, active)
- Decision: an append-only log of every message, step and answer, searchable from the REPL. Over budget, early steps fold into one index line each.
- Rejected:
  - LLM summaries: [Scroll](https://arxiv.org/abs/2608.21690) scored 73.1% against 19.9% for summaries. Summaries also lose how-to-work instructions ([2610.31778](https://arxiv.org/abs/2610.31778)), and 83% of failures traced to summary entries ([2610.20927](https://arxiv.org/abs/2610.20927));
  - context the model edits itself: injection risk and compute-only gains ([2609.37725](https://arxiv.org/abs/2609.37725));
  - provider-side compaction: opaque and provider-specific.

## D09 · Steering (2026-11-03, active)
- Decision:
  - keys: Enter sends into the running turn, Tab queues, and Esc, Ctrl+C or the button stop;
  - delivery: messages arrive at step boundaries and are restated at the end of the prompt.
- Rejected:
  - stop-only (the brief's literal Enter→stop): it loses corrections, and corrections raised success from 40.3% to 64.1% ([FeatureLoop](https://arxiv.org/abs/2610.35488));
  - aborting the in-flight call: it wastes the call;
  - Enter on an empty prompt stops: accidental halts. This closes ledger A8.

## D10 · Shell-aware undo via private git snapshots (2026-11-03, active until D22 lands)
- Decision: bracket each foreground command with tree snapshots in a private index and object directory, using the repository's objects as alternates.
- Rejected:
  - ghost commits: they write into the user's repository, and Codex abandoned them in v0.126;
  - overlay copy-on-write: per the [kernel docs](https://docs.kernel.org/filesystems/overlayfs.html), changing the lower layer while it is mounted is undefined;
  - btrfs or APFS snapshots: not portable.

## D11 · Harbor installed-agent adapter and `--export` (2026-11-03, active)
- Rejected: a custom runner. Terminal-Bench's own harness is [Harbor](https://harborframework.com), which leaderboards use, and it also runs long-horizon and SWE datasets.

## D12 · Recursive deletes ask (2026-11-03, active)
- Source: a Codex review finding on PR #2.

## D13 · A confined, credential-free REPL worker (2026-11-03, active, 3c188c9)
- Decision:
  - the worker starts in the sandbox with a shared TMPDIR;
  - credentials are scrubbed from its environment;
  - the audit hook refuses sockets, name lookups and urllib;
  - where no sandbox works, an unconfined fallback runs, with a notice.
- Rejected:
  - the hook alone: not a boundary;
  - scrubbing alone: `/proc/<pid>/environ` stays readable;
  - DSPy's WASM interpreter: see D02;
  - refusing to run unconfined: the REPL is essential.

## D14 · A provenance marker on the user's messages (2026-11-03, active, 3c188c9)
- Decision:
  - each session tags the user's mid-turn messages with a random marker and strips that marker from all other text;
  - steer and fold entries are distinct classes.
- Rejected:
  - English framing: forgeable;
  - a separate message per steer: tool output shares the user role;
  - [Spotlighting](https://arxiv.org/abs/2403.14720) marks on all output: they leak into the exact strings copied into `edit()`;
  - native tool-call rendering by default: it changes what the model imitates; it stays an experiment (A13).

## D15 · Merge commits on main (2026-11-03, active)
- Rejected: squash and rebase merges. They create new hashes, and the ledger cites the originals.

## D16 · frond is a research vehicle; the agent owns the repository (2026-11-03, active)
- Decision: per the owner's standing orders, the agent makes every decision (architecture, scope, priorities, experiments, naming, merging) and asks the owner only for what it cannot get itself: API keys, money, accounts, infrastructure.
- The work order follows the research question, not daily-driver hardening.
- Rejected: the daily-driver order (P2, P4, P6a first). It hardens frond for daily use without testing any hypothesis; that work is deferred in the ledger.

## D17 · No PR watching; the agent merges its own PRs (2026-11-03, active)
- Decision: branch, push, open a PR, run the local checks, merge. A PR is a record, not a review gate.
- Rejected: waiting on Codex or Devin bot reviews. Nobody acts on them, and the local test suite is the gate.

## D18 · State lives in the repository (2026-11-03, active)
- Decision:
  - `CLAUDE.md` at the repository root states the mission, the autonomy and how to resume, and imports only `frond/docs/now.md`;
  - `frond/docs/ledger.md` is the one ledger of everything open and closed;
  - this file records decisions;
  - `frond/docs/design.md` holds the analysis and traceability;
  - `frond/docs/research.md` holds the experiment protocol.
- Rejected:
  - importing the full ledger: about 430 lines in every session's context;
  - `frond/CLAUDE.md`: a nested CLAUDE.md loads only once a file under `frond/` is read;
  - auto memory and task lists: they live in the VM;
  - the chat: compaction loses it (W8).

## D19 · A Stop hook enforces "committed, pushed, on main" (2026-11-03, active)
- Decision: `.claude/hooks/stop_guard.py` blocks the end of a turn once when the tree is dirty, commits are unpushed, or HEAD is not on `origin/main`.
- Rejected:
  - a written rule alone: unenforced rules decay;
  - blocking without limit: risks a loop. `stop_hook_active` limits it to one block per stop.

## D20 · Terminal-Bench 4.0.0 is the primary benchmark (2026-11-03, active)
- Decision: `terminal-bench/terminal-bench@4.0.0` (66 tasks, released 2026-08-26), pinned. Long-horizon experiments use `silrlab/long-horizon-terminal-bench-2.0` (77 tasks) from the Harbor hub.
- Rejected:
  - TB 2.1: superseded, and its top scores sit near 88–93%, which leaves little headroom to detect differences;
  - TB 3.0: TB 4.0 recalibrated task resources and cut timeouts and errors ([announcement](https://www.tbench.ai/news/terminal-bench-4-0));
  - SWE-bench Verified: contaminated, and it does not test terminal work.
- Reference points: about 65% for Claude Opus 5.5 under Claude Code and mini-SWE-agent ([Vals AI](https://www.vals.ai/benchmarks/terminal-bench-4), [Snorkel](https://snorkel.ai/leaderboard/terminal-bench/)).

## D21 · Ablations inside frond first; external baselines second (2026-11-03, active)
- Decision:
  - hypotheses are tested by arms inside frond on the same model (research.md);
  - the external references are Claude Code and Terminus 2 on the same Claude model, which needs one API key.
- Rejected: frond against Codex CLI as the primary instrument. It confounds harness, prompts, tools and model provider, and needs a second provider. Codex stays an optional later arm.

## D22 · Worlds: content-addressed, versioned state as frond's core (2026-11-03, active)
- Decision:
  - the agent's state becomes a persistent DAG of worlds: workspace trees in a content-addressed store, REPL images, observations and steps (design.md, "Worlds");
  - undo is a revert by three-way merge, rewind and fork are moves in the DAG, and every prompt is a pure function of a path.
- Rejected:
  - extending the journal plus git snapshots: two mechanisms, git-only, no ignored files, unsafe under concurrent edits;
  - git or jj as the store: often absent in task containers, so git stays an optional accelerator;
  - overlayfs branches: default Docker's seccomp profile blocks `mount`.
- Evidence:
  - [AgentRewind](https://arxiv.org/abs/2608.14380): environment and context rewound together reached 87.8%, against 62.2% for no rewind and 43.9% for the context alone;
  - [Spine](https://arxiv.org/abs/2610.37224) and [CarryOn](https://arxiv.org/abs/2610.18784): structure beats retention.

## D23 · Docker in the cloud VM, with a registry mirror (2026-11-03, active)
- Decision: `dockerd` runs in the session VM, with Docker Hub pulls served from `mirror.gcr.io` because Docker Hub rate-limits the shared egress IP (HTTP 429). `frond/scripts/dev-env.sh` sets this up.
- Rejected: asking the owner for Daytona, which costs an account and money, when local Docker works. Limits: 4 CPUs, 15 GB RAM and 29 GB disk per session, so runs execute one or two at a time and prune images.

## D24 · Default models and research model (2026-11-03, active)
- Decision:
  - the main model is `claude-opus-5-5` ($4/$20 per MTok, $0.20 cache reads), Anthropic's current default model and the model on the TB 4.0 leaderboards;
  - sub-queries use `claude-haiku-5-5` ($0.10/$0.50);
  - Sonnet 5.5 ($2/$10) is the cost-sensitive secondary arm.
- Rejected: Sonnet 5.5 as the primary model, because external references are on Opus 5.5.
- Constraint learned: Claude 5.5 models reject `temperature`, `top_p`, `top_k` and disabled thinking with HTTP 400. Ledger B1 verifies that frond sends none of them.

## D25 · Earlier skipped ideas, kept closed (2026-11-03, active)

Each stays closed unless new evidence reopens it:
- No copy of the RLM loop inside frond: it would break C1 as written. With D16, C1 is now a choice, and H1 tests it.
- No recursion deeper than one level: two levels did worse than one ([RLM reproduction](https://arxiv.org/abs/2603.02615)).
- No Prime Agent-style background sub-agents: they paid off in multi-day runs, not interactive edits.
- No routing of steps to cheaper models: it raised cost in half of TurnCost's settings.
- No StateHarness diagnostic sessions or CarryOn compiler and grounder: extra model calls. Worlds give their benefits structurally (D22).
- No online self-editing of prompts: nothing gates it. Offline optimization with a regression gate is E7.
- No Windows support: the TUI depends on termios.
- No macOS work in the research program: the program runs on Linux containers. Seatbelt stays untested (V3, closed).
- No ACP support for now: it serves daily-driver IDE use, not the research question. Reopen after the research program.
- PR #2's mistaken commit message stays as it is: it credits a mouse-input fix to the wrong commit, and rewriting pushed history is destructive.

## D26 · Explicit reasoning effort; keep the native route behind the public endpoint (2026-11-03, active)
- Decision:
  - frond sets the main model's effort to `high` (`--effort`, which the Harbor adapter passes through), and leaves sub-calls at the model's default;
  - when `<PREFIX>_BASE_URL` or `_API_BASE` names the provider's own public endpoint, as hosted sessions set `ANTHROPIC_BASE_URL=https://api.anthropic.com`, frond unsets it so DSPy keeps its native engine, with prompt caching and effort;
  - for a real gateway, frond keeps the variable and turns prompt caching off instead of failing.
- Rejected:
  - effort `medium`, Opus 5.5's default: the Claude API guidance asks for at least `high` on intelligence-sensitive work, and E10 sweeps effort;
  - `xhigh` by default: the cost has not been measured;
  - unsetting every base URL: breaks real gateways;
  - declaring a provider through `dspy.lm15.register_provider`: more DSPy-internal surface for the same effect.
- Evidence: without the fix, every call from this VM fails with "requires LiteLLM, which has no prompt_cache bridge" (ledger G4). `tests/test_lm.py` captures the exact payload.

## D27 · Trust the egress CA at the environment layer, for every container process (2026-11-03, active)
- Decision: a Docker Compose overlay (`bench/compose/egress-ca.yaml`) mounts the host's CA bundle read-only into each task's `main` service and points `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`, `PIP_CERT`, `NODE_EXTRA_CA_CERTS`, `GIT_SSL_CAINFO` and `CARGO_HTTP_CAINFO` at it. Every run in this VM uses it; the Harbor adapter's own CA upload (G6) is removed.
- Why: the VM re-terminates outbound TLS. The adapter's fix covered frond's processes only, so the oracle, other agents (the Claude Code and Terminus 2 references of D21) and the task's own commands still failed. A fault that depends on the host belongs in the host's environment layer, where it is fixed once for every agent; in the adapter it would have to be repeated per agent, and the arms would differ in network access.
- Rejected:
  - installing the CA into each image's system store (`update-ca-certificates`): needs a command per image and per distribution, and changes the image the task ships;
  - keeping the adapter's copy as well: two mechanisms for one fault;
  - an unintercepted network for the VM: not available to this session.
- Effect on measurement: all arms see the same environment, so paired comparisons are unaffected. Absolute pass rates in this VM now match a normal network for tasks whose `main` container reaches the internet. TB 4.0's separate verifier containers do not get the overlay; E0a shows whether any of them needs the network.
- Evidence: with the overlay, the oracle passed `fin-saccr-rwa` (24/24 tests) and `satb-audio-transcription` (40/40), which it failed without it (ledger G7).

## D28 · Pre-registered specs, sequential confidence sequences, and a fixed task population (2026-11-03, active)
- Decision:
  - an experiment is a TOML spec in `bench/experiments/`, committed before its first trial: tasks, a seeded run order, batches, arms, trials, and claims with their tests and margins. `bench/matrix.py` runs it and `bench/analyze.py` evaluates it from the same file;
  - a claim holds when its one-sided p-value, Holm-adjusted across the spec's claims, is below alpha. The exact Wilcoxon signed-rank test serves pass-rate claims, and a bootstrap test serves cost-ratio claims;
  - between batches, pass-rate claims are read through betting confidence sequences (Waudby-Smith and Ramdas), which allow stopping at any batch without inflating error; specs opt in with `stop_early`;
  - arms alternate order across batches (ABBA); only the first k valid trials of a task count; trials whose environment failed before the agent started are reported and not scored; Harbor retries only those;
  - cost is computed per model call from `bench/prices.toml`, because frond's main and sub-models have different prices;
  - the task population is the TB 4.0 tasks that start in this VM with their declared resources: 56 of 66 (G20).
- Rejected:
  - Harbor's default retries: they cover `NonZeroAgentExitCodeError`, and a retried trial overwrites the first attempt, so an agent's crash could be replaced by a later success;
  - reading a fixed-size test after every batch, as `research.md` planned: it inflates the error rate, which the protocol had accepted as a cost;
  - group-sequential alpha spending (O'Brien–Fleming): it needs the number of looks fixed in advance and normal approximations, which 22-task batches of 0/1 outcomes do not justify;
  - `--cpus ignore` to run all 66 tasks: it changes every task's resources, not only the 10 that do not fit; excluding the 10 keeps the other 56 as their authors specified;
  - SciPy for the statistics: the bench stays standard-library-only, like frond, and the exact tests are short;
  - Harbor's own `cost_usd` for frond: it is not filled for installed agents, and one price per run cannot separate main and sub-model calls.
- Evidence: `tests/test_bench.py` checks the Wilcoxon p-values against enumeration of every sign assignment, the confidence sequence's coverage by simulation, the ABBA plan, the retry list, and an analysis of synthetic Harbor jobs.

## D29 · Undo, diffs and command tracking all come from worlds; the tools keep no journal (2026-11-03, active)
- Decision:
  - frond snapshots the workspace when a turn starts and after every step (`world/timeline.py`); each step-log record names its world, and each turn record its first and last;
  - `/undo` reverts the latest turn that changed files and is not yet undone, by three-way merge against the directory as it is now. Later edits by anyone survive; same-line conflicts are kept as they are and reported;
  - a turn's net change is the difference between its first and last worlds (`/diff`, `TurnRecord.files`). A command's diffs come from snapshots around it, in any directory;
  - in a git work tree, untracked paths git ignores are left out. Within a turn the ignored set only takes in paths that did not exist at the previous snapshot. A turn that moved HEAD is left to git;
  - the store lives beside the workspace's sessions (private, 0700), so `/undo` works after `--continue`. Files over 16 MB are tracked by signature only; a workspace past 200,000 files is not snapshotted, and undo says so;
  - `agent/checkpoints.py` and `agent/snapshots.py` are deleted.
- Why: a journal kept by each tool misses whatever does not go through a tool: shell commands outside git, background jobs, formatters. It also needs one code path per mutation kind (moves, links, deleted trees), each a source of bugs; PR #3 found three in `GitSnapshots`. A snapshot sees every change, whatever made it. The revert gives R3, which the journal's restore could not. Every step having a world is the substrate for rewind (R7, B9) and fork (B7).
- Rejected:
  - keeping the journal and adding snapshots only for commands: two mechanisms, and still no R3;
  - git-based snapshots (`GitSnapshots`): need git, write a private index, and mishandled nested workspaces, CRLF filters and file-to-directory changes (G19);
  - snapshotting only at turn boundaries: cheaper, but no world per step for rewind and fork. A warm snapshot costs 0.16 s on 12k files (K16), small beside a model call;
  - a Python `.gitignore` matcher: a second implementation of git's rules (nesting, negation, anchoring); asking git is exact;
  - undoing a turn that committed, file by file: it would leave HEAD at a commit whose content the working tree no longer holds.
- Evidence: `tests/test_command_undo.py` (commands with and without git, ignored paths, un-ignoring mid-turn, a commit left to git, a background job, a concurrent edit kept, same-line conflicts reported, the net diff, a world per step, the file limit) and the undo tests in `test_regressions` and `test_agent` pass on worlds.

## D30 · Freshness: per-file observations, a stale-read field, and compare-and-swap writes (2026-11-03, active)
- Decision:
  - every `view` and `read` by the main agent records an observation: the path, the blob id of the bytes seen (`world.object_id`), and the step. Observations last for the turn;
  - before each step, the prompt's volatile `stale_reads` field names the reads whose files changed since;
  - a whole-file `write`, a `delete` or a patch's delete over a stale read is refused until the model reads the file again. A stale `edit` or patch update applies where its old text still matches, and the result says the file had changed. The model's own changes keep its observation fresh, unless it was stale already;
  - `--freshness off` removes the field, the refusals and the notes, and keeps the count (`stale_actions`): the H3 control arm;
  - sub-agents record nothing: their reads inform their reports, not the main agent's picture.
- Why: an edit made from an out-of-date picture either fails (a failed edit, the H3 metric) or, worse, silently overwrites a change the model never saw: a formatter's, a background job's, the user's. Marking staleness addresses the first; compare-and-swap on whole-file writes removes the second outright, as git refuses to overwrite unmerged work.
- Rejected:
  - observations per line range (`view` shows a window): finer, but a change outside the window can still invalidate the model's plan, and file level is one dictionary lookup;
  - warning on stale writes instead of refusing: the overwrite has already happened by the time the model reads the warning;
  - a `force=True` parameter for writes: it would change the tool's documented signature in both arms; reading the file again is the one way through;
  - tracking reads made through `sh("cat …")`: parsing shell commands is unreliable, and `view`/`read` are what the prompt directs the model to use;
  - keeping observations across turns: earlier turns reach the prompt only as summaries, so their reads are not the model's current picture;
  - attributing each change to a step ("changed at step 7 by your sed"): needs a world lookup per stale path per step; deferred until E3 shows whether the bare mark helps.
- Evidence: `tests/test_freshness.py` (a read going stale and cleared by a new read in the prompt; refusal and recovery; a stale edit's note; a patch refused before writing anything; the off arm's counts).

