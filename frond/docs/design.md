# frond: problem space and design space

A living document. The first version was written on 2026-11-03 against commit 2726a56. It applies the separation of problem space, design space and solution space to frond, stating environment facts W, requirements R and constraints C in the sense of Zave and Jackson's `W, S ⊢ R` ([Four Dark Corners of Requirements Engineering](https://dl.acm.org/doi/10.1145/237432.237434)), traced in both directions. Code references are relative to `frond/`.

The other documents:
- [decisions.md](decisions.md): every decision, with the alternatives rejected (D-IDs);
- [ledger.md](ledger.md): every open and closed item;
- [research.md](research.md): the experiment protocol (H-IDs);
- [now.md](now.md): the current focus.

This file holds the analysis and the traceability matrix. It is updated in the same commit as any change that moves a requirement's status.

## Since the first version (2026-11-03)

- frond is a research vehicle, and the agent owns every decision (D16). Constraints C1 and C2 below were the brief's. They are now choices that the agent keeps for reasons and tests as hypotheses: H1 tests C1's RLM premise.
- The architecture moves to worlds (D22, "Architecture: worlds" below).
- The plan lives in the ledger and `now.md`. The section "Plan" below keeps only the order.

## Summary

Three results came out of the analysis.

1. frond breaks two requirements that its brief implies but never states.
   - Python that the model writes can open network connections while holding the user's API keys. The REPL worker inherits the whole environment (`src/frond/agent/repl.py:113`). Its audit hook checks only subprocess, write and path events (`src/frond/agent/_worker.py:248`). So no approval stands between an injected instruction and `urlopen(..., os.environ[...])`.
   - Tool output can reproduce the exact framing frond puts around messages the user sends mid-turn (`src/frond/agent/adapter.py:41`). frond's prompt then tells the model that those messages win over the original request (`src/frond/agent/adapter.py:119`).
2. "Outperform Codex" has to be split. The pass-rate part can only be shown as "no worse" at an affordable sample size. Cost and the interactive properties can be shown decisively.
3. Four recent papers each solve part of the long-horizon problem, and together they point to one design move that suits an RLM well: treat the transcript, the workspace and the REPL namespace as one versioned state, with checkpoints at boundaries the agent itself declares.

## Problem space

### The brief, sorted

Most items in the brief are solutions, and each stands for a need. Naming the need lets a better solution replace the stated one without losing what it was for.

| In the brief | Kind | Need it stands for |
|---|---|---|
| visible diffs; terminal-command components | solution | see every change and side effect before relying on it |
| streaming | solution | see progress early enough to intervene |
| Enter→stop button | solution | halt promptly |
| queued messages | solution | record the next intent without waiting |
| context-limit bar | solution | anticipate running out of context, and the cost |
| @-tagging | solution | point at code cheaply |
| sleek, resizable TUI | solution and quality | usable all day in real terminals |
| edit/create files; bash, also in the background | capability | change code; run long processes |
| `dspy.RLM`; Python, DSPy and the stdlib only; uv, ruff, ty | constraints | imposed from outside, so part of the problem |
| outperform Codex | success criterion | undefined until a measurement is chosen |

Read as needs, the brief also implies five needs it never states:
- frond does nothing the user cannot see or reverse, including outside the workspace;
- the user's own concurrent edits survive frond's undo;
- text from repositories and tools cannot speak as the user or carry secrets out;
- the user's instructions survive long sessions intact;
- frond survives changes in DSPy.

Each one became a requirement below.

### Environment facts (W)

These hold whatever frond does.

