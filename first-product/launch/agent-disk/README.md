# Guide page: "What coding agents and dev tools leave on your Mac" (for getsizewise.app/agent-disk)

- `agent-disk.html`: drop-in page matching the live guides (head, header, footer and inline script copied from /developer-caches and /docker-disk; the Cloudflare script Cloudflare injects is left out on purpose).
- `agent-disk.md`: the same text plus a source table mapping every claim (77 rows) to the tool's own docs or source, checked 2026-10-15.

Covers worktrees (git), Claude Code (worktrees, transcripts, checkpoints, `claude purge`), Codex (worktrees, sessions, `codex delete`, the open .git objects issue #29388 with a safe `git gc` path), Conductor, Cursor, node_modules with npm / pnpm / Bun and uv venvs (clones and hard links, why deleting frees less than the size), Rust target and the cargo registry, Playwright, Hugging Face (`hf cache`; `huggingface-cli` was removed in huggingface_hub 1.0), Ollama, LM Studio, and links to the existing Xcode, Docker and package-cache guides. Ends with "Advice to skip".

To ship: copy to the site root as agent-disk.html (or /agent-disk per the site's routing), add it to sitemap.xml and the footer, and to llms.txt under Guides.
