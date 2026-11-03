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

## D17 · No PR watching; the agent merges its own PRs (2026-11-03, active; its rejection of waiting for review bots superseded by D40)
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

## D31 · The REPL forks by os.fork in the worker, with its channel passed over SCM_RIGHTS (2026-11-03, active)
- Decision:
  - each worker starts with one end of a UNIX socketpair (FROND_FORK_FD). To fork, the host sends `fork` on the protocol and a fresh socket over that pair (`socket.send_fds`); the idle worker calls `os.fork()`;
  - the copy calls `setsid`, so the host can interrupt and kill it alone. It swaps its inherited stdin and protocol descriptors for /dev/null at the OS level, takes a scratch directory under the shared one, starts its own reader thread, and says `ready` on the new socket;
  - the original reaps its copies (SIGCHLD); user code cannot start processes in the worker, so every child is a copy. Only originals fork;
  - host side, `ReplSession.fork()` returns a session over a Popen look-alike (`_Forked`); the copy calls the same tools unless it is given others.
- Why: H2's branches must start from the same REPL state at the cost of a fork, not a replay. `os.fork` copies the namespace by copy-on-write in milliseconds, whatever it holds: imports, loaded data, closures. Passing the channel as a descriptor lets the copy talk to the host directly. The sandbox (user, mount and network namespaces, or Landlock) is inherited by construction, and there is no PID namespace, so the copy's pid is valid on the host.
- Rejected:
  - replaying the steps' code into a fresh worker: re-runs side effects and costs the steps' time again;
  - pickling the namespace (`dill`): fails on modules, sockets, generators, locks and C objects, and is not standard library;
  - CRIU or another checkpoint/restore tool: privileges and an external dependency;
  - letting the copy keep the original's stdin and stdout: the host would see the original's stream stay open after it died, and the two could interleave writes;
  - closing the inherited Python file objects in the copy: the reader thread that did not survive the fork may hold their buffer locks, so the copy replaces the descriptors under them instead.
- Caveat: forking a process with threads is only safe when no other thread holds a lock the copy needs. The worker forks only between steps, when user threads should have ended (it warns when they have not), and the copy touches none of the objects the reader thread held.
- Evidence: `tests/test_fork.py`: namespace kept, then independent; tools reach the host; scratch of its own; interrupt and shutdown affect only the copy, which is reaped; copies do not fork again; the containment checks (no write, no connection) pass inside a copy under namespaces and Landlock.

## D32 · FORK: model-requested branches, run in turn from the world at FORK, kept by the model's own check (2026-11-03, active)
- Decision:
  - `FORK(options, check=None, steps=8)` is a REPL built-in, like SUBMIT, defined only when `--fork` is 2 or more. Calling it ends the step;
  - for each option, frond checks out the world at FORK, forks the main REPL (B6), and runs a branch of the agent for at most `steps` steps. The branch continues the main history, with a note naming its option as the FORK step's output, and has its own observations, jobs and step-log scope;
  - `check`, a shell command, runs on each branch's world; exit 0 passes. Without a check, a branch that called SUBMIT passes. The passing branch with the fewest steps is kept (a submitted one first), and its world is checked out; with none passing, the world at FORK is. The FORK step's output reports every branch;
  - the main REPL stays as it was at FORK; branches cannot fork again; `--fork` defaults to 1 (off) until E2.
- Why: H2 asks whether exploring alternatives and keeping what a verifier prefers raises pass rate per dollar. The model knows when it faces a real choice, and usually knows a command that tells which option worked. Continuing the same history makes every branch's prompt share the main prompt's prefix through the FORK step, so each branch's context costs cache reads (`design.md`, "Views are compiled").
- Rejected:
  - branches in parallel, each in a copy of the directory: copies lack the caches and environments worlds exclude (`.venv`, `node_modules`), so checks fail for the wrong reason; and parallel branches race for the VM's 4 CPUs. Running in turn costs wall-clock time, which the program does not measure;
  - continuing the main REPL from the winner's fork: the copy cannot fork again (D31), so later FORKs would fail; the model recomputes what it needs, as the report says;
  - an LLM judge to choose between branches: another model call per branch, and a weaker signal than a check;
  - merging several passing branches by three-way merge: their changes overlap more often than not; one branch is kept, as best-of-k sampling does;
  - frond deciding when to fork (on every failed check, say): the model sees the choice, frond does not; E2 measures whether the model uses FORK well.
