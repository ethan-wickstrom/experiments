# frond open items

This file is the single list of everything still open in frond, so no open item depends on a chat or a session's memory. `frond/CLAUDE.md` sets the rules for keeping it current. The reasoning behind most items is in [design.md](design.md), whose IDs this file cites.

Each item has a stable ID, a one-sentence statement, a done-when check, a status, what it is blocked on, and its source.
- Statuses are open, in progress, decided, or done followed by a commit hash or date.
- A commit cannot name its own hash. So the commit that finishes an item marks it "done (this commit)", and the next commit that touches this file replaces that with the hash.
- ID prefixes: P plan step, R requirement, U unknown, V unverified claim, A assumption to test, N rename, K uncalibrated number, I idea or gap, X decision that closes an earlier idea, PR pull request.

Last updated: 2026-11-03.

## Waiting on you

### Needs an API key and Docker or Daytona

#### P0 · Live pilot on 5–10 Terminal-Bench tasks
Run frond with a real model on 5–10 Terminal-Bench 2.1 tasks through `bench/frond_harbor.py`. Record the provider's `cache_read_input_tokens`, whether the model keeps to the RLM protocol, and per-task variance for sizing P3.
- Done when: a report under `bench/results/` gives, for each task over at least 3 trials:
  - pass or fail;
  - input and cache-read tokens for each model call;
  - the count of replies that broke the RLM protocol or failed to parse;
  - the tasks and trials P3 needs to resolve a 5-point difference.
- Status: open · Blocked on: an Anthropic or OpenAI API key, and Docker or Daytona · Source: your instruction of 2026-11-03; feeds R1, R8, U5, U6, V1, V2, V4.

Once P0 has run, these also unblock: A5, A6, A9, A12, A13, I9, I10, K1–K15.

#### P3 · Paired comparison with Codex CLI on Terminal-Bench 2.1
Run frond and Codex CLI with the same model on the same tasks, paired by task, using the trial count P0 gives.
- Done when: a report gives:
  - per-task pass fractions for both;
  - the Wilcoxon signed-rank test with the task as the pairing unit;
  - the non-inferiority result at a 5-point margin;
  - cost per solved task priced with cache reads.
- Status: open; sixth in the work order · Blocked on: P0, an API key, Docker or Daytona, and the budget (U5) · Source: R1; design.md "Success criteria".

#### U6 · Sandbox availability inside task containers
It is unknown whether user namespaces or Landlock work inside Harbor's Docker and Daytona task containers. That decides whether read-only sub-agents get a shell there, and whether P1's worker confinement applies.
- Done when: the result of frond's `sandbox_status()` probe (`src/frond/agent/shell.py:82`), run inside one Docker and one Daytona task container, is recorded here.
- Status: open · Blocked on: Docker or Daytona · Source: W6.

#### V1 · No turn has run on a live model
Every agent turn so far ran on the scripted engine, so prompts, streaming and reply parsing are unverified against a real provider.
- Done when: P0 completes at least one task end to end on a real model.
- Status: open · Blocked on: an API key · Source: PR #2 and PR #3 descriptions, "Not tested".

#### V2 · No real Terminal-Bench run
The Harbor adapter has passed only `harbor run --dry-run`, which stopped at the missing Docker daemon.
- Done when: P0 completes.
- Status: open · Blocked on: an API key, and Docker or Daytona · Source: PR #3 description, "Not tested".

#### V4 · Cache savings are simulated
The cached share (85% over a 20-step turn, at under a third of the cost) comes from a simulator of Anthropic's documented rules (`tests/test_caching.py`), not from provider usage figures.
- Done when: P0 reports the measured cache-read share for turns of 10 or more steps on Anthropic, next to the simulator's prediction for the same turns.
- Status: open · Blocked on: an Anthropic API key · Source: PR #3 description; R8.

#### R8 · Most input is served from the cache
At least 90% of input tokens are read from the cache over a 20-step turn, on Anthropic and on OpenAI.
- Done when: measured live on both providers.
- Status: simulated only · Blocked on: Anthropic and OpenAI API keys · Source: design.md R8.

### Needs your answer, your machine or your account

