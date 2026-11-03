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
or helper functions around while you talk to it.

## What you see

The TUI streams each step as it is written: the model's reasoning, then its code, then the effects of that code as
cards — a unified diff with line numbers and syntax highlighting for every file it creates, edits, moves or deletes,
and a terminal card with live output and exit status for every command. The final answer streams as Markdown,
decoded on the fly from the model's `SUBMIT("""...""")` call.

- **Send and stop.** Enter sends. While the agent works, the send button becomes a stop button (click it or press
  Esc), and Enter queues your next message; queued messages run in order when the turn ends, and ↑ pulls the last one
  back for editing.
- **@-mentions.** Type `@` to fuzzy-find files and folders; their contents are attached to the request as a REPL
  variable rather than pasted into the prompt.
- **Context meter.** The status line shows a bar that fills as the latest prompt approaches the model's context window
  (looked up from DSPy's model metadata), plus the session cost. Long turns compact their own earlier steps.
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
  tells the agent it happened. Changes made by shell commands such as formatters are not tracked.
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

Keys: Enter send · Ctrl+J, Alt+Enter, Shift+Enter or a trailing `\` new line · Esc stop or close a popup ·
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
  per-variable previews (the full request, the tail of the conversation), and in-turn compaction.
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

## Developing

```sh
uv sync
uv run python -m unittest discover -s tests -t .   # 111 tests: decoder, layout, tools, REPL, agent turns, undo, sessions, the app
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