- Evidence: `tests/test_branches.py`: the passing branch's world is kept and its REPL changes are not; every branch starts from the world at FORK; none passing restores it; branch prompts equal the main prompt through the FORK step; FORK is absent when off; too many options is an error the model sees; branch calls are tagged and fork outcomes exported.

## D33 · The tool-calling arm is an action space of frond's own loop, not dspy.ReAct (2026-11-03, active)
- Decision:
  - `--arm react` switches FrondRLM to a tools action space. Each step the model writes `reasoning`, `tool` and `args` (a JSON object); frond calls that one tool host-side and shows its result as the step's output; `submit` ends the turn;
  - everything else is the RLM arm's: the tools and their documentation, the instructions (rewritten without the REPL, `prompts.TOOL_AGENT_INSTRUCTIONS`), the turns layout with the latest reply cache-marked, freshness, folding, steering, the step log and the exports. The inputs are shown as text, clipped like the REPL's previews;
  - FORK and `llm_query` exist only in the RLM arm: both need code;
  - E1 caps the tools arm at 100 steps and the RLM arm at 40: a tools step is a single call, and the comparison is pass rate and cost, not steps.
- Why: H1 asks whether the action space (code in a persistent REPL against single JSON tool calls) changes pass rate per dollar. Holding everything else fixed is what lets E1 attribute a difference to the action space.
- Rejected:
  - `dspy.ReAct`: it re-renders the whole trajectory into one user message each step, so it loses prompt caching (H6's control condition), and it describes tools in its own format. A difference would mix action space with layout;
  - the provider's native tool calling: a second difference (the API's tool_use blocks) beside the action space; E12 studies native rendering on its own;
  - equal step caps: they would test a budget, not the action space; the step caps are pre-registered in E1's spec, and cost is measured either way.
- Evidence: `tests/test_tools_arm.py`: a turn of single calls edits, checks and answers; past calls appear as turns in the call format; no code field or REPL variables reach the prompt; unknown tools and bad arguments come back as errors; the cache mark lands on the latest call.

## D34 · H4's control arm summarises with the main model and offers no way back (2026-11-03, active; its rule on the user's messages superseded by D38)
- Decision:
  - `--context summary` keeps the fold's trigger and budget, so compaction happens at the same points in both arms. It replaces the early steps, any earlier summary and the user's mid-turn messages among them with a summary the main model writes (`prompts.Compaction`), escaped like any tool-derived text;
  - in that arm `history_search` and `history_step` are not offered, and no index points back to the steps. The step log still records everything for the export;
  - if the summary call fails, a clipped trace of the steps stands in, so a turn never loses its context entirely;
  - both arms count compactions, and the summary arm counts its summary calls (`metrics.json`).
- Why: H4 compares frond's lossless fold with what products ship: summarise and continue (Claude Code's compaction, Codex's). The comparison is fair only if the summary arm gets the best version of that: the main model, a prompt that asks to keep the user's constraints and every concrete fact, and compaction at the same moments.
- Rejected:
  - summarising with the sub-model: cheaper, but it would handicap the control arm;
  - keeping the history tools in the summary arm: that would be the fold with a summary added, not the conventional baseline;
  - keeping the user's mid-turn messages verbatim outside the summary: frond's provenance design, not the products', and the known failure the fold exists to fix (`steplog.py`, arXiv 2610.31778).
- Evidence: `tests/test_summary_arm.py`: past the budget the summary replaces early steps, with no index and no history tools, and the summary call is counted; the fold arm keeps the index and the tools.

## D35 · Scopes are tools whose effect lands on the next step's history (2026-11-03, active)
- Decision:
  - `open_scope(goal)` records a savepoint: the step, the world and the REPL's names digest. `close_scope(result)` and `abandon_scope(reason)` end the innermost scope; the loop applies the change to the history at the start of the next step;
  - closing replaces the scope's entries (the tail of the history) with one entry, goal and result, pointing at the steps' log sequence numbers; abandoning reverts the scope's workspace changes with `Timeline.revert` (a three-way merge), cuts the entries away, and adds a note with the reason, what was reverted, what was kept, and the REPL names changed since, now stale;
  - the user's messages from inside a scope are kept; scopes end with the turn; a FORK branch cannot open or end the main line's scopes;
  - a volatile `open_scopes` field lists the open scopes; `--scopes` defaults to off until E5; counts go to `metrics.json` (A1).