#### ORDER · Confirm the work order
You asked for the daily-driver order and then said frond is a research vehicle. This file follows the daily-driver order (P1, P2, P4, P6a, P6b, then P3, P5), which the analysis tied to daily-driver use.
- Done when: you confirm this order or give another, and the Plan section matches.
- Status: open · Blocked on: your answer · Source: chat, 2026-11-03.

#### A8 · What "Enter→stop" was for
I assumed the brief's "Enter→stop button" was about halting promptly, which Esc, Ctrl+C and the stop button do; Enter now sends a message into the running turn.
- Done when: you confirm, or ask for Enter on an empty prompt to stop as well. That is a one-line change in `submit` (`src/frond/tui/app.py:553`).
- Status: open · Blocked on: your answer · Source: design.md "Other decisions", Intervention.

#### U2 · Which providers and models you use
Cache mechanics and default models differ by provider: Anthropic needs explicit cache marks, while OpenAI caches automatically.
- Done when: you name them here.
- Status: open · Blocked on: your answer · Source: design.md "Unknowns".

#### U4 · Whether you edit files while a turn runs
This sets R3's urgency: if you do, today's `/undo` can overwrite your edits.
- Done when: you answer, or P2's conflict notices show it happening.
- Status: open · Blocked on: your answer, or P2 · Source: W2.

#### U5 · Evaluation budget
One full paired comparison is about 900 agent runs (about 90 tasks × 5 trials × 2 agents; the task count is an estimate).
- Done when: you state a budget here.
- Status: open · Blocked on: your decision · Source: design.md "Unknowns".

#### V3 · The macOS sandbox has never run
The Seatbelt profile in `src/frond/agent/_sandbox.py` is untested. Read-only agents on macOS depend on it, and so does the REPL worker, which falls back to running unconfined if Seatbelt refuses it.
- Done when: `tests/test_sandbox.py` passes on a Mac, and a read-only sub-agent's write fails there.
- Status: open · Blocked on: a Mac, or a macOS CI runner (the repo has no CI) · Source: PR #2 description, "Not tested"; R11.

