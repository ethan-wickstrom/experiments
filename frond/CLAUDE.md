# frond

The repository's rules are in `../CLAUDE.md`; this file adds what is specific to frond.

## Mission

frond is a research vehicle for coding-agent harnesses. The question: which mechanisms make an agent solve more terminal tasks per dollar on the same model? It is built on `dspy.RLM`, where the model acts by writing code in a persistent REPL. It is moving to worlds: content-addressed, versioned agent state in which undo, rewind, fork, freshness and prompt caching are operations on one data structure (`docs/design.md`). Aim for the frontier, and measure every claim.

## Resuming

1. `docs/now.md`, imported below, says what is in flight and what comes next.
2. The other documents:
   - `docs/ledger.md`: every open and closed item; open requests to the owner are its REQ entries;
   - `docs/decisions.md`: decisions, with the alternatives rejected;
   - `docs/research.md`: the experiment protocol;
   - `docs/design.md`: the analysis, the architecture and the traceability matrix.
3. Benchmarks need Docker: run `scripts/dev-env.sh` first.

## Rules

- Keep `docs/design.md`'s traceability matrix and `docs/now.md` current.
- Checks, from `frond/`:
  - `uv run python -m unittest discover -s tests -t .`
  - `uv run ruff check`
  - `uv run ruff format --check`
  - `uv run ty check`

@docs/now.md
