# "What a week of coding agents adds to a Mac" (demo page for getsizewise.app)

A drop-in page for the Sizewise site, built from the site's own `map.js`, `explorer.js` and `site.css`, in the same pattern as `/macos`. It maps a sample developer's home folder on Monday and on Friday and colors what changed, the way Show Changes does in the app.

Files:
- `demo-dev-week.js`: the two sample trees. Made-up projects, seeded so both days match wherever nothing changed. Folder paths are where the tools put things (Cargo `target`, Xcode `DerivedData` and `CoreSimulator/Devices`, Docker Desktop's `Docker.raw`, `~/Library/Caches/ms-playwright`, `~/.cache/huggingface/hub`, `~/.claude/projects`, `~/.codex/sessions`, worktrees in `.claude/worktrees`). Sizes are typical, not measured; the page says so in its lede and in "How this was made".
- `dev-week.html`: the page. Facts, a "What changed since Monday / Kinds of files" toggle, the map, Grew the most / New / Removed, five stories with "Show on the map", and the usual footer and Get Sizewise block.
- `screenshots/`: full page (light) and map crops (light, dark) for posts.

Tested 2026-10-15 in Chromium 1194 (Playwright), light and dark, no console errors. Rendered numbers: Monday 88.8 GB, Friday 152 GB, grew 63.7 GB; largest changes: Rust target +22.9 GB, a model download +16.4 GB, Docker.raw +9 GB, six worktrees 7.22 GB (Monday's one was 918 MB), simulators and Xcode +5.54 GB.

To ship: copy both files to the site root next to `map.js`, add `/dev-week` to `sitemap.xml` and the footer if wanted. Before shipping, confirm the worktree location sentence against the developer guide's sources (Claude Code's `.claude/worktrees` is cited from a third-party hook README; the guide draft checks it against Claude Code's docs).

Ethan's call: a real before/after of his own home folder (scripts/atlas.ts, names anonymized) would be stronger than a sample, but takes a week to collect.