#### I3 · Devin's three unposted security findings on PR #2
Devin's review of PR #2 reported three security findings that it did not post on the PR because of the repository's Devin settings, and I cannot open them.
- Done when: each finding is copied here as its own item, then fixed or declined with a reason.
- Status: open · Blocked on: you opening [Devin's review page](https://app.devin.ai/review/ethan-wickstrom/experiments/pull/2) or enabling posting · Source: PR #2 review, 2026-11-03.

#### PR2 · PR #2 waits on your review and merge
[PR #2](https://github.com/ethan-wickstrom/experiments/pull/2) (`claude/frond-rlm-coding-agent`, head 5837329) is ready for review. It merges cleanly, has all 15 review threads resolved and has no CI; I never approve or merge.
- Done when: you merge or close it.
- Status: open · Blocked on: your review · Source: PR #2.

## Plan

Work order: P1 → P2 → P4 → P6a → P6b → P3 → P5 (see ORDER). P0 runs whenever its blockers clear. P0 and P3 are under Waiting on you.

#### P1 · Close R5 and R6 for the REPL worker, inside PR #3
Close both gaps in the REPL worker with four changes:
- scrub credentials from the worker's environment;
- run it under the read-only, no-network sandbox where one is available;
- block the `socket.connect` and `urllib.Request` audit events where none is;
- tag your mid-turn messages with a per-session marker that frond strips from everything else the model reads.

The rest of the item:
- Done when tests show that REPL code:
  - cannot see provider keys in `os.environ`;
  - cannot open a TCP connection;
  - still has a temp directory whose files commands can read.

  Also, a step output containing the marker and frond's framing renders with the marker removed; all tests, ruff and ty pass; and the commit is on PR #3.
- Status: done in 3c188c9. Tests: `tests/test_containment.py`, `tests/test_provenance.py` · Blocked on: nothing · Source: R5, R6; design.md "Containment and provenance"; your instruction of 2026-11-03.

#### P2 · Undo leaves later edits alone
Record a hash of what frond left in each path, and have `/undo` skip and report any path whose content changed since.
- Done when: a test that edits a file between frond's change and `/undo` shows the later edit kept and a notice naming the path.
- Status: open · Blocked on: nothing; second in order · Source: R3; W2.

#### P4 · Sandbox the main agent's commands
Run the main agent's commands where they can write only to the workspace and temp, with network off and without credentials, and ask for approval only to run one outside the sandbox. An approved escape gets the full environment.
- Done when: tests on the namespace and Landlock paths show:
  - writes outside the workspace and network connections fail inside the sandbox;
  - an approved escape runs outside it;
  - escape approvals are counted per session.
- Status: open · Blocked on: nothing; third in order · Source: R6; design.md "Containment and provenance"; [Anthropic's sandboxing report](https://www.anthropic.com/engineering/claude-code-sandboxing).

#### P6a · Back up state outside the workspace before known commands
Before package installs (pip, uv, npm), record the installed set; before commands that move git refs, record the old ref.
- Done when: tests show the record made for each rule, and `/undo` says how to restore it.
- Status: open · Blocked on: nothing; fourth in order · Source: W3; [RegretBench](https://arxiv.org/abs/2610.28934).

#### P6b · Fail at startup on an incompatible DSPy
Pin DSPy's minor version, and check at startup that `dspy.RLM` still has the three private methods frond overrides, with the signatures it expects.
- Done when: a test that changes one signature gets a clear message at startup rather than a failure mid-turn.
- Status: open · Blocked on: nothing; fifth in order · Source: R9; W12.

#### P5 · Scopes as savepoints, behind a flag
Add `begin`, `end` and `abandon` to the REPL:
- `end` replaces a scope's steps with goal → result at the tail of the transcript;
- `abandon` restores the workspace and transcript to the savepoint, with the reason;
- open scopes show as a stack after the cached prefix.

The rest of the item:
- Done when: unit tests cover collapse, rewind and cache-prefix preservation, and a long-horizon run (a SWE-Milestone or MettleBench subset) compares the flag on and off.
- Status: open; last in order · Blocked on: P0 and P3's setup for the measurement (the code itself is not blocked); N2 first · Source: R7; W9; W10; [Spine](https://arxiv.org/abs/2610.37224), [CarryOn](https://arxiv.org/abs/2610.18784), [AgentRewind](https://arxiv.org/abs/2608.14380).

## Requirements not done

R8 is under Waiting on you. R10 is done; its dry-run caveat is V2.

#### R1 · Parity with Codex on the same model, at lower cost
With the same model, frond solves at least as many Terminal-Bench 2.1 tasks as Codex CLI (within 5 points), at lower cost per solved task.
- Done when: P3's report shows it.
- Status: unmeasured · Blocked on: P3 · Source: design.md R1.

#### R2 · Every change is shown, and a turn's net change is reviewable
Every change in a turn is shown as a diff, including command-made ones, and the turn's net change can be reviewed at the end.
- Done when:
  - each mutation kind (edit, create, delete, chmod, symlink, command) emits a diff;
  - a net-change view exists;
  - changes to ignored files and non-git folders are shown, or documented as unsupported.
- Status: partly done; per-change diffs in git workspaces only · Blocked on: no plan step yet · Source: design.md R2.

#### R3 · `/undo` restores frond's changes and keeps later changes by others
- Done when: P2's test passes.
- Status: fails today · Blocked on: P2 · Source: design.md R3.

#### R4 · Stopping is prompt and final
Esc halts the turn within a second, and no tool runs after the stop is acknowledged.
- Done when: the scripted harness measures stop latency at P95 ≤ 1 s, and a test shows no tool effect after the turn ends.
- Status: mid-turn messages and queueing tested; stop latency unmeasured · Blocked on: no plan step yet · Source: design.md R4.

#### R5 · Your words cannot be confused with tool output
- Done when: P1's marker test passes.
- Status: done in 3c188c9, with P1 · Blocked on: nothing · Source: design.md R5; [Compaction Laundering](https://arxiv.org/abs/2610.29869).

#### R6 · No unapproved writes outside the workspace, network use or credential use
- Done when: P1 and P4 are done.
- Status: holds for the REPL worker (P1, 3c188c9) and for read-only agents' commands. The main agent's commands still run with your permissions and credentials, which P4 closes. See I13 for Landlock's limits · Blocked on: P4 · Source: design.md R6.

#### R7 · The agent can rewind its context and the workspace together
- Done when: P5's rewind test passes.
- Status: missing · Blocked on: P5 · Source: design.md R7; W10.

#### R9 · An incompatible DSPy fails at startup
- Done when: P6b is done.
- Status: missing · Blocked on: P6b · Source: design.md R9.

#### R11 · Works on macOS
- Done when: V3 is done.
- Status: Linux only · Blocked on: V3 · Source: design.md R11.

## Unknowns

U2, U4, U5 and U6 are under Waiting on you.

#### U1 · Daily driver or research vehicle
- Done when: answered.
- Status: done in 79155cf; a research vehicle (your answer, 2026-11-03) · Blocked on: nothing · Source: design.md "Unknowns".

#### U3 · How long you pause between turns
A 1-hour cache lifetime pays only if enough gaps between turns last 5–60 minutes (A7), and frond does not log gap lengths.
- Done when: frond logs turn start and end times, and a week of sessions gives the distribution.
- Status: open · Blocked on: A7's logging, then use · Source: design.md "Unknowns".

## Not verified

V1, V2, V3 and V4 are all under Waiting on you.

## Assumptions to test

A8 is under Waiting on you.

#### A1 · The model opens and closes scopes without being told each time
- Done when: P5's runs report begin and end calls per turn. For comparison, Spine's agents closed 224 scopes across seven projects.
- Status: open · Blocked on: P5 · Source: Spine.

#### A2 · Collapsing a closed scope hides nothing needed later
- Done when: P5's runs report how often `history_step` is called on collapsed steps.
- Status: open · Blocked on: P5 · Source: design.md "The turn's state".

#### A3 · Listing stale names after an abandon keeps the model off discarded values
- Done when: a scripted test and P5's runs show stale names going unused, or report the rate at which they are used.
- Status: open · Blocked on: P5 · Source: design.md "The turn's state".

#### A4 · Rewinds need a verifier signal
- Done when: P5's runs split rewinds and their outcomes by whether the task has tests. AgentRewind had checklist feedback.
- Status: open · Blocked on: P5 · Source: AgentRewind.

#### A5 · Terminal-Bench turns rarely reach the fold budget, so P5 needs a long-horizon set
- Done when: P0 reports how many turns reached the fold budget (K7).
- Status: open · Blocked on: P0 · Source: design.md "The turn's state".

#### A6 · Edit friction
Editing through Python string literals may cost frond extra output tokens and failed edits; Claude spent 39.9% more output tokens this way in the [restriction study](https://arxiv.org/abs/2607.10569).
- Done when: P0 and P3 logs give syntax errors and failed edits per edit, and output tokens per changed line. If these are high, decide on a raw patch output field.
- Status: open · Blocked on: P0 · Source: prior-art assessment; design.md "Other decisions".

#### A7 · When a 1-hour cache lifetime pays
It pays when more than about 0.65·T/H of the gaps between turns last 5–60 minutes (T = tokens a turn adds, H = history so far).
- Done when: frond logs gap lengths, T and H, and the decision is recorded here.
- Status: open · Blocked on: the logging is not built · Source: design.md "Other decisions"; [Anthropic's caching docs](https://docs.claude.com/en/docs/build-with-claude/prompt-caching).

#### A9 · The per-step message layout changes accuracy as well as cost
PR #3's layout was chosen for caching; nothing yet shows its effect on success.
- Done when: an A/B on P0's tasks between DSPy's default ChatAdapter and `FrondAdapter` reports pass rates.
- Status: open · Blocked on: P0 · Source: prior-art assessment, "What I couldn't establish".

#### A10 · Inline scopes can replace sub-agents for sequential subtasks
- Done when: P5's runs show fewer sub-agent calls with scopes on and no score loss. In Spine, recursive sub-agents matched its score at 3.8× the cost.
- Status: open · Blocked on: P5 · Source: Spine.

#### A11 · Offline prompt optimization (GEPA) gains hold on held-out tasks
- Done when: an optimization run with a held-out split, gated on P3's suite as a regression check, reports no regressions.
- Status: open · Blocked on: P3, and a reward (I11) · Source: [regression-aware optimization study](https://arxiv.org/abs/2607.14004).

#### A12 · Confining the worker costs no capability
Every effect of REPL code already goes through host tools, so a read-only worker without network access loses nothing.
- Done when: P1's suite passes with the worker confined, and P0's runs show no task where REPL code needed network access or writes outside temp.
- Status: half done; all 143 tests and `frond --demo` pass with the worker confined (3c188c9). The live half waits on P0 · Blocked on: P0 · Source: design.md "Containment and provenance".

#### A13 · Native tool-call rendering for provenance
Rendering past steps as native tool calls and results would let provider roles show where text came from, but it changes what the model sees itself doing.
- Done when: an experiment with it on and off reports pass rates on P0's tasks and results on an injection test set.
- Status: open · Blocked on: P0 · Source: Compaction Laundering; design.md "Containment and provenance".

## Renames

#### N1 · `Compacted` → `Folded`
The `Compacted` event (`src/frond/events.py:207`) and the `compacted` hook describe what everything else calls folding.
- Done when: no `Compacted` or `compacted` identifiers remain, and the tests pass.
- Status: open · Blocked on: nothing · Source: design.md "Vocabulary".

#### N2 · `Record.scope` → `Record.agent`
`Record.scope` names the sub-agent a step belongs to and would clash with P5's scopes.
- Done when:
  - `steps.jsonl` writes `agent`;
  - readers still accept `scope` in existing logs;
  - `bench/frond_harbor.py` reads the new name;
  - the tests pass.
- Status: open · Blocked on: nothing; must land before P5 · Source: design.md "Vocabulary".

#### N3 · `Checkpoints` → `UndoJournal`
This keeps "checkpoint" free for an aligned savepoint of transcript and workspace.
- Done when: renamed, and the tests pass.
- Status: open · Blocked on: nothing · Source: design.md "Vocabulary".

## Uncalibrated numbers

Every row is open, blocked on P0's logs (or P3's for larger samples), and sourced from design.md "Traceability". Each row is done when the named measurement is recorded here and the value is kept or changed with a reason.

| ID | Number | Where | Measurement that calibrates it |
|---|---|---|---|
| K1 | 40 REPL steps per turn | `src/frond/agent/session.py:78`, `src/frond/cli.py:51` | share of turns that hit the limit |
| K2 | 16 steps per sub-agent | `src/frond/agent/session.py:84` | share of sub-agent runs that hit it |
| K3 | 16,000 characters of step output shown | `src/frond/agent/session.py:83` | how often output is cut, and whether the next step re-reads it |
| K4 | 24,000 characters of command output shown | `src/frond/agent/tools.py:50` | the same, for commands |
| K5 | 300-line view window | `src/frond/agent/tools.py:47` | how often consecutive views page through one file |
| K6 | 32,000 output tokens per reply | `src/frond/agent/lm.py:66` | how often a reply hits the limit |
| K7 | fold budget: 45% of the window, at most 150,000 tokens | `src/frond/agent/session.py:204` | fold frequency, and `history_step` use after folds |
| K8 | 3.6 characters per token | `src/frond/agent/session.py:206` | characters per token measured from provider usage |
| K9 | last 4 steps kept unfolded | `src/frond/agent/rlm.py:111` | how often folded steps are re-read |
| K10 | 8,000 characters of earlier user messages shown verbatim | `src/frond/agent/session.py:127` | how often earlier messages fall out of the preview |
| K11 | 20 diffs shown per command | `src/frond/agent/tools.py:51` | how often one command changes more than 20 files |
| K12 | snapshots switched off past 2 s | `src/frond/agent/snapshots.py:23` | snapshot times on large repositories |
| K13 | 40 REPL names listed | `src/frond/agent/_worker.py:49` | how many names a REPL typically holds |
| K14 | BM25 k1 = 1.2, b = 0.75 | `src/frond/agent/steplog.py:30` | whether `history_search` hits answer real queries |
| K15 | resource guards (listed below) | `src/frond/agent/session.py`, `tools.py`, `steplog.py`, `checkpoints.py`, `tui/app.py` | which of them bind in practice |

K15 covers these guards:
- attachments: 120,000 characters;
- stored output: 200,000 characters;
- directory snapshots: 50 MB;
- step timeout: 600 s;
- LLM calls: 80 per turn and 40 per sub-agent;
- preview limits: 20,000 for request, 24,000 for workspace, 12,000 for history, 6,000 for attachments, and 8,000, 8,000 and 16,000 for the sub-agent fields;
- mentions: 400,000 bytes.

## Ideas and gaps without a decision

I3 is under Waiting on you.

#### I1 · ACP support
Speak the [Agent Client Protocol](https://agentclientprotocol.com/) so frond can run inside Zed and Toad; the prior-art assessment called it "worth adding later".
- Done when: decided (build or drop), with the reason here.
- Status: open · Blocked on: a decision · Source: prior-art assessment, 2026-11-03.

#### I2 · Upstream the message layout and extension hooks to DSPy
The cache-friendly layout, and hooks that would replace frond's overrides of private methods, could live in `dspy.RLM` itself.
- Done when: decided; if yes, the upstream issue or PR is linked here.
- Status: open · Blocked on: a decision · Source: prior-art assessment; design.md "Other decisions", DSPy coupling.

#### I4 · Redact secrets in persisted logs
Command output and file reads can contain secrets, and `steps.jsonl` and the session files keep them, with file mode 0600.
- Done when: decided; if yes, redaction lands with tests.
- Status: open · Blocked on: a decision · Source: gap found while writing this file.

#### I5 · Show "esc stops the command" while a message waits
A mid-turn message sent during a long foreground command waits until that command ends.
- Done when: the TUI shows the hint whenever a message is pending and a command has run for more than a few seconds, with a test.
- Status: open · Blocked on: nothing · Source: design.md "Other decisions", Intervention.

#### I6 · The truncation note tells the model how to narrow
[TurnCost](https://arxiv.org/abs/2610.15093) found that a narrowing hint after truncation made 76.9% of next actions narrow the query, against 44% with bare truncation; frond's note gives only the log path.
- Done when: the note for cut-off command output suggests narrowing, such as `rg` or `sed -n` on the log path, and a test checks it.
- Status: open · Blocked on: nothing · Source: design.md "Traceability".

#### I7 · An inline rendering option
frond draws on the alternate screen (`src/frond/tui/terminal.py:24`), so its output never reaches the terminal's own scrollback, search and copy.
- Done when: decided (keep, or add an inline mode).
- Status: open · Blocked on: a decision · Source: gap found while writing this file.

#### I8 · Default model IDs may be stale
`PROVIDER_DEFAULTS` (`src/frond/agent/lm.py:13`) names models chosen from memory, such as `gemini/gemini-3.1-pro-preview` and `openai/gpt-5.4-mini`.
- Done when: each default is confirmed or replaced, citing the provider's current model list.
- Status: open · Blocked on: nothing · Source: gap found while writing this file.

#### I9 · Does GPT-5.4-mini write literal `\n` into scripts?
frond's default OpenAI sub-model, which runs sub-agents, did this in the [Bitter Lesson study](https://arxiv.org/abs/2608.06370). frond sends code as text, so it may not.
- Done when: P0 includes an OpenAI run with sub-agents, and the result is recorded.
- Status: open · Blocked on: an OpenAI key (P0) · Source: prior-art assessment, open questions.

#### I10 · Does `plan()` still help?
Amp [dropped its TODO tool](https://ampcode.com/news/todos-are-done), but frond still offers `plan()` (`src/frond/agent/tools.py:949`).
- Done when: an ablation on P0's tasks with `plan()` removed is reported.
- Status: open · Blocked on: P0 · Source: prior-art assessment, open questions.

#### I11 · Self-improvement with a regression gate (bet 6)
Optimize frond's DSPy prompts offline with GEPA, gated on held-out tasks and P3's suite, with versioned prompt files. The open question is which reward avoids rewarding shortcuts: [Prime Agent](https://arxiv.org/abs/2608.23552) kept an exploit.
- Done when: a reward is chosen and recorded, then A11 runs.
- Status: open · Blocked on: P3, and the reward choice · Source: prior-art assessment, bet 6.

#### I12 · Load this file at launch
`frond/CLAUDE.md` loads only once a session reads or writes a file under `frond/`, so a session that starts at the repository root sees these rules only after it touches frond.
- Done when: decided; if yes, a root `CLAUDE.md` imports `frond/CLAUDE.md`.
- Status: open · Blocked on: your decision · Source: [Claude Code memory docs](https://code.claude.com/docs/en/memory), "How CLAUDE.md files load".

#### I13 · Under Landlock alone, the REPL can still read and leak frond's environment
Two limits apply only where user namespaces are blocked, such as Ubuntu 24.04 desktops:
- the confined worker can read frond's own environment, API keys included, through `/proc/<pid>/environ`;
- Landlock does not restrict UDP.

So code that gets around the audit hook with ctypes could send a key out in a DNS query. In namespace mode the `/proc` read fails (EACCES), and the network is gone.
- Done when: decided. One option is to make frond's process non-dumpable (`prctl(PR_SET_DUMPABLE, 0)`, as ssh-agent does), which closes the `/proc` read for every process of the user, at the cost of attaching debuggers. If built, a test shows the read failing under Landlock.
- Status: open · Blocked on: a decision · Source: found while building P1 (probe on Linux 6.18, Landlock ABI 7).

## Pull requests

PR2 is under Waiting on you.

#### PR3 · PR #3 stays draft until P1 lands
[PR #3](https://github.com/ethan-wickstrom/experiments/pull/3) (`claude/frond-context-engine`, stacked on PR #2) is a draft with no reviews. It leaves draft only after P1 is committed to it.
- Done when all of these hold:
  - P1 is on the branch (done in 3c188c9);
  - the description cites AgentRewind precisely: 62.2% with no rewind, 43.9% with the context rewound alone, 87.8% with both (done 2026-11-03, with P1 and the docs added to it);
  - the description ends with the PR attribution lines (done 2026-11-03);
  - the PR is marked ready.
- Status: open; P1 is on the branch · Blocked on: your go-ahead to leave draft, which also starts the Codex and Devin reviews · Source: PR #3; your instruction of 2026-11-03.

Safety-net check-ins for both PRs exist only in the session that created them. The next is at 08:34 UTC on 2026-11-03, and the empty count reset with the P1 push. A new session has none, and should subscribe to both PRs itself.

## Decisions that close earlier ideas

Reopen one only with new evidence.

| ID | Decision | Reason | Source |
|---|---|---|---|
| X1 | No lossy summaries of context | W8: a lossless log scored 73.1% against 19.9% for summaries; summaries drop instructions | [Scroll](https://arxiv.org/abs/2608.21690), [compaction study](https://arxiv.org/abs/2610.31778) |
| X2 | No context the model edits itself | injection risk; gains were in compute only | [Context Language Models](https://arxiv.org/abs/2609.37725) |
| X3 | No native JSON tool calls | C1; no measured gain | Bitter Lesson study; restriction study |
| X4 | No copy of the RLM loop inside frond | breaks C1 as written | design.md "Other decisions" |
| X5 | No deeper recursion (sub-agents of sub-agents) | two levels did worse than one | [RLM reproduction](https://arxiv.org/abs/2603.02615) |
| X6 | No Prime Agent-style background sub-agents for now | they paid off in multi-day runs, not interactive edits | prior-art assessment |
| X7 | No routing of steps to cheaper models | it raised cost in half of TurnCost's settings | TurnCost |
| X8 | Read-only by command patterns or an allowlist | replaced by the OS sandbox in 5837329 | PR #2 review thread on `tools.py` |
| X9 | No overlay copy-on-write for commands | changing the lower layer while mounted is undefined, and W2 says you will change it | [overlayfs docs](https://docs.kernel.org/filesystems/overlayfs.html) |
| X10 | No filesystem snapshots (btrfs, APFS) | not portable | design.md "Recoverability" |
| X11 | No ghost commits in your repository | they write into your repo; Codex abandoned them in v0.126 | design.md "Recoverability" |
| X12 | No Spotlighting marks on all tool output by default | marks would leak into exact strings copied into `edit()` | [Spotlighting](https://arxiv.org/abs/2403.14720) |
| X13 | No separate message per mid-turn message | tool output shares the user role | design.md "Containment and provenance" |
| X14 | No StateHarness diagnostic sessions, or CarryOn compiler and grounder, for now | extra model calls; the REPL already holds the objects | design.md "The turn's state" |
| X15 | No online self-editing of prompts | nothing gates it | design.md "Other decisions" |
| X16 | No Windows support | the TUI depends on termios | C4 |
| X17 | PR #2's mistaken commit message is left as is | it claims a mouse-input fix made in an earlier commit, and rewriting pushed history is destructive | first report on PR #2, 2026-11-02 |
