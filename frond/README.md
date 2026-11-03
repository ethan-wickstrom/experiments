# frond

frond is a coding agent for the terminal whose every action is a step of a
[Recursive Language Model](https://arxiv.org/abs/2512.24601). It runs on
[`dspy.RLM`](https://dspy.ai/current/api/modules/RLM/): instead of calling tools through JSON, the model writes Python
in a persistent REPL where reading, searching, editing, running commands, querying sub-models and spawning sub-agents
are ordinary functions. Its only runtime dependency is DSPy; the TUI is built on the CPython standard library
and runs on macOS and Linux.

```sh
uv tool install ./frond          # or: uv run frond, from this directory
frond --demo                     # a scripted session in a sample project, no API key needed
ANTHROPIC_API_KEY=... frond      # work on the current directory
frond -p "why does test_api.py fail?"     # headless: progress on stderr, answer on stdout
```

## Why RLM-centric

An RLM treats context as data in an environment rather than text in the prompt: the root model sees metadata and
short previews, inspects the rest with code, and recursively calls models on the slices that need semantic reading.
For a coding agent that changes what a step can do. One step can grep a repository, read the three files that matter,
and print only the lines it needs; another can fan out `llm_query_batched` over forty files to summarise them in
parallel, or hand a whole investigation to `subagent()`, a nested read-only RLM with a fresh context. Large results
stay in variables instead of the context window, which is the agent's scarcest resource, as
[Amp's context-management guide](https://ampcode.com/guides/context-management) argues. Writing actions as code
rather than JSON tool calls also follows the evidence from [CodeAct](https://arxiv.org/abs/2402.01030) and
Anthropic's write-up on [code execution with tools](https://www.anthropic.com/engineering/code-execution-with-mcp).

The REPL namespace persists across steps *and* across conversation turns, so the agent can keep notes, parsed data
or helper functions around while you talk to it. Each step lists the names the code has defined, so later turns know
what is there.

## Context that is lossless, cache-friendly and steerable

- **Nothing is summarised away.** Every user message, step (reasoning, code, full output) and answer goes into an
  append-only step log, kept beside the session file. The agent searches it with `history_search('words')` and reads
  any record back exactly with `history_step(seq)`. When a turn outgrows its budget, early steps are folded into one
  index line each (seq, headline, first output line), with the recovery instructions right there; no summary is
  written. The user's own words are never shortened. The design follows
  [Scroll](https://arxiv.org/abs/2608.21690), where a lossless log the model queries beat summarised history 73.1%
  to 19.9%. It also sidesteps what summaries do wrong:
  - they drop the user's instructions about how to work ([arXiv 2610.31778](https://arxiv.org/abs/2610.31778));
  - they mix the summariser's guesses in with facts ([arXiv 2610.20927](https://arxiv.org/abs/2610.20927));
  - they can launder injected text into fake user turns ([arXiv 2610.29869](https://arxiv.org/abs/2610.29869)).
- **The prompt is laid out for the provider's cache.** `dspy.RLM` sends the REPL history as one ever-growing
  message, which Anthropic's [prompt cache](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) can
  never reuse. frond sends each step as its own pair of turns and marks the latest reply as a breakpoint, so each step
  reads all earlier ones from the cache. A test replays a 10-step turn through the real Anthropic payload builder and
  a simulator of the documented cache rules: the cached share of input exceeds 70% and the cache-priced cost halves.
  The meter shows the cached share of each prompt.
- **Steer while it works.** Enter sends your message into the running turn; the model reads it before its next step,
  marked as newer than everything above it, and it is restated at the end of the prompt while the turn lasts. Tab
  queues it for after the turn instead. A message the turn never reaches runs next.

## What you see

The TUI streams each step as it is written: the model's reasoning, then its code, then the effects of that code as
cards — a unified diff with line numbers and syntax highlighting for every file it creates, edits, moves or deletes,
and a terminal card with live output and exit status for every command. The final answer streams as Markdown,
decoded on the fly from the model's `SUBMIT("""...""")` call.

- **Send, steer and stop.** Enter sends. While the agent works, the send button becomes a stop button (click it or
  press Esc). Enter then steers the running turn and Tab queues; queued messages run in order when the turn ends, and
  ↑ pulls the last one back for editing.
- **@-mentions.** Type `@` to fuzzy-find files and folders; their contents are attached to the request as a REPL
  variable rather than pasted into the prompt.
- **Context meter.** The status line shows a bar that fills as the latest prompt approaches the model's context window
  (looked up from DSPy's model metadata), how much of it the provider served from its cache, and the session cost.
- **Approvals.** Edits inside the workspace and ordinary commands run freely. Recursive deletes, history-rewriting
  git commands, pushes, `sudo`, piping downloads into a shell, and writes outside the workspace ask first (`--yolo`
  never asks; `--read-only` forbids changes and runs commands in the read-only sandbox below).
- **Read-only sandbox.** Sub-agents are read-only, and so is `--read-only` mode. Their commands run in an OS
  sandbox in which every filesystem write fails. Anything can still be read or run, including test suites.
  - On Linux: a user and mount namespace with every mount read-only and no network. Landlock is the fallback
    where user namespaces are blocked.
  - On macOS: Seatbelt (untested in this build).
  - Where no sandbox is available, read-only agents get no shell.
- **Undo.** Every change goes through frond's tools, so each turn checkpoints the original bytes of the files it
  touches; `/undo` restores the last turn exactly (edits, new files and their new folders, deletions, renames) and
  tells the agent it happened. In a git workspace it also covers what shell commands change (formatters,
  codegen, `sed -i`). frond snapshots the worktree around each command into a private index and object store,
  so `.git` is untouched, and shows a diff for each file the command changed. Files git ignores, and commands
  that move `HEAD`, are left alone.
- **Continue.** Each conversation is saved per workspace (under `~/.local/share/frond`, readable only by you);
  `frond --continue` picks up the most recent one, so the agent knows what was said and changed before.
- **Background jobs.** `sh(..., background=True)` starts dev servers and watchers that outlive a step; `/jobs` and
  `/kill` manage them.
- **Terminal craft.** Truecolor with a 256-colour fallback, dark and light palettes derived from your terminal's
  actual background (queried with OSC 11), diff-based rendering inside
  [synchronized updates](https://gist.github.com/christianparpart/d8a62cc1ab659194337d73e399004036), resize reflow,
  bracketed paste, mouse wheel and click-to-expand, Ctrl+Z suspend, clickable file references via
  [OSC 8](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda), and the
  [kitty keyboard protocol](https://sw.kovidgoyal.net/kitty/keyboard-protocol/) where available (so Shift+Enter works).

Keys: Enter send (steer while working) · Tab queue while working · Ctrl+J, Alt+Enter, Shift+Enter or a trailing `\` new line · Esc stop or close a popup ·
Ctrl+C clear, stop, or quit when pressed twice · PgUp/PgDn or the wheel scroll · Ctrl+O full details ·
`/help` for the rest. Hold Shift (Option in iTerm2) to select text with the mouse, or use `/copy`.

## Models

Any model string DSPy accepts works (`--model provider/name`). Without one, frond picks defaults from your keys:
`ANTHROPIC_API_KEY` selects `anthropic/claude-sonnet-5-5` with `claude-haiku-5-5` for sub-queries,
`OPENAI_API_KEY` selects `openai/gpt-5.5` with `gpt-5.4-mini`, and `GEMINI_API_KEY` selects Gemini 3.1 Pro with
Gemini 3 Flash. `FROND_MODEL` and `FROND_SUB_MODEL` override them. Provider-side prompt caching is enabled for
natively supported providers (`--no-prompt-cache` turns it off).

Project instructions in `AGENTS.md` (or `CLAUDE.md`) from the git root down to the working directory, plus
`~/.config/frond/AGENTS.md`, are included in every turn.

## How it works

```
 keys, mouse ──► tui.app ──start_turn──► agent.session ──► FrondRLM (dspy.RLM subclass)
      ▲             ▲                          │                 │ generate_action (streamed)
      │             └──── events (queue) ◄─────┤                 ▼
   terminal                                    │        ReplSession: CPython worker process
                                               │          ├─ tool calls ──► Toolbox (host): fs, grep, sh, jobs…
                                               │          └─ llm_query ──► sub-LM, subagent() ──► nested FrondRLM
                                               └──► LM stream sink (send_stream) ──► reasoning/code deltas
```

- `agent/rlm.py` subclasses `dspy.RLM` to add events, cancellation, a tool reference with real signatures,
  per-variable previews (every user message verbatim, then the latest turns), the defined-names digest, steering
  messages at step boundaries, step records, and folding of long turns into an index.
- `agent/adapter.py` lays each step's prompt out as conversation turns, with what changes per step at the end and a
  cache breakpoint on the latest reply. It keeps the ChatAdapter's text protocol, so parsing and streaming are DSPy's.
- `agent/steplog.py` is the conversation's lossless record (JSONL, BM25 search) behind `history_search` and
  `history_step`; `agent/snapshots.py` brackets shell commands with private git snapshots for `/undo`.
- `agent/repl.py` and `agent/_worker.py` implement DSPy's `CodeInterpreter` protocol with a persistent CPython
  process: live stdout, SIGINT interruption that keeps the namespace, per-step timeouts, and a
  [PEP 578](https://peps.python.org/pep-0578/) audit hook that steers file writes and subprocesses onto the tools,
  where the user can see them. It is a guard rail, not a sandbox: the main agent's commands run with your
  permissions.
- `agent/_sandbox.py` is the read-only sandbox, a stdlib-only helper. Before exec'ing the command it applies the
  strongest restriction available, then checks that the workspace really is unwritable; otherwise it runs nothing.
- `agent/streaming.py` is the `send_stream` sink DSPy writes chunks to; it parses the ChatAdapter's field markers
  incrementally and is also where a stopped turn aborts the in-flight LM call.
- `tui/` is a small immediate-mode TUI: an input decoder, a cell buffer with a diffing renderer, text wrapping that
  understands wide characters, a Markdown renderer and a syntax highlighter.

## Benchmarks

`bench/frond_harbor.py` plugs frond into [Harbor](https://harborframework.com), the harness behind
[Terminal-Bench](https://www.tbench.ai). It installs frond in each task's container from a wheel built from this
checkout, runs `frond -p --yolo --export …` on the task, and turns the exported record into Harbor's ATIF trajectory.
Every REPL step becomes a tool call with its output, so Harbor's viewer and leaderboard review see each command, and
tokens, cache reads and cost reach the results.

```sh
uv tool install harbor
export ANTHROPIC_API_KEY=...
PYTHONPATH=bench harbor run -d terminal-bench/terminal-bench-2-1 -a frond_harbor:Frond \
    -m anthropic/claude-sonnet-5-5 -n 8 -o jobs          # add -e daytona (or modal, e2b) to run without Docker
```

`frond -p --export DIR` writes the same record for any other harness: `steps.jsonl`, `usage.json` and `answer.md`.

## Developing

```sh
uv sync
uv run python -m unittest discover -s tests -t .   # 131 tests: decoder, layout, tools, REPL, agent turns, undo, sessions, the app
uv run ruff check && uv run ruff format --check && uv run ty check
```

The UI is built to be [feedback-loopable](https://ampcode.com/notes/feedback-loopable). `frond.tui.headless` drives
the real app without a terminal and renders frames as text or colour-accurate HTML:

```sh
uv run python -m frond.tui.headless --demo --type "add a flag" --wait --html frame.html
```

and `frond --script steps.json` replays scripted model steps (a JSON list of `{"reasoning", "code"}` objects) in the
real TUI, which makes interactive behaviour (queueing, stopping, approvals) reproducible. The test-suite uses the
same scripted engine, so every agent turn in it executes real code against a temporary workspace.