- Why: H5 asks whether letting the model fold its own finished subtasks, and rewind failed ones, beats the budget fold on long tasks. A closed scope is always the tail, so collapsing it leaves the cached prefix intact, unlike the budget fold, which rewrites from its index onward. AgentRewind found the note on a failed attempt necessary (51.2% without it), so the reason is kept. Abandoning needs the workspace and the context rewound together, which worlds (D29) provide; that also meets R7.
- Rejected:
  - REPL built-ins (like SUBMIT) instead of tools: scopes must work in the tools arm too (H1 and H5 cross);
  - rewinding the REPL by forking it at each open: a copy cannot fork again (D31), so FORK would stop working after the first abandon, and every open would cost a process;
  - restoring the world at open by checkout: it would discard edits made by others meanwhile; the revert keeps them;
  - collapsing the user's messages with the scope: their words are never shortened (D14).
- Evidence: `tests/test_scopes.py`: a closed scope becomes goal and result while its steps stay in the log; an abandoned scope reverts the workspace, cuts the context, notes the reason and the stale names; the prefix before a scope is unchanged; ending a scope that is not open is an error the model sees; with scopes off there are no tools or field.

## D36 · Pin DSPy exactly and check its internals at startup (2026-11-03, active)
- Decision: pyproject requires `dspy==3.4.1`. At startup the CLI checks the private DSPy parts frond overrides or calls (`RLM._execute_iteration` and five more methods, `_LLMCallBudget`, `_strip_code_fences`, the adapter helper, `select_backend`, `CacheConfig`): each must exist, and the overridden methods must keep their parameter names. Otherwise frond exits with status 2 and names what changed.
- Why: frond's loop is a subclass of `dspy.RLM` that overrides private methods; a patch release could change one and frond would run wrongly instead of failing (R9).
- Rejected: a version range (`>=3.4.1,<3.5`): a patch release may change private methods; vendoring DSPy: frond is built on DSPy, and copying its RLM would break C1 (D25); checking only the version string: it says nothing about what changed.
- Evidence: `tests/test_compat.py`.

## D37 · Collect the world store by mark-and-sweep from recent sessions' worlds (2026-11-03, active)
- Decision: when a workspace's store passes 2 GB, frond collects it in the background at startup. The roots are every world named by the session files and step logs of sessions touched in the last 30 days; everything reachable from them stays, and so does every object used in the last hour. `Store.put` refreshes the timestamp of an object it finds already stored, and each turn's first world goes into the step log as the turn starts, so an object a running session depends on is always either reachable or recent.
- Why: the store is shared by all of a workspace's sessions so that `/undo` survives `--continue` (D29), and without collection it only grows (G21).
- Rejected: reference counting (every snapshot would write counts for thousands of entries); deleting whole old sessions' stores (objects are shared across sessions by design); collecting while a session snapshots without the in-use rule (a reused old blob could vanish from under a new tree); a size bound that drops reachable objects (undo history within 30 days is kept whole).
- Evidence: `tests/test_world.py::CollectionTest`.

## D38 · The summary arm keeps the user's words verbatim, and every loop of an arm follows its context policy (2026-11-03, active)
- Decision:
  - under `--context summary`, the user's mid-turn messages among the compacted steps stay verbatim and in order, ahead of the summary; the summariser still sees them. Earlier summaries go into the new one, and when the summary call fails they are kept, followed by a clipped trace of the steps since;
  - neither policy compacts again when only notes and the user's words are left past the budget, so a long message cannot cause a summary call at every step;
  - the context policy holds for every loop of an arm: under `--context summary`, FORK branches (with the main model, billed to the branch) and sub-agents (with the sub-model) summarise too, no loop is given `history_search` or `history_step`, and every loop's compactions are counted.
- Why:
  - D34 asks for the best version of what products ship. Codex keeps the user's messages verbatim, newest first within 20,000 tokens, and puts the summary after them ([`compact.rs`](https://github.com/openai/codex/blob/main/codex-rs/core/src/compact.rs), `build_compacted_history`), so D34's reason for rejecting this, that it is "not the products'", was wrong. Claude Code instead asks its summariser to list every user message;
  - the fold keeps the user's words verbatim too (D14), so the arms now differ only in how the agent's own steps are compacted, which is the question H4 asks;
  - a summary arm whose sub-agents and branches could search the step log was partly a fold arm, which would bias H4 toward no difference (G27).
- Rejected:
  - the summariser restating the user's messages (Claude Code's way): a restatement can drop or soften a constraint, the failure W8 cites, so it is the weaker of the two product practices;
  - Codex's 20,000-token cap: the fold never shortens the user's words, and the arms must treat them alike;
  - keeping the user's messages inside the summary note: the next compaction rewrites the note, and they would be summarised away then.
