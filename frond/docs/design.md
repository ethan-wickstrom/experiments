# frond: problem space and design space

Written on 2026-11-03 against commit 2726a56 of `claude/frond-context-engine`. This file applies the separation of problem space, design space and solution space to frond itself. It states environment facts W, requirements R and constraints C in the sense of Zave and Jackson's `W, S ⊢ R` ([Four Dark Corners of Requirements Engineering](https://dl.acm.org/doi/10.1145/237432.237434)), and it traces in both directions. It records the reasoning. The work that follows from it is tracked with stable IDs in [open-items.md](open-items.md), which cites the R, W, C and U IDs used here. Code references are relative to `frond/`.

## Decisions taken after the analysis

- U1 is answered: frond is a research vehicle (the user, 2026-11-03).
- The work order is the daily-driver order, as the user instructed on 2026-11-03: P1, P2, P4, P6a, P6b, then P3 and P5. P0 runs whenever an API key and Docker or Daytona are available. Item ORDER in open-items.md asks for confirmation, because the analysis tied this order to daily-driver use.
- A step 0 was added: a live pilot on 5–10 Terminal-Bench tasks (see Plan).
- Step 1 lands inside PR #3 before it leaves draft, because PR #3 is the change that gives mid-turn messages priority over the original request.

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
| R2 | Every change in a turn is shown, including command-made ones, and the turn's net change is reviewable | Each mutation kind (edit, create, delete, chmod, symlink, command) emits a diff; a net-change view exists | Per-change diffs in git workspaces only. No net view. Changes to ignored files and non-git folders are unseen |
| R3 | `/undo` restores what frond changed and leaves later changes by others alone, reporting the conflict | A test edits a file between frond's change and `/undo` | Fails: undo overwrites the later edit |
| R4 | Esc halts within a second and no tool runs afterward; a mid-turn message reaches the model at the next step; Tab queues | Latency measured in the scripted harness | Mid-turn messages and queueing tested; stop latency unmeasured |
| R5 | The user's words reach the model verbatim and cannot be confused with tool output | A file containing frond's framing for user messages is shown escaped | Verbatim within a turn and for the last 8,000 characters across turns. Can be forged |
| R6 | Without the user's approval, no frond process writes outside the workspace and temp, reaches the network, or holds credentials | Exfiltration test from the REPL; sandbox tests | Holds only for sub-agents' commands. The PR #2 OS-level read-only guarantee does not cover their Python. Every REPL worker has network access and the keys |
| R7 | The agent can return its context and the workspace to an earlier point in the turn | Rewind test | Missing |
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
- Pass rate. About 90 tasks at 5 trials each gives a 95% interval of roughly ±4–5 points on the paired difference. That is an estimate, assuming per-task variance typical of agent runs, and P0 measures it. A 3-point gap cannot be resolved at that size, but "no worse within 5 points" can. The test is the Wilcoxon signed-rank test with the task as the pairing unit, the method AgentRewind used.
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

Work order (the user's instruction of 2026-11-03): P1 → P2 → P4 → P6a → P6b → P3 → P5. P0 runs as soon as an API key and Docker or Daytona are available. Each step's done-when check is in open-items.md.

- P0. Live pilot on 5–10 Terminal-Bench tasks: read the provider's real `cache_read_input_tokens`, check that the model keeps to the RLM protocol, and measure per-task variance to size P3.
- P1. Close R5 and R6 for the worker, inside PR #3 and before it leaves draft:
  - scrub its environment and confine it;
  - block the socket audit events;
  - add the random marker with escaping;
  - add tests that forge a mid-turn message and attempt an exfiltration.
- P2. Add post-images and the check before undo, with a concurrent-edit test.
- P3. Probe the sandbox inside a Harbor task container, then run the paired Terminal-Bench comparison with Codex CLI.
- P4. Add the sandbox for the main agent's commands (writes inside the workspace only, network off), with approval only to escape.
- P5. Add scopes as savepoints (begin, end, abandon) behind a flag, measured on a long-horizon set.
- P6a. Add pairing rules for state outside the workspace.
- P6b. Add the DSPy startup check.