| ID | Fact | Evidence | What it forces |
|---|---|---|---|
| W1 | The user corrects course while frond works | Progressive delivery with corrections raised success from 40.3% to 64.1% in [FeatureLoop](https://arxiv.org/abs/2610.35488) | Steering and queueing are core, not polish |
| W2 | The user and their tools edit the workspace during a turn: editor saves, formatters, branch switches | Ordinary practice; no study found | Undo cannot assume frond is the only writer |
| W3 | Regretted losses are often outside the workspace | In [RegretBench](https://arxiv.org/abs/2610.28934), agents finished 86.1% of tasks but backed up the affected state first in only 15.2%; harness backups cover the workspace only | Reversibility needs a stated boundary, or rules that extend it |
| W4 | Repository and tool text can imitate any in-band framing | Forged turns survived compaction 87–100% of the time in flattened harnesses and 0% in role-typed ones ([Compaction Laundering](https://arxiv.org/abs/2610.29869)) | The user's messages need a mark of origin that tool output cannot forge |
| W5 | Model-written code is arbitrary code | [PEP 578](https://peps.python.org/pep-0578/) says audit hooks are not a sandbox. [DSPy's default interpreter](https://dspy.ai/current/api/tools/PythonInterpreter/) is a Deno/Pyodide WASM sandbox with network, file and environment access off unless granted; constraint C2 rules it out | The worker needs OS confinement |
| W6 | OS confinement is unevenly available | [Ubuntu](https://www.ubuntu.com/blog/ubuntu-23-10-restricted-unprivileged-user-namespaces) restricts unprivileged user namespaces through AppArmor, on by default in 24.04. [Docker's default seccomp profile](https://docs.docker.com/engine/security/seccomp/) blocks `mount` unless the container has CAP_SYS_ADMIN, and frond's namespace sandbox needs `mount`. Whether Docker allows Landlock's syscalls is unconfirmed | Landlock is the main Linux path; benchmark containers need a probe |
| W7 | Cost follows the number of turns | 84% of cost variance, with 98.6% of input cached ([TurnCost](https://arxiv.org/abs/2610.15093)), but in headless runs. A pause of more than five minutes expires [Anthropic's default cache](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) | Fewer steps; cache lifetime chosen from measured pauses |
| W8 | Summaries lose instructions | A third of anti-cheat rules were lost after the first compaction, and how-to-work rules six times as often as specs ([study](https://arxiv.org/abs/2610.31778)). A lossless log scored 73.1% against 19.9% for summaries ([Scroll](https://arxiv.org/abs/2608.21690)) | No lossy summaries |
| W9 | Long-horizon gains come from structure, not just retention | See below the table | Structure the context, and measure the result |
| W10 | Recovery needs the context and the workspace rewound together | [AgentRewind](https://arxiv.org/abs/2608.14380) raised success from 62.2% (no rewind) to 87.8%. Rewinding the context but not the workspace scored 43.9%, worse than not rewinding | No context-only rewinds |
| W11 | Differences between harnesses in pass rate are small | Within 3 points across action interfaces ([restriction study](https://arxiv.org/abs/2607.10569)) | R1 must be framed so it can be detected |
| W12 | `dspy.RLM` is young, and frond overrides three of its private methods | frond's own code | Pin DSPy and check at startup |

The evidence for W9 comes from three papers:
- [Spine](https://arxiv.org/abs/2610.37224) has the agent declare where each subtask starts and ends. Against native Codex it raised the SWE-Milestone score 11.8% and cut cost 32.4%.
- [CarryOn](https://arxiv.org/abs/2610.18784) keeps reusable objects plus a list of open goals and constraints. It gained 5.8 points with 51.9% fewer tokens, and hiding the goals list cost 11.9 points.
- [StateHarness](https://arxiv.org/abs/2610.17616) keeps project state up to date. It raised RefactorBench chain completion from 29.4% to 35.3%. On ChainSWE, however, previously passing tests that broke rose from 16 to 23.

### Requirements (R)

Each is stated as a property of the world. Three are met and left out of the table: @-mentions, background jobs and the context meter.

| ID | Requirement | Acceptance check | Status at 2726a56 |
|---|---|---|---|
| R1 | With the same model, frond solves at least as many Terminal-Bench 2.1 tasks as Codex CLI, at lower cost per solved task | Paired by task, 5 trials each; no worse within 5 points; cost priced with cache reads | Unmeasured |
| R2 | Every change in a turn is shown, including command-made ones, and the turn's net change is reviewable | Each mutation kind (edit, create, delete, chmod, symlink, command) emits a diff; a net-change view exists | Done (D29): command diffs in any directory, `/diff` for the net change. Files git ignores are left out by design |
| R3 | `/undo` restores what frond changed and leaves later changes by others alone, reporting the conflict | A test edits a file between frond's change and `/undo` | Done (D29): a three-way revert |
| R4 | Esc halts within a second and no tool runs afterward; a mid-turn message reaches the model at the next step; Tab queues | Latency measured in the scripted harness | Mid-turn messages and queueing tested; stop latency unmeasured |
| R5 | The user's words reach the model verbatim and cannot be confused with tool output | A file containing frond's framing for user messages is shown escaped | Verbatim within a turn and for the last 8,000 characters across turns. Can be forged |
| R6 | Without the user's approval, no frond process writes outside the workspace and temp, reaches the network, or holds credentials | Exfiltration test from the REPL; sandbox tests | Holds only for sub-agents' commands. The PR #2 OS-level read-only guarantee does not cover their Python. Every REPL worker has network access and the keys |
| R7 | The agent can return its context and the workspace to an earlier point in the turn | Rewind test | Done (D35): `abandon_scope` rewinds both to the scope's savepoint |
| R8 | Most input is served from cache | At least 90% cache reads over a 20-step turn, live on Anthropic and OpenAI | Simulated only |
| R9 | An incompatible DSPy release fails at startup, not mid-turn | Contract test | Missing |
| R10 | Every run leaves a complete record for analysis and benchmark review | ATIF export | Done; tested only in a dry run |
| R11 | Works in Linux and macOS terminals; Windows is out of scope (termios) | CI matrix | Tested on Linux only |

### Constraints (C)

- C1: `dspy.RLM` at the center.
- C2: Python, DSPy and the CPython stdlib only.
- C3: uv, ruff and ty.
- C4: Unix terminals, which follows from handling the terminal with the stdlib.

C2 has a consequence that crosses spaces. DSPy's sandboxed interpreter runs on Deno, so C2 forced frond to write its own CPython worker. That worker has the open network path behind R6. A constraint created a requirement gap, which is why constraints belong in the problem space.

### Success criteria

"Outperform Codex" splits three ways:
- Pass rate. About 90 tasks at 5 trials each gives a 95% interval of roughly ±4–5 points on the paired difference. That is an estimate, assuming per-task variance typical of agent runs, and E0 measures it. A 3-point gap cannot be resolved at that size, but "no worse within 5 points" can. The test is the Wilcoxon signed-rank test with the task as the pairing unit, the method AgentRewind used.
- Cost per solved task. Cost differences between harnesses are large, so a real advantage would be detectable.
- Interaction. Stop latency, delivery of mid-turn messages, undo fidelity including shell changes, and injection resistance are deterministic properties. The scripted LM can test them, and they are where frond's design differs most from Codex, which removed its ghost-commit undo in v0.126.

### Unknowns (U)

- U1: whether frond is mainly a daily driver or a research vehicle. Answered: a research vehicle.
- U2: which providers the user runs; their caching mechanics differ.
- U3: how long the user pauses between turns, which decides the cache lifetime.
- U4: whether the user edits files during turns, which sets R3's priority.
- U5: the evaluation budget, about 900 agent runs for one full paired comparison.
- U6: whether Landlock works inside Terminal-Bench containers; one command inside a task container answers it.

## Design space

For each decision the alternatives came first, then the choice. Three decisions changed in this pass. The rest are in the table at the end of this section.

### The turn's state

Per turn, frond holds three kinds of state: the transcript the model sees, the workspace, and the REPL namespace. Seven ways to manage them were considered:
1. Fold old steps into an index when a budget is exceeded, over a lossless log. This is what frond does now.
2. Summaries. Rejected by W8.
3. Context the model edits itself. Rejected earlier: injection risk, and the gains were in compute only ([Context Language Models](https://arxiv.org/abs/2609.37725)).
4. Project records plus a working brief refreshed by fixed rules (StateHarness).
5. Scopes the agent opens and closes, compiled into the context just before each model call (Spine).
6. Reusable objects plus an explicit list of open goals and constraints, plus the recent steps verbatim (CarryOn).
7. Checkpoints that align context and workspace, with rewind (AgentRewind).

Options 4–7 are not rivals; they describe the same structure from different sides.
- Opening a scope creates a savepoint.
- Closing a scope with a result is Spine's move. frond would replace the scope's steps with one entry, goal → result, and the steps stay in the step log. Spaces nest here: the design's own problem includes the cache rule that only replacing the tail of the transcript keeps the cached prefix. A closed scope is the tail, so the cache before it survives. Today's fold puts its index first (`src/frond/agent/rlm.py:313`), so every fold re-writes the whole history to the cache.
- Abandoning a scope is AgentRewind's move. frond would restore the workspace from the journal and snapshots it already keeps, cut the transcript back to the savepoint, and add the reason as a note on the failed attempt. AgentRewind needed that note: success fell to 51.2% without it.
- The open scopes, shown as a stack after the cached prefix at each step, are the goals list CarryOn found indispensable and StateHarness calls the current focus. frond gets it without an extra model call.
- The REPL namespace cannot be rewound cheaply. frond would list the names changed since the savepoint as stale.
- frond's REPL variables already play the role of CarryOn's reusable objects. The RLM's premise is that progress lives in the environment, not the transcript.

StateHarness's diagnostic sessions and CarryOn's compiler and grounder are rejected: each adds model calls per fold, and the REPL already holds the objects. The budget fold stays as the fallback for when the agent never closes a scope.

As built (B9, D35): `open_scope(goal)`, `close_scope(result)` and `abandon_scope(reason)` are tools; the loop applies a close or an abandon to the history at the start of the next step. Closing collapses the scope's steps to one entry; abandoning reverts the scope's workspace changes by a three-way merge (so later edits by others stay), cuts the context back, notes the reason, and lists the REPL names changed since as stale. The user's messages from inside a scope are kept. Scopes are a turn's: they do not outlive it.

Assumptions to test (A1–A4, A10 in open-items.md):
- The model opens and closes scopes unprompted. Spine's agents closed 224 scopes across seven projects; frond's logs should be counted.
- A collapsed scope hides nothing needed later. Count how often `history_step` is called on collapsed steps.
- The list of stale names stops the model relying on discarded values.
- Rewinds need a verifier signal. AgentRewind had checklist feedback; frond has one only where tests exist.

Terminal-Bench tasks are mostly short, so this experiment needs a long-horizon set such as SWE-Milestone or MettleBench.

### Recoverability

The alternatives:
- the tool journal plus git snapshots with a private index and object store (now);
- copy-on-write through an overlay mount in the sandbox;
- filesystem snapshots (btrfs, APFS clones);
- ghost commits in the user's repository;
- backup rules that run before commands.

AgentRewind independently built nearly the same snapshot mechanism as frond: a private index driven by git's low-level commands. That is some evidence it is the right one. It stays, with three additions:
1. Post-images. Record a hash of what frond left in each path. At undo, skip any path whose content has changed since, and report it. This closes R3.
2. Pairing rules before commands with known effects outside the workspace, in the style of RegretBench's BackUpper. Package installs save the installed set first, and commands that move git refs record the old ref. BackUpper covered every regretted action at $0.014 per task, and its rules need no model call.
3. The agent's rewind from the section above.

Rejected: the overlay, because the [kernel documents](https://docs.kernel.org/filesystems/overlayfs.html) that changing the lower layer while it is mounted gives undefined behaviour, and W2 says the user will change it; filesystem snapshots, because they are not portable; ghost commits, because they write into the user's repository, which Codex itself abandoned.

### Containment and provenance

For the REPL worker, the alternatives are:
- the audit hook alone (now);
- scrubbing credentials from the worker's environment;
- OS confinement with the existing sandbox helper;
- audit-hook blocks on the `socket.connect` and `urllib.Request` events;
- DSPy's WASM interpreter, which C2 excludes.

The worker needs no network and no writes outside temp, because every effect already goes through host tools, which are approved, journaled and shown. So confining it costs no capability (assumption A12), and all three cheap layers are chosen:
- Always scrub its environment. This is necessary but not enough, since a process running as the same user can read the parent's `/proc/<pid>/environ`.
- Confine it to read-only with no network wherever the sandbox applies.
- Add the socket audit events where the sandbox does not apply.

For the main agent's commands, the earlier recommendation stands: a sandbox that allows writes inside the workspace, with network off by default and approval only to escape. [Anthropic reports](https://www.anthropic.com/engineering/claude-code-sandboxing) that sandboxing cut permission prompts by 84% in its internal use. On Linux, Landlock will carry most of this load (W6), and kernels at Landlock ABI 3 cannot restrict networking at all.

For the user's messages, the alternatives are:
- English framing in the text (now). It can be forged.
- A separate message per steer. Useless, because tool outputs share the user role.
- [Spotlighting](https://arxiv.org/abs/2403.14720)-style marking of all tool output. It cut attack success from over 50% to under 2% on its static test set. But a marker on every line would leak into the exact strings the model copies into `edit()`.
- A per-session random marker in the framing of genuine user messages. frond escapes the marker wherever it appears in tool output, fold lines or answers.
- Rendering past steps as native tool calls and tool results, so the provider's own roles show where text came from.

The random marker with escaping is chosen now, because it is deterministic and testable. Native rendering is an experiment (A13), because it changes what the model sees itself doing, and so what it imitates. The priority the user's mid-turn messages get stays, but it is only safe once it is tied to the marker.

### Other decisions

| Decision | Chosen | Rejected, and why | Assumption to test |
|---|---|---|---|
| Action format | RLM text protocol: reasoning plus Python that calls tools. Required by C1, and code actions matched or beat JSON for [11 of 14 models](https://arxiv.org/abs/2608.06370) | Native JSON tool calls: violate C1, no measured gain | Editing through string literals cost Claude 39.9% more output tokens. Count syntax errors and failed edits in the logs; if high, add a raw patch output field (A6) |
| Cache layout | Cache marker on the last model reply; per-step fields after it | Marking only the system prompt: loses the cached history on Anthropic | A 1-hour cache lifetime costs 0.75·T extra per turn (T = tokens a turn adds). It saves 1.15·H after each pause of 5–60 minutes (H = history so far). So it pays when more than about 0.65·T/H of the gaps between turns are such pauses: 6.5% when H is ten times T. Log the pauses (A7) |
| Intervention | Enter steers, Tab queues, Esc and the button stop; messages delivered between steps | Stop-only, the brief's literal Enter→stop: loses corrections (W1). Aborting the model call mid-step: wastes the call | The need behind Enter→stop was halting promptly (A8). A long foreground command delays a mid-turn message, so show "esc stops the command" while one waits (I5) |
| Sub-agents | Parallel, independent reads only | Delegating every subtask: Spine's recursive-subagent baseline matched Spine's score at 3.8× the cost | Inline scopes cover sequential subtasks (A10) |
| Evaluation | Harbor on Terminal-Bench 2.1, paired with Codex CLI; a long-horizon set for the scope experiment; scripted tests for R2–R6 | Single-trial runs: cannot resolve the effects at stake (W11) | Probe the sandbox in a task container first (U6) |
| Self-improvement | Offline prompt optimization (GEPA) behind a regression gate, once evaluation exists | Online self-editing: nothing gates it | Gains hold on held-out tasks (A11) |
| DSPy coupling | Pin the minor version; a startup check that the three overridden methods keep their signatures; propose upstream hooks | Copying the RLM loop into frond: breaks C1 as written | — |

## Architecture: worlds (D22)

The thesis: an agent's state is a value, not a place. frond keeps every state it passes through as an immutable, content-addressed world, and compiles every prompt as a pure function of a path through those worlds. Undo, rewind, fork, merge, freshness and prompt caching then stop being separate features with separate failure modes. Each becomes one operation on one data structure.

### Objects

- **Blob:** file bytes, addressed by H(bytes), where H is BLAKE2b-256 from `hashlib`. Each blob is stored once, compressed.
- **Tree:** a sorted map from path to (mode, blob id or link target), addressed by H of its canonical encoding. A workspace snapshot is a tree id. Snapshots that differ in d files share every other entry, so k snapshots cost O(Σd) storage, not O(k·n).
- **World:** a tree id, a REPL image, a view head and a set of observations. The REPL image is a forked live process (B6). Failing that, it is a replay recipe: the code of earlier steps, together with their recorded tool results.
- **Step:** an edge from one world to the next. It holds the model's reasoning and code, every tool call with its inputs and outputs, usage, cost and verifier results. Steps are the lossless log (D08), and worlds index it.
- **Observation:** what the model has seen of a file: the path, H(bytes) at read time, and the step. At world w, an observation is fresh if and only if tree(w)[path] equals its hash.

A run is a rooted tree of worlds. In interactive use, the user's working directory is one more world, u, observed on demand.

### Operations, and what each replaces

- **snapshot(dir) → tree.** It is incremental: a stat cache (size, mtime_ns, inode) skips unchanged files, as git's index does. It replaces the edit journal and the per-command git snapshots (D05, D10), and it also covers non-git workspaces and ignored files, up to a size cap.
- **checkout(tree, dir)** writes exactly the symmetric difference.
- **diff(a, b)** lists the paths whose entries differ. A turn's net change is diff(start, end), which meets R2.
- **revert(n → a)** on the user's tree u is merge3(base = n, ours = u, theirs = a). Undo becomes a revert. The agent's changes are taken back, and changes anyone else made since are kept. Overlapping changes become conflicts shown to the user, never silent overwrites. This meets R3 by construction rather than by bookkeeping. merge3 is a line-level diff3 built on the stdlib's `SequenceMatcher`; a binary file conflicts unless one side left it unchanged.
- **rewind(n → a)** moves the agent to an ancestor world: checkout(a), the view cut back to a's path plus a note saying why (AgentRewind's rewind memory), and the REPL restored from a's image. This meets R7.
- **fork(n, k)** creates k children that share n's path. Each has its own directory (a checkout of n's tree), its own forked REPL, and the same view prefix.
- **select and merge:** verifiers score the children, the parent continues from the best child, and that child's tree merges into the parent's line.

  As built (B7, D32): the model calls `FORK(options, check, steps)`, which ends its step. Branches run one after another in the real directory, each reset to the world at FORK and given a fork of the REPL (B6), so caches and environments excluded from worlds are there for every branch. Each continues the main history with its own note as the FORK step's output, so branches and the main line share one cached prefix. The kept branch's world is checked out; the main REPL stays as it was at FORK.

### Views are compiled, and caching follows from immutability

The prompt for world w is View(w) = render(policy(path(root → w))).
- **Append-only:** paths are immutable, so View only grows along a path. The one exception is collapsing a closed scope, and a closed scope is always the tail, so the collapse keeps the prefix.
- **Shared prefix:** siblings share their parent's view as an exact prefix.

With prefix caching, the k children of a world whose view is P tokens cost

    k · P · r + Σ new_i    (r = cache-read price ÷ input price: 0.05 on Opus 5.5, 0.1 on Sonnet 5.5)

in place of k · P. Forking three ways from a 50k-token prefix on Opus 5.5 costs 3 × 50k × $0.20/M = $0.03 in prefix reads, against $0.60 uncached. That turns parallel exploration from a luxury into a routine operation.

### Freshness is truth maintenance

Every read records an observation. At each step the compiler checks every observation against the current tree, one dictionary lookup each, and marks the stale ones in the view: "you read src/x.py at step 3; it changed at step 7 (your sed)" or "…changed outside frond". The model then sees that it is about to edit a file from an out-of-date picture at the moment that matters (H3). The observation set is also what [CarryOn](https://arxiv.org/abs/2610.18784) calls continuation carriers, except that their validity is checked mechanically rather than by a model.

As built (B5, D30): observations are per file and per turn, keyed by the blob id the world store uses. A stale read is named in a volatile prompt field before each step. A whole-file write or a delete over a stale read is refused until the model reads the file again: compare-and-swap, so a change the model never saw cannot be overwritten. With `--freshness off`, only the count of stale actions remains, which is the control arm of H3.

### Provenance

Every fragment of a view has one of three sources:
- the user, marked (D14);
- the model, in the assistant role;
- the world, escaped tool output.

The compiler alone renders views, so the marker discipline is enforced in one place.

### Search

At a fork, children run until a verifier gives a signal or a budget runs out. With per-branch success probability p and independent branches, best-of-k succeeds with probability 1 − (1 − p)^k, for example 0.875 when k = 3 and p = 0.5. Correlated branches do worse, which E2 measures. Children run in parallel, so wall-clock time follows the slowest branch, not the sum of all branches.

### What it removes

| Before | After |
|---|---|
| An edit journal plus git snapshots around commands: two mechanisms, git-only | One store with snapshot, checkout and diff, in any directory |
| Undo overwrites concurrent edits (R3 fails) | Revert is merge3: concurrent edits are kept and conflicts shown |
| The agent cannot rewind (R7) | Rewind moves to an ancestor world |
| Sub-agents re-read context from scratch | Forks share the cached prefix |
| Stale reads are invisible | Stale observations are marked in the view |
| REPL state dies with the process | A REPL image: a forked process, or a replay recipe |

Build order (ledger): B4 (store and merge; wired into frond in B4b, D29) → B5 (freshness) → B6 (forkable REPL) → B7 (fork, select, merge) → B9 (scopes) → B13 (world view).

## Traceability matrix

Requirements to design, code, tests and status. Design commitments without a requirement behind them are the calibrations K1–K15. Every decision in `decisions.md` names the requirement or evidence it rests on.

| Req | Decisions | Code | Tests | Status (2026-11-03) | Ledger |
|---|---|---|---|---|---|
| R1 | D20, D21, D28 | `bench/frond_harbor.py`, `bench/matrix.py`, `bench/analyze.py` | `test_bench` | unmeasured; the machinery is in place | E1, E11 |
| R2 | D10, D22, D29 | `world/timeline.py`, `agent/session.py` (`turn_diff`), `agent/tools.py`, `tui/app.py` (`/diff`) | `test_command_undo`, `test_app` | done: per-command diffs in any directory, and each turn's net change (`/diff`) | closed |
| R3 | D22, D29 | `world/merge.py` (`revert`), `agent/session.py` (`undo`) | `test_world`, `test_command_undo` | done: `/undo` reverts by three-way merge and reports what it kept | closed |
| R4 | D09 | `tui/app.py`, `agent/session.py` | `test_steering`, `test_app` | steer and queue done; stop latency unmeasured | B17 |
| R5 | D14 | `agent/adapter.py`, `agent/rlm.py`, `agent/session.py` | `test_provenance` | done (3c188c9) | — |
| R6 | D06, D13 | `agent/_sandbox.py`, `agent/repl.py`, `agent/_worker.py`, `agent/shell.py` | `test_sandbox`, `test_containment` | worker and read-only agents done; main agent's commands deferred | R6, G1 |
| R7 | D22, D29, D35 | `world/timeline.py`, `agent/scopes.py`, `agent/rlm.py` (`_apply_scopes`) | `test_world`, `test_scopes` | done: abandoning a scope rewinds context and workspace together; the REPL is not rewound | closed |
| R8 | D07 | `agent/adapter.py` | `test_caching` (simulated) | simulated | E0 |
| R9 | D36 | `agent/compat.py`, `cli.py`, `pyproject.toml` | `test_compat` | done: DSPy pinned exactly, its internals checked at startup | closed |
| R10 | D11, D46 | `cli.py` (`--export`), `bench/frond_harbor.py` | `test_memory`, `test_metrics` | done: a real Opus 5.5 run through Harbor exported usage, cost, cache reads and protocol counts (PR #27) | E0 |
| R11 | D25 | — | — | Linux only, by decision | closed |

## Traceability

Requirements with no design behind them at 2726a56: R3 (post-images), R5 (the marker), R6 for the worker and the main agent's commands, R7 (rewind), R9 (the startup check), and R2's net-change view.

Design commitments with no requirement behind them are numbers chosen without measurement. They are labelled as choices (K1–K15 in open-items.md) and are to be calibrated from the step logs, which already record what is needed:
- step limits: 40 per turn, 16 for sub-agents;
- output sizes: 16,000 characters of step output, 24,000 of command output, 32,000 output tokens;
- view window: 300 lines;
- fold: triggers at 45% of the context window (capped at 150,000 tokens, at 3.6 characters per token) and keeps the last four steps unfolded;
- across turns, 8,000 characters of the user's earlier messages shown verbatim;
- limits: 20 command diffs, a 2-second snapshot cutoff, 40 REPL names;
- search: BM25's textbook k1 = 1.2 and b = 0.75.

One calibration already has evidence: after truncated output, TurnCost found that a hint on how to narrow the query made 76.9% of next actions narrow it, against 44% with bare truncation. frond's truncation note only gives the log path (I6).

## Revisions so far

These are written down rather than left implicit in the code.

1. Enter→stop became Enter→steer, with Esc and the button stopping, based on W1 and on Codex's and Amp's moves. The need was kept; the stated solution was not.
2. Read-only enforcement moved from matching command text to the OS, because pattern matching could not satisfy R6.
3. Anthropic's caching needs explicit markers, so the transcript layout was rebuilt around them.
4. An earlier claim that the meter undercounted cached tokens was wrong, because DSPy already adds them. The claim was withdrawn and the code left alone.
5. Found in this analysis:
   - steering created a forgeable channel (R5);
   - C2 removed DSPy's interpreter sandbox (R6);
   - the namespace sandbox is unavailable on Ubuntu desktops and in Docker (W6);
   - R3 had assumed frond is the only writer (W2).

## Vocabulary

Three names should change before the scope design lands, because they would collide (N1–N3 in open-items.md):
- The `Compacted` event and the `compacted` hook describe what everything else calls folding.
- `Record.scope` names the sub-agent a step belongs to, which would clash with the new scopes; `Record.agent` fits.
- "Checkpoint" should be reserved for an aligned transcript-and-workspace savepoint, so the per-turn `Checkpoints` class reads better as an undo journal.

Beyond those, the vocabulary stays loose.

## Plan

The plan lives in [ledger.md](ledger.md), with the current order in [now.md](now.md). That order is research-first (D16): the measurement and experiment infrastructure (B1–B3), then worlds (B4–B7), then the experiments as soon as REQ-1 arrives.