- Consequence: headless benchmark runs have no mid-turn messages, so E4 measures the same contrast under D34 and D38; the message rule matters for interactive use and any later steering experiment.
- Evidence: `tests/test_summary_arm.py` (`EveryLoopTest`, `SummaryCompactionTest`); G27–G29.

## D39 · Docker's default runtime here is runc behind a wrapper that sets umask 022 (2026-11-03, active)
- Decision: `scripts/dev-env.sh` installs `/usr/local/bin/frond-runc` (`umask 022`, then `exec runc "$@"`) and makes it dockerd's default runtime in `daemon.json`. The script and the matrix runner's preflight measure the umask of a `docker exec` process in a probe container. The runner refuses to start unless it measures 0022, and an umask it cannot measure counts as wrong; the script's probe is plain shell, so setup needs only Docker.
- Why: Harbor runs agents, reference solutions and tests through `docker exec`, whose processes inherit the umask of the runtime chain (dockerd, containerd, the shim, runc), not the container's. dockerd 29.9.2 sets its own umask to 0, so every file those processes created here was world-writable, and `rs-archive-clone`'s reference solution failed 41 of 57 tests on file modes. A standard host gives 0022. Left alone, the difference would touch every agent's runs wherever modes matter (tests of permissions, ssh refusing a private key others can read).
- Rejected:
  - starting dockerd with umask 022: it resets its umask to 0 (tried);
  - a separately started containerd with umask 022: a second daemon to manage, and the image store would move;
  - setting the umask in the commands Harbor runs: Harbor is pinned and unpatched, and the reference agents' and verifiers' commands go through it too;
  - excluding `rs-archive-clone`: the confound would remain on every other task.
- Evidence: `docker exec` printed umask 0000 before and 0022 after; `tests/test_bench.py::MatrixTest::test_preflight_refuses_a_daemon_whose_exec_umask_is_not_022`; G26.

## D40 · Merge after the review bots have read the PR (2026-11-03, active)
- Decision: after marking a PR ready, wait for the Codex and Devin reviews, which arrive within about two minutes, and keep working meanwhile. Verify each finding like any other claim, fix the real ones in the same PR, and answer the rest in their threads with what was traced. Then merge. If a review has not arrived within 15 minutes, merge, and read the PR's reviews again later. Findings found on PRs merged without their reviews go into the ledger when found.
- Why: D17 rejected waiting because nobody acted on the reviews. On #17 all three of Devin's findings were real, and one biased H4's control arm (G27–G29). The PR had merged within seconds, which also ends the session's subscription to its events, so the findings sat unread. The local suite did not catch them: it tested what the arm was meant to do, not every path into it.
- Rejected: merging at once (it shipped G27–G29); making a review a hard gate (the bots can be slow or down).

## D41 · Cost claims use a studentized bootstrap, specs that may stop early decide by stopping-valid rules, and misconfigured trials are not scored (2026-11-03, active)
- Decision:
  - a ratio claim (treated cost / control cost below b) is tested on the per-task values treated − b × control, whose mean is below 0 exactly when the ratio of the totals is below b, by a one-sided bootstrap-t: resampled statistics are centred on the sample mean and studentized (`stats.bootstrap_t_below`). Fewer than 5 tasks, or values that do not vary, give p = 1. The percentile interval of the ratio stays, as a description;
  - a spec with `stop_early` decides each claim by a rule fixed before the run and valid at any stopping time: a pass-rate claim by its betting confidence sequence, any other claim by its fixed-size p-value times the number of planned looks (batches) times the number of claims, against alpha. A spec without `stop_early` keeps Holm on fixed-size p-values;
  - every trial's recorded configuration is checked against its arm's model and options; a trial that contradicts them did not run the arm, so it is unscored and listed, like an infrastructure failure, and the next valid trial counts instead.
- Why:
  - the old ratio test took the share of percentile-bootstrap ratios on the far side of the bound, which follows neither of Hall and Wilson's guidelines for bootstrap tests (resample under the null, use a pivotal statistic). On skewed null data with 20 tasks it rejected 14% of the time at a nominal 5%; the bootstrap-t rejected 6.7% (F5);
  - a fixed-size test read at a batch the data chose to stop at does not keep its error rate, as `research.md` already said, yet the analysis decided by Holm in every spec (F10). The union bound over looks makes the decision valid whatever the stopping rule, and cost, unlike pass rate, has no useful bound for a confidence sequence;
  - an arm misconfigured the same way in every trial looked consistent in the report (F9).
