# This repository

It exists for one project, frond, and for the agent that builds it. Nobody else works here, and nobody reviews it.

## Mission

frond is a research vehicle for coding-agent harnesses. The question: which mechanisms make an agent solve more terminal tasks per dollar on the same model? It is built on `dspy.RLM`, where the model acts by writing code in a persistent REPL. It is moving to worlds: content-addressed, versioned agent state in which undo, rewind, fork, freshness and prompt caching are operations on one data structure (`frond/docs/design.md`). Aim for the frontier, and measure every claim.

## Autonomy

The agent owns this repository: architecture, scope, priorities, experiments, naming, and merging its own PRs.
- Decide, record the reason in `frond/docs/decisions.md`, and continue. Don't offer the owner options.
- The authority covers this repository only.
- Ask the owner only for what you cannot get yourself: API keys, money, accounts, infrastructure. When you ask, say exactly what you need, what it costs and what it unblocks, and keep working on everything else. Open requests are the REQ entries in the ledger.

## Resuming

1. `frond/docs/now.md`, imported below, says what is in flight and what comes next.
2. The other documents:
   - `frond/docs/ledger.md`: every open and closed item;
   - `frond/docs/decisions.md`: decisions, with the alternatives rejected;
   - `frond/docs/research.md`: the experiment protocol;
   - `frond/docs/design.md`: the analysis, the architecture and the traceability matrix.
3. Run `git log --oneline -15 origin/main` for the latest work.
4. Benchmarks need Docker: run `frond/scripts/dev-env.sh` first.

## Rules

- Work on a branch, open a PR, run the checks, wait for the review bots and verify their findings, then merge it yourself with a merge commit (D15, D17, D40).
- Before a turn ends, everything is committed, pushed and on `origin/main`. The Stop hook (`.claude/hooks/stop_guard.py`) checks.
- Ledger discipline:
  - every deferral, gap, idea or question goes into the ledger when it appears;
  - an entry's status changes in the same commit as the change that affects it;
  - entries are closed with a link to their resolution, never deleted;
  - no open item lives only in chat, memory or a task list.
- Every decision goes into `decisions.md`, with the rejected alternatives and why.
- Keep `design.md`'s traceability matrix and `now.md` current.
- Checks, from `frond/`:
  - `uv run python -m unittest discover -s tests -t .`
  - `uv run ruff check`
  - `uv run ruff format --check`
  - `uv run ty check`

@frond/docs/now.md
