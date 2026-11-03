# frond

@docs/open-items.md

Open items live in frond/docs/open-items.md. Add an entry whenever you defer something, find a gap, or I raise an idea. Update its status in the same commit as the change that affects it. Mark finished items done with the commit hash instead of deleting them. Never keep an open item only in chat or in the task list.

The reasoning behind the open items is in `docs/design.md`. Before committing, run `uv run python -m unittest discover -s tests -t .`, `uv run ruff check`, `uv run ruff format --check` and `uv run ty check` from `frond/`.