- Rejected:
  - a t-test on the same per-task values: costs are skewed, and the bootstrap-t corrects for skew at the same cost in code;
  - a sign-flip permutation test: a ratio hypothesis is not a sharp null, so flipping signs is not justified by the design;
  - alpha-spending boundaries (O'Brien–Fleming) for early stopping: they rest on a Brownian approximation of each test statistic's path, which the exact Wilcoxon and the bootstrap tests do not give, and more machinery for a union bound's few looks;
  - a confidence sequence for cost: a betting sequence needs bounded values, and the only bound (steps × context × price, about $29 a trial on Sonnet 5.5) makes it far too wide to decide anything;
  - dropping `stop_early`: it is what keeps a capped key's budget for more experiments;
  - scoring misconfigured trials, or failing the whole analysis on one: the first mixes setups into an arm, the second loses every valid trial to one bad one.
- Consequence: cost claims in early-stopping specs pay a factor of 2–4 in p (2 to 4 planned looks) for the option to stop. `research.md` states the rules.
- Evidence: `tests/test_bench.py` (`BootstrapTTest`, `test_a_spec_that_may_stop_early_decides_by_rules_valid_at_any_stop`, `test_a_trial_that_did_not_run_its_arm_is_not_scored`).

## D42 · An experiment runs one version of frond (2026-11-03, active)
- Decision:
  - the adapter installs frond's wheel under constraints exported from `uv.lock`, so every trial runs the locked versions of every dependency;
  - a jobs directory is bound to the digest of its spec and to a digest of the files a trial's frond is built from (`src/`, the adapter, `pyproject.toml`, `uv.lock`). Resuming it after either changed is refused; `--allow-changed-source` allows a source change, for one that cannot affect the arms, and each run records it.
- Why: the arms differ in one mechanism each, and a change to frond, or to a dependency resolved at install time, between batches would be a second difference, invisible in the report (F8, G31).
- Rejected:
  - pinning only DSPy: litellm and the rest still floated between containers;
  - binding jobs to the git commit: documentation commits would block every resume, and a dirty tree would hide real changes;
  - refusing any source change without an override: a change to the TUI cannot touch a benchmark arm.
- Evidence: `test_jobs_of_another_spec_or_source_are_not_resumed`; a constrained install in a scratch tool directory ran `frond --version` with DSPy 3.4.1.

## D43 · The owner's grant is enforced twice: a Console spend limit, and a runner that will not start a job past the cap (2026-11-03, active)
- Decision: `bench/budget.toml` holds the program's cap ($100, the owner's grant of 2026-11-03). Before each Harbor job, `bench.matrix` totals what every trial under `jobs/` cost at list prices, adds the most the job could cost (its remaining trials times the costliest measured trial of its model times 1.5, or before any measurement a per-model guess scaled by the arm's step limit), and stops if the sum passes the cap. Preflight refuses an arm whose model has no price or no guess. The key lives in a Console workspace whose spend limit is the same $100, which stops a job midway.
- Why: the runner sees only finished trials, so it cannot stop a job that runs over; the Console limit can, but it fails a job halfway, after money is spent on trials that may be unusable. Checking before each job keeps the runner from starting what the cap cannot pay for.
- Rejected: the Console limit alone (a job that hits it leaves a half-run batch); a check inside each trial (Harbor runs trials in parallel containers with no shared ledger); a guess with the margin applied too (it would put E0's plan, $45-75 by its own estimate, above the cap before any measurement).
- Evidence: `tests/test_bench.py::BudgetTest`, including that E0 fits the cap on the guesses alone ($70.50).

## D44 · E1–E3 run their 53 tasks in four batches of up to 14 (2026-11-03, active)
- Decision: E0a's final list leaves 53 TB 4.0 tasks, and E1, E2 and E3 take batches of 14 (14, 14, 14, 11), amended before any trial.
- Why: the batch count is the number of planned looks. Under `stop_early` (E1, E2) a cost claim's p-value is multiplied by it (D41), and each batch is one round of the ABBA order. Batches of 13 would have made five looks, the fifth for a single task.
- Rejected:
  - 13 tasks per batch: a fifth look raises the cost claims' multiplier from 4 to 5 for one task, and a one-task batch costs a full ABBA round;
  - dropping one task to keep 52 in batches of 13: an exclusion with no cause in the task;
  - 18 per batch (three looks): fewer chances for the confidence sequences to stop a decided experiment early.
- Evidence: `python -m bench.matrix bench/experiments/e1-action-space.toml --dry-run` (and e2, e3) shows 53 tasks in 4 batches.

## D45 · The paid smoke run is frond's arm alone; the reference agents first spend in E11, under per-trial bounds (2026-11-03, active)
- Decision: the first run with the real key is `smoke.toml --arms frond`: one task, every arm flag, 3 steps on Opus 5.5, so at most a few tens of cents. Its checks are that a model call succeeds end to end, that cost and cache reads reach the export, and that the key's value appears in no file under `jobs/`. Claude Code, Terminus 2 and `dspy-rlm` keep the free smoke (a dummy key, 401), which they passed on 2026-11-03, and spend first in E11, once its spec bounds each per trial (G33).
- Why: `smoke.toml` was written for a dummy key, under which every arm stops at its first call. With a real key, Claude Code and Terminus 2 run until the task's 8-hour limit, and the guard (D43) would admit them on a $2 guess it cannot enforce within a trial. The paid smoke needs one agent that reaches the model; frond's step limit bounds its cost.
- Rejected: running all four arms with the key (an unbounded spend for checks the free smoke already made); bounding the reference agents in `smoke.toml` now (the bound is E11's design choice, since a bound that binds changes the reference); skipping the paid smoke and starting E0 (a fault in the export or a leaked key would then spoil 50 trials instead of one).

## D46 · A reply off the field protocol is recovered when it names one action, and otherwise costs a step, not the run (2026-11-03, active)
- Decision: when a step's reply does not parse into its fields, `FrondAdapter` recovers it if it names exactly one action: one `<invoke>` call (its `code` parameter for the code arm; its name and parameters, JSON-decoded where they parse, for the tools arm), or for the code arm exactly one fenced Python block. The text before the action, without field markers, is the reasoning. Any other reply raises as before, and the loop turns it into an error step: nothing runs, the model sees its own words in the reasoning slot and a one-line statement of the format, and the step counts against the budget. Every reply off the protocol is still counted (`parse_failures`), with `parse_recovered` and `unparsed_steps` beside it.
- Why: the first real call showed that Opus 5.5 at high effort writes a narration line before its fields, and often drops the markers for a fenced block or its native tool-call syntax (G34): 4 of 7 first-step replies. A run that ends on the first such reply measures the parser, not the harness, and would have made E0's pass rates mostly zeros. The recovered shapes leave no doubt about what to run, so accepting them changes no action the model chose; a reply with two blocks or a non-Python fence could mean several things, so it is refused, not guessed.
- Rejected:
  - only rewording the prompt (it already ends by naming the three markers; the habit comes from the model, and a reworded prompt changes every arm's cached prefix while still leaving a fatal path);
  - DSPy's JSON-adapter fallback (a second, full-price call in another format; DSPy skips it anyway once a stream has emitted output, which frond's always has);
  - Anthropic's native tool calling for the code arm (that is the tools arm of H1; using it here would erase the difference H1 tests);
  - turning thinking off to suppress the narration (effort is fixed per arm by D26, and the narration did not stop the 3 replies that kept the markers from parsing);
  - ending the run but scoring it as an infrastructure failure (the model did produce the reply; hiding it would bias every arm's pass rate toward models that comply).
- Consequence: H1's protocol comparison reads `parse_failures` per step for adherence, and `unparsed_steps` for what adherence cost. The tools arm gets the same recovery, so neither arm of H1 is favoured.
- Evidence: `tests/test_metrics.py` (`ParseFailureTest`, `UnparsedStepTest`); the six replayed replies and the smoke's reply all parse.

## D47 · Experiments run from a frozen worktree of `origin/main`, sharing the checkout's `jobs/` (2026-11-03, active)
- Decision: a paid experiment runs from `git worktree add /home/user/run-<id> <merge commit>`, whose `frond/jobs` is a symlink to the main checkout's `frond/jobs`. Development goes on in the main checkout meanwhile.
- Why: an experiment like E0 runs for hours, and each Harbor job builds frond from the tree it runs in. The runner now refuses a changed source between jobs (G35), but a refusal stops the experiment; a worktree no edit reaches lets work continue alongside it. The shared `jobs/` keeps every trial where the spending guard counts it (D43) and where the analysis and later sessions look.
- Rejected: pausing development while an experiment runs (hours lost per experiment); a copy of the tree instead of a worktree (no commit to name in the results); a separate `jobs/` per worktree (the guard would not count the other's spending).

## D48 · E0 runs one trial per model, cheapest first; the variance trials move to E0b on the screening model (2026-11-03, active)
- Decision: E0 runs its 10 tasks once on each of Haiku 5.5, Sonnet 5.5 and Opus 5.5, in that order. The 2 further trials per task that measure variance (E0b) run on the screening model E0 picks, under a spec committed once the model is known. `bench/budget.toml`'s per-trial guesses rise to $5 (Opus), $2.50 (Sonnet) and $0.15 (Haiku) at 40 steps.
- Why:
  - the second paid smoke spent $0.70 on 3 Opus steps at high effort: 27k output tokens, 17.6k of them thinking, against the 2k a step `research.md` assumed. Even if later steps of a 40-step run are half that size, an Opus trial costs about $5, so E0's 30 Opus trials would have cost about $150 of a $100 grant;
  - the old guess ($2) would have let the runner start that job, and the Console limit would have stopped it midway, with neither cheaper arm run (the failure D43 was written to prevent);
  - E1–E5 run on the screening model, so it is that model's variance, not Opus's, that sizes them. Measuring it on Opus was the wrong model as well as the costliest;
  - cheapest first: each arm's measured cost tightens the guard's estimate before the next, costlier arm starts.
- Rejected: E0 as pre-registered (over the grant); lowering Opus's effort to fit (D26 fixes high effort; it would change the model being measured); fewer tasks per model (10 is already the least that tells a 20–80% pass rate from the ends); asking the owner for more money before any measurement (the request would rest on a guess; E0's costs are what the program's budget request needs).
- Consequence: E0 plans $76.50 on the guesses. The program's budget request (now.md) follows E0, from measured costs; E0b may need it.

## D49 · Spending that `jobs/` cannot show is recorded in git (2026-11-03, active)
- Decision: `bench/budget.toml` holds `[[spent]]` entries, each with its amount and reason, for spending the trials under `jobs/` cannot show: jobs lost with an earlier VM, trials killed before they wrote their cost, and calls made outside Harbor. An entry that names a jobs directory stands in for it, and the guard does not scan that directory. An entry is added after every paid run and committed.
- Why: `jobs/` is not in git and dies with the VM, so the guard of D43 began each session at $0, with only the Console limit holding the grant. And a trial killed mid-run (E0's first start, stopped for G36) leaves a result with no cost, which correctly stops the guard, with no way to account for it short of deleting evidence.
- Rejected: committing `jobs/` (gigabytes of trajectories, and the redaction of B12 is the only thing between them and a key); reading spend from the Anthropic Console (needs an admin key the session does not have, REQ); deleting killed trials so the guard runs (loses the record, and their money still counts); an estimate per killed trial computed by the runner (the bound depends on the model and steps, and is rare enough to state by hand, with its reasoning).
- Evidence: `test_recorded_spending_counts_and_stands_in_for_its_jobs`.

## D50 · E11's reference agents run under per-trial bounds set well above typical spend (2026-11-03, active)
- Decision: Claude Code runs with `max_budget_usd = 10` per trial, Terminus 2 with `max_turns = 150`, and Harbor's `dspy-rlm` with its default of 20 iterations and 50 LLM calls. The guard (D43) takes a dollar cap as a trial's worst case and scales its per-trial guess by a turn or iteration cap as it does frond's steps; preflight refuses a reference agent whose spec sets no bound it knows.
- Why: with a real key the reference agents would otherwise run until a task's 8-hour limit, and the guard could neither estimate nor enforce their spend (G33). A bound that binds changes the reference, so each sits well above what a trial typically spends: frond's own Opus trials are estimated at $5 for 40 steps (D48), and frond's tools arm gets 100 steps (D33), so $10 and 150 turns leave room. How often a bound binds is reported before E11's analysis (G39), so a reference weakened by its bound shows.
- Rejected: no bound (unenforceable spend); bounds equal to frond's (40 steps), which would handicap the references against their own published configurations; a wall-clock bound (Harbor's per-task timeout is the task's, and time does not bound spend).

## D51 · Each step's reply carries a short note for the user, not the model's reasoning (2026-11-03, active)
- Decision: the action signature's first output field is `note`, "one or two sentences for the user: what this step does, and what you expect its result to show", in place of DSPy's `reasoning` ("Think step-by-step: what do you know? What remains? Plan your next action."), in both arms. The model's reasoning stays in its thinking blocks (adaptive thinking, D26). Inside frond the note is still each step's `reasoning`, so the step log, exports and TUI are unchanged.
- Why: Sonnet 5.5 refused every call of E0's Sonnet arm with `stop_reason: refusal`, category `reasoning_extraction` (G41). Anthropic's refusal guidance names a `reasoning` field the model fills before answering as the trigger, and says to change the prompt, asking for a short explanation or a summary of the actions instead, and to read reasoning from thinking blocks; the category has no fallback model. The note is what frond used the field for anyway: the user's narration of each step.
- Rejected: a fallback model (the arm would no longer measure the model it names, and the category has none); keeping the field on Opus and Haiku, which answered it (the classifiers can change, and two protocols would make the models incomparable in E0 and every later experiment); rewording the field until the classifier passes it (that is getting around a provider safeguard, not following its guidance).
- Consequence: the protocol changed before E0 measured anything on it, so E0 restarts and its earlier Haiku trials are not E0's. Protocol adherence is measured afresh.
- Evidence: `NoteFieldTest`; 3-step frond runs on Sonnet 5.5, Opus 5.5 and Haiku 5.5, every reply parsed.

## D52 · A PR merges once Codex has reviewed it and its findings are answered; Devin is read when it posts (2026-11-03, active, amends D40)
- Decision: after opening a PR, wait for Codex's review (about two minutes), verify and answer its findings, and merge. Devin's reviews are read when they arrive, before or after the merge; findings on merged PRs go into the ledger (G40 tracks the open ones).
- Why: D40 waited up to 15 minutes for both bots. Devin posted nothing on #34 to #40, over three hours, while Codex reviewed each within two minutes. The wait held finished work, and a paid run, which lasts only while a turn is active (G44), behind a reviewer that was not reviewing.
- Rejected: keeping the 15-minute wait (pure delay while Devin is silent); dropping Devin altogether (its findings on #14 to #33 were real, and it may come back).

## D53 · Each code step replies with one JSON object held to a schema by structured output (2026-11-03, active)
- Decision: frond asks each code step for one JSON object with the string fields `note` and `code`, and passes the schema as the provider's structured output (Anthropic's `output_config.format`), so the reply is held to it as it is generated (`--protocol json`, the default). DSPy's `[[ ## field ## ]]` markers stay as `--protocol markers`, the control arm. A JSON reply is read strictly: one that is not whole was cut off or refused, and is never repaired into code that was not finished. The tools arm keeps the markers until its `args` has a schema per tool (B19). E0 was stopped before its Opus arm and restarts on the json protocol.
- Why: under the markers, E0's fourth start had 75 of Haiku's 256 replies (29%) and 64 of Sonnet's 208 (31%) off the protocol, and 21 and 19 of them unread, each a lost step (G48). Most off-protocol replies held tool-call markup (`<invoke name="x">`, `<parameter name="note">`) where the markers belonged: the models write the native tool calls they are trained on, which no prompt wording reliably stops. A third of every trial's steps spent on the format would swamp the effects E1–E6 measure. Structured output removes the failure rather than recovering from it: in a probe, 6 of 6 replies on Haiku, Sonnet and Opus 5.5 were schema-valid ($0.02), and frond completed a small task on each with no reply off the protocol (3–4 steps, $0.08 in all).
- Rejected: recovering more shapes under the markers (G34's recovery already handled two; the shapes keep varying, and a recovered step is still a guess at what the model meant); native tool use, one `run(note, code)` tool (Opus and Sonnet 5.5 reject forced `tool_choice`, so a step could still come back as text; it is the stronger candidate for the tools arm, B19); running E0's Opus arm on the markers for completeness (up to $50 on a protocol being replaced); dropping the markers altogether (they are the comparison that says what the protocol costs or gains, and code inside JSON has been reported to lower code quality on some models, which the arm can show).
- Consequence: E0's Haiku and Sonnet results on the markers are kept as `jobs/E0-markers` and recorded in `bench/results/`, as the markers arm's first measurement; they are not E0's. Every spec inherits the json protocol; E0 names it. Pass rates under the two protocols are compared once E0 has run (on the markers, Haiku passed 0 of 10 and Sonnet 1 of 8 scored, `bench/results/2026-11-03-e0-markers/`).
- Evidence: `test_json_steps_are_json_turns_held_to_a_schema`, `ReplyStreamParserTest`, `test_a_sub_agents_replies_count_apart_from_the_main_models`; the probe and smoke runs above.
