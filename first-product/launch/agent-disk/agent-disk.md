# What coding agents and dev tools leave on your Mac

Coding agents often give each task its own copy of your project, and each copy gets its own dependencies and build files. Here is where the common agents and dev tools keep what they save, how long they keep it, and each tool’s own way to remove it.

What this page says about each tool comes from its own documentation, checked on October 15, 2026. If something here is out of date, [tell us](mailto:support@getsizewise.app) and we’ll fix it.

## Worktrees: a copy of your project for each task

Most of these tools use [Git worktrees](https://git-scm.com/docs/git-worktree): extra working folders for one repository. Worktrees share the repository’s history, but each has its own copy of your files. A new worktree starts with only the files Git tracks, so folders Git ignores, such as node_modules or a build folder, appear when you install and build in it, and each worktree gets its own. [OpenAI’s Codex docs](https://learn.chatgpt.com/docs/environments/git-worktrees) warn: “Worktrees can take up a lot of disk space. Each one has its own set of repository files, dependencies, build caches, etc.” How much each extra node_modules takes depends on the package manager, as the section on node_modules below explains.

- `git worktree list` lists a repository’s worktrees and the branch each one has checked out.
- `git worktree remove` and a worktree’s path deletes its folder, including ignored folders such as node_modules. Git refuses when the worktree has changed or untracked files, unless you add `--force`, which deletes those too. The branch stays. Delete it with [`git branch -d`](https://git-scm.com/docs/git-branch) when you no longer need it.
- `git worktree prune` clears Git’s records of worktrees whose folders were deleted another way.

## Claude Code

### Worktrees

`claude --worktree` and a name creates a worktree in .claude/worktrees at the root of your repository, on a new branch whose name starts with worktree-. The desktop app uses the same folder unless you change Worktree location in Settings > Claude Code. When you exit a worktree session and nothing in it changed, [Claude Code removes](https://code.claude.com/docs/en/worktrees) the worktree and its branch, asking first in a named session. When there’s work in it, Claude Code asks whether to keep it. Runs with `-p` leave their worktrees in place. Worktrees Claude made for subagents and background sessions are removed by a periodic sweep once they’re older than the cleanupPeriodDays setting, 30 days by default, unless they still hold work. In the desktop app, [archiving a session](https://code.claude.com/docs/en/desktop) removes its worktree.

### Transcripts

~/.claude/projects holds a transcript of each session: every message, tool call and tool result, including the contents of files Claude read. [Claude Code deletes](https://code.claude.com/docs/en/claude-directory) each one once it’s older than cleanupPeriodDays, 30 days by default. It keeps transcripts of sessions you started or last continued in Claude Desktop or Cowork at any age, unless you set desktopSessionCleanupPeriodDays.

### Checkpoints

~/.claude/file-history holds copies of files from before Claude edited them, which `/rewind` uses to restore your code. [Claude Code keeps](https://code.claude.com/docs/en/checkpointing) them for the 100 most recent checkpoints in a session, and the same sweep deletes them about 30 days after the session last saved one.

To remove one project’s transcripts and checkpoints at once, run `claude purge` and the project’s path. It shows what it will delete and asks first. It also deletes Claude’s memory notes for the project and its entry in ~/.claude.json, with its trust setting and the MCP servers you added for it. You can no longer resume or rewind its past sessions. Before Claude Code 2.1.288, the command was `claude project purge`.

## Codex

### Worktrees

Codex keeps the worktrees it makes in ~/.codex/worktrees. To use another folder, open Settings > Worktrees and change Worktree root. In the ChatGPT desktop app, [Codex keeps](https://learn.chatgpt.com/docs/environments/git-worktrees) your 15 most recent Codex-managed worktrees by default and deletes older ones. It also deletes a chat’s worktree when you archive the chat. It keeps the worktrees of pinned chats and of chats still running, and permanent worktrees. Before deleting one, it saves a snapshot of the work, and the chat offers to restore it. Worktrees the Codex CLI makes with `--worktree` go in the same folder, and [Codex’s source code](https://github.com/openai/codex/blob/e89b7c442c0433ad5167e72a5a25bb6d0712766a/codex-rs/worktree/src/settings.rs) shows the CLI doesn’t clean them up on its own.

### Sessions

Codex saves each session’s transcript in ~/.codex/sessions, and moves archived ones to ~/.codex/archived_sessions. Its docs don’t say it deletes them on its own. [`codex delete`](https://learn.chatgpt.com/docs/developer-commands?surface=cli) and a session’s ID or name deletes one for good. `codex archive` only hides it from the session picker and keeps the transcript.

### Checkpoints in your project

Codex’s docs don’t mention them, but in [an open issue](https://github.com/openai/codex/issues/29388) from June 2026, a user reported that Codex’s turn-diff checkpoints were written as Git objects into the project’s own .git folder, and that nothing removed them after newer checkpoints replaced them. In that user’s project, `git count-objects` counted 8,476 loose objects taking 101.86 GiB. A comment on September 30 says it still happens with codex-cli 0.159.2.

To check a project and get the space back:

1. In Terminal, in the project’s folder, run [`git count-objects -vH`](https://git-scm.com/docs/git-count-objects). Its size line is the space loose objects take, the kind the issue describes.
2. Quit Codex and other apps that use the repository, so nothing writes to it while Git cleans up.
3. Run [`git gc`](https://git-scm.com/docs/git-gc). It keeps every object a branch, tag, reflog or other ref still points to, and by default removes unreachable loose objects once they’re more than two weeks old.
4. To remove them whatever their age, run `git gc --prune=now`. Git warns that this “increases the risk of corruption if another process is writing to the repository concurrently.” It also removes work Git could otherwise still recover, such as a [stash you dropped](https://git-scm.com/docs/git-stash) by mistake.

A commenter on the issue notes that cleaning up “won’t stop Codex from re-creating snapshots,” so the space can build up again while the issue is open.

## Conductor and Cursor

### Conductor

[Conductor gives](https://www.conductor.build/docs/concepts/git-worktrees) each workspace its own worktree, usually in ~/conductor/workspaces, in a folder for each repository. Older workspaces can be in a .conductor folder inside the repository. Archive a workspace in Conductor when you’re done with it. You can [restore it later](https://www.conductor.build/docs/troubleshooting/issues) from the History pane.

### Cursor

[Cursor keeps](https://cursor.com/docs/cli/using) agent worktrees in ~/.cursor/worktrees, in a folder for each repository, whether they come from the editor or its CLI. Since Cursor 3.5, it [deletes older worktrees](https://cursor.com/docs/configuration/worktrees) to keep at most 25 on your Mac by default, counting every project, and the cursor.worktreeMaxCount setting changes that limit. Its docs add that worktrees “created by /worktree skills or git worktree add” can be deleted too. In the editor, `/delete-worktree` removes one when you’re done.

## node_modules and virtual environments

How much a project’s node_modules takes, and how much deleting it frees, depends on the package manager.

### npm

npm writes a full copy of every package into each project. [pnpm’s docs](https://pnpm.io/motivation) put it this way: “When using npm, if you have 100 projects using a dependency, you will have 100 copies of that dependency saved on disk.” Deleting an npm project’s node_modules frees about what it takes.

### pnpm

pnpm keeps one copy of each package file in its store, ~/Library/pnpm/store on a Mac, and `pnpm store path` prints the one in use. It puts those files in each project without copying their data: [on a Mac, its default](https://pnpm.io/settings/node-modules#packageimportmethod) is to clone them from the store, and to hard link them where it can’t clone. Run [`pnpm store prune`](https://pnpm.io/cli/store) to remove packages no project on your Mac uses. pnpm says it “is not harmful and has no side effects on your projects,” and downloads a removed package again if a later install needs it.

### Bun

Bun keeps the packages it downloads in ~/.bun/install/cache, and `bun pm cache` prints the folder in use. [On a Mac, its default](https://bun.com/docs/pm/global-cache) is to clone them into each project. [`bun pm cache rm`](https://bun.com/docs/pm/cli/pm) empties the cache. `bun pm cache prune` removes only packages Bun downloaded more than 30 days ago, including ones still in use, and Bun downloads them again when an install needs them.

### uv

uv keeps the Python packages it downloads and builds in ~/.cache/uv, and `uv cache dir` prints the folder in use. [On a Mac, its default](https://docs.astral.sh/uv/reference/settings/#link-mode) is to clone them into each virtual environment. [`uv cache prune`](https://docs.astral.sh/uv/concepts/cache/) removes entries uv no longer uses, and uv says it “is safe to run periodically.” `uv cache clean` removes everything, and uv downloads and builds packages again as it needs them.

A clone is an APFS copy that, [Apple says](https://developer.apple.com/documentation/foundation/about-apple-file-system), “occupies no additional space on disk”: both files share the same blocks until one of them changes. A hard link is a second name for the same file. Either way, a node_modules folder from pnpm or Bun, or a virtual environment from uv, looks as big as a full copy, but its package files share their data with the store or cache. Deleting the folder frees only the part no other file shares. The rest is freed only when nothing else, such as the store, the cache or another project, still uses it. [pnpm’s FAQ](https://pnpm.io/faq) explains the hard-link case: “that 1MB is the same space on the disk addressed from two different locations.”

## Rust build folders

[Cargo builds](https://doc.rust-lang.org/cargo/reference/build-cache.html) into a folder named target at the root of each project, so every project, and every worktree of one, has its own. Cargo cleans up its download cache on its own, but not target.

- Run [`cargo clean`](https://doc.rust-lang.org/cargo/commands/cargo-clean.html) in a project to delete its target folder. `cargo clean --dry-run` shows what it would delete. The next build compiles everything again.
- ~/.cargo/registry holds the crates Cargo downloaded: compressed .crate files in registry/cache and their unpacked sources in registry/src. When you build, [Cargo deletes](https://doc.rust-lang.org/cargo/reference/config.html#cache) files there it hasn’t used in 3 months, or in 1 month for files it can make again without a download. It skips this when it runs offline.

## Browsers and models

### Playwright

Playwright downloads Chromium, Firefox and WebKit to ~/Library/Caches/ms-playwright, and [its docs](https://playwright.dev/docs/browsers#managing-browser-binaries) say they take a few hundred megabytes. Playwright deletes a browser version once no Playwright installation on your Mac needs it. [`npx playwright uninstall`](https://playwright.dev/docs/browsers#uninstall-browsers) removes the browsers of the installation you run it from, and adding `--all` removes every installation’s. `npx playwright install` downloads them again.

### Hugging Face

Models and datasets you download with Hugging Face’s libraries go in ~/.cache/huggingface/hub, unless HF_HOME or HF_HUB_CACHE points somewhere else. [`hf cache ls`](https://huggingface.co/docs/huggingface_hub/guides/manage-cache) lists what’s there. `hf cache rm` and a repo ID, such as model/bert-base-cased, deletes one, and `hf cache prune` deletes revisions no branch or tag uses and unfinished downloads. Add `--dry-run` to see what either would delete. Version 1.0 of the huggingface_hub library [removed the older huggingface-cli command](https://huggingface.co/docs/huggingface_hub/concepts/migration), so guides that use `huggingface-cli delete-cache` are out of date.

### Ollama

[Ollama keeps](https://docs.ollama.com/faq) models in ~/.ollama/models, or the folder the OLLAMA_MODELS variable names. [`ollama ls`](https://docs.ollama.com/cli) lists your models, and `ollama rm` and a model’s name deletes one. `ollama pull` downloads it again.

### LM Studio

[LM Studio’s docs](https://lmstudio.ai/docs/app/advanced/import-model) show its models in ~/.lmstudio/models, in a folder for each publisher and model. You can [change that folder](https://lmstudio.ai/docs/app/basics/download-model) in its My Models tab. [`lms ls`](https://lmstudio.ai/docs/cli/local-models/ls) lists each model with its size, and the total. LM Studio’s docs don’t describe a command to delete a model.

## Xcode, Docker and package caches

Other Sizewise guides cover the rest of a developer’s disk: [Xcode’s DerivedData, archives and simulators](https://getsizewise.app/xcode-storage), [Docker Desktop’s disk image](https://getsizewise.app/docker-disk), [Homebrew, pip and npm caches](https://getsizewise.app/developer-caches), and [Android Studio’s SDK and emulators](https://getsizewise.app/android-storage).

## Advice to skip

- **Deleting a worktree’s folder in Finder.** Git keeps its record of the worktree until `git worktree prune` clears it, and the branch stays. [Conductor’s changelog](https://www.conductor.build/changelog/0.36.2-model-picker-bug-fixes) asks: “please do not move or delete workspace or repo directories outside Conductor.” Use `git worktree remove`, or the tool’s own archive or delete.
- **Deleting a project’s .git folder to shrink it.** The workaround in the Codex issue labels `rm -rf .git && git init` “Nuclear.” It deletes every commit, branch and stash that exists only on your Mac. `git gc`, above, removes only objects nothing points to.
- **Deleting files inside a package store or cache by hand.** uv’s docs say “it’s never safe to modify the cache directly,” such as by removing a file or folder. Use the tool’s own command, such as `pnpm store prune`, `bun pm cache rm` or `uv cache clean`.
- **Deleting ~/.claude or ~/.codex.** Next to transcripts, they hold your settings and can hold your sign-in. Claude Code’s docs say not to delete ~/.claude.json, ~/.claude/settings.json or ~/.claude/plugins, which “hold your auth, preferences, and installed plugins.” Use `claude purge` or `codex delete` instead.

## How to see yours

![A Sizewise window showing a sample home folder as a map: Movies, Library with Developer and CoreSimulator, Pictures and Downloads, each a rectangle sized by the space it takes, with a selected folder outlined and its size in the status bar.](https://getsizewise.app/images/selection.webp)

1. In Sizewise, choose **File > Scan Folder** and choose your home folder, or scan your whole disk to see these folders next to everything else.
2. Lock a folder with a click to see what deleting it would free. When that’s less than its size, Sizewise shows what keeps the rest, such as copies that share their data.
3. Scan the same folder again next week, and if it grew a lot, a strip over the map names up to three places where the space went.

Sizewise shows where the space is, and you decide what goes. It asks before every move, and moves files only to the Trash, so you can put them back.

## Try it on your Mac

Scanning is free, with no account. A license, $12.99 once, adds Move to Trash. It needs macOS Sequoia or later.

[Get Sizewise](https://getsizewise.app/#download)


---

# Sources

Every claim on the page, mapped to where it was verified. All sources were checked on **2026-10-15**. "Docs" means the tool's own documentation; "source" means the tool's own repository; "issue" means a user report, which the page attributes as such.

## Intro and worktrees

| # | Claim on the page | Source | Checked |
|---|---|---|---|
| 1 | Coding agents often run each task in its own copy (Git worktree) of the project | https://code.claude.com/docs/en/worktrees ; https://learn.chatgpt.com/docs/environments/git-worktrees ; https://www.conductor.build/docs/concepts/git-worktrees ; https://cursor.com/docs/configuration/worktrees | 2026-10-15 |
| 2 | Worktrees share the repository's history; each has its own files | https://git-scm.com/docs/git-worktree ("sharing everything except per-worktree files such as HEAD, index, etc.") ; https://code.claude.com/docs/en/worktrees | 2026-10-15 |
| 3 | A new worktree gets only tracked files; ignored folders (node_modules, build output) appear when you install/build in it | https://www.conductor.build/docs/concepts/git-worktrees ("A new worktree starts from tracked files. Git does not automatically bring along untracked or gitignored local files") ; https://code.claude.com/docs/en/worktrees ("checks out only tracked files"; "A worktree is a fresh checkout, so initialize your development environment there") | 2026-10-15 |
| 4 | Quote: "Worktrees can take up a lot of disk space. Each one has its own set of repository files, dependencies, build caches, etc." | https://learn.chatgpt.com/docs/environments/git-worktrees (Worktree cleanup) | 2026-10-15 |
| 5 | `git worktree list` lists worktrees and the branch each has checked out | https://git-scm.com/docs/git-worktree (`list`) | 2026-10-15 |
| 6 | `git worktree remove` removes only clean worktrees (no changed or untracked files) unless `--force` | https://git-scm.com/docs/git-worktree (`remove`) | 2026-10-15 |
| 7 | `git worktree remove` deletes the folder including ignored folders such as node_modules, and leaves the branch | Local test, git 2.43.0: worktree with an ignored 1 MB node_modules file; `git worktree remove` succeeded, folder gone, branch `wt1` still listed by `git branch` | 2026-10-15 |
| 8 | `git branch -d` deletes a branch (only if fully merged) | https://git-scm.com/docs/git-branch (`-d`, `--delete`) | 2026-10-15 |
| 9 | `git worktree prune` clears records of worktrees whose folders are missing | https://git-scm.com/docs/git-worktree (`prune`) | 2026-10-15 |

## Claude Code

| # | Claim | Source | Checked |
|---|---|---|---|
| 10 | `claude --worktree <name>` creates `.claude/worktrees/<name>/` at the repo root, on a new branch `worktree-<name>` | https://code.claude.com/docs/en/worktrees ("Start Claude in a worktree") | 2026-10-15 |
| 11 | The desktop app uses `<project-root>/.claude/worktrees/` by default; changeable in Settings > Claude Code > Worktree location | https://code.claude.com/docs/en/desktop ("Work in parallel with sessions") | 2026-10-15 |
| 12 | On exit: clean worktree removed with its branch (named session prompts first); worktree with work prompts to keep or remove | https://code.claude.com/docs/en/worktrees ("Clean up worktrees") | 2026-10-15 |
| 13 | `-p` runs don't clean up their worktrees | https://code.claude.com/docs/en/worktrees ("Non-interactive runs with -p have no exit prompt, so Claude doesn't clean up their worktrees") | 2026-10-15 |
| 14 | Subagent and background-session worktrees removed by a periodic sweep once older than cleanupPeriodDays, unless they still hold work | https://code.claude.com/docs/en/worktrees ("Clean up subagent and background-session worktrees") | 2026-10-15 |
| 15 | Desktop: archiving a session removes its worktree | https://code.claude.com/docs/en/desktop ("To remove a worktree when you're done, hover over the session in the sidebar and click the archive icon") | 2026-10-15 |
| 16 | Transcripts in `~/.claude/projects/<project>/<session>.jsonl`, with every message, tool call and tool result; tool output includes file contents | https://code.claude.com/docs/en/claude-directory ("Application data", "Cleaned up automatically") | 2026-10-15 |
| 17 | Deleted once older than cleanupPeriodDays, default 30 days | https://code.claude.com/docs/en/claude-directory ; https://code.claude.com/docs/en/settings-reference (`cleanupPeriodDays`) | 2026-10-15 |
| 18 | Claude Desktop and Cowork transcripts kept at any age unless `desktopSessionCleanupPeriodDays` is set | https://code.claude.com/docs/en/claude-directory ; https://code.claude.com/docs/en/settings-reference (`desktopSessionCleanupPeriodDays`) | 2026-10-15 |
| 19 | `~/.claude/file-history/<session>/` holds pre-edit snapshots used by checkpoint restore (`/rewind`); kept for the 100 most recent checkpoints; deleted by the sweep about 30 days after the session last saved one | https://code.claude.com/docs/en/claude-directory ; https://code.claude.com/docs/en/checkpointing ("How checkpoints work") | 2026-10-15 |
| 20 | `claude purge <path>` deletes transcripts, auto memory, file-history and the project's `~/.claude.json` entry (trust, history, MCP servers); prints the plan and asks; lose resume/rewind; was `claude project purge` before v2.1.288 | https://code.claude.com/docs/en/claude-directory ("Clear local data") | 2026-10-15 |

## Codex

| # | Claim | Source | Checked |
|---|---|---|---|
| 21 | Codex creates worktrees in `$CODEX_HOME/worktrees`; `CODEX_HOME` defaults to `~/.codex` | https://learn.chatgpt.com/docs/environments/git-worktrees ; https://learn.chatgpt.com/docs/config-file/config-advanced ("Config and state locations") | 2026-10-15 |
| 22 | Change location in Settings > Worktrees > Worktree root | https://learn.chatgpt.com/docs/environments/git-worktrees (FAQ) | 2026-10-15 |
| 23 | Keeps the 15 most recent Codex-managed worktrees by default; deletes on chat archive or over the limit; never for pinned chats, running chats, permanent worktrees; saves a snapshot before deleting and offers restore | https://learn.chatgpt.com/docs/environments/git-worktrees ("Worktree cleanup") | 2026-10-15 |
| 24 | Codex CLI `--worktree` creates a managed worktree in the same root, with automatic cleanup off | https://learn.chatgpt.com/docs/developer-commands?surface=cli (`--worktree`) ; source https://github.com/openai/codex/blob/e89b7c442c0433ad5167e72a5a25bb6d0712766a/codex-rs/worktree/src/settings.rs ("CLI allocation uses the same root without enabling automatic cleanup"; `for_cli` sets `auto_cleanup_enabled: false`; `DEFAULT_WORKTREE_KEEP_COUNT = 15`) | 2026-10-15 |
| 25 | Session transcripts in `~/.codex/sessions`, archived in `~/.codex/archived_sessions` | https://learn.chatgpt.com/docs/reference/troubleshooting ("Feedback and logs") ; source constants `SESSIONS_SUBDIR`/`ARCHIVED_SESSIONS_SUBDIR` in codex-rs/rollout/src/lib.rs at e89b7c4 ; app-server docs in https://learn.chatgpt.com/docs/llms-full.txt (`thread/archive` moves the log file into the archived directory) | 2026-10-15 |
| 26 | Codex docs don't describe automatic deletion of session transcripts | Searched https://learn.chatgpt.com/docs/llms-full.txt (only `history.max_bytes` caps `history.jsonl`; no session retention) | 2026-10-15 |
| 27 | `codex delete <SESSION>` permanently deletes; `codex archive` hides from the picker without deleting the transcript | https://learn.chatgpt.com/docs/developer-commands?surface=cli (`codex delete`, `codex archive`) | 2026-10-15 |
| 28 | Codex docs don't mention turn-diff checkpoints | Searched https://learn.chatgpt.com/docs/llms-full.txt for "checkpoint" and "turn-diff" (no matches about local storage) | 2026-10-15 |
| 29 | Issue #29388: open; opened June 22, 2026; title "Codex turn-diff checkpoint blobs silently consume 100+ GB disk space"; objects written into the project's `.git` (refs under `refs/codex/turn-diffs/checkpoints/`); "No garbage collection or pruning is performed after checkpoints are superseded"; `git count-objects -vH` showed `count: 8476`, `size: 101.86 GiB` | https://github.com/openai/codex/issues/29388 (read with WebFetch; direct GitHub access is blocked from this machine) | 2026-10-15 |
| 30 | Sep 30, 2026 comment: "still happens in `codex-cli 0.159.2`" | https://github.com/openai/codex/issues/29388 | 2026-10-15 |
| 31 | Aug 2, 2026 comment: cleanup "won't stop Codex from re-creating snapshots" | https://github.com/openai/codex/issues/29388 | 2026-10-15 |
| 32 | `git count-objects -vH`: `size` is disk space consumed by loose objects; `-H` human-readable | https://git-scm.com/docs/git-count-objects | 2026-10-15 |
| 33 | `git gc` keeps objects referenced by branches, tags, the index, reflogs and anything in `refs/*`; by default prunes loose objects older than 2 weeks | https://git-scm.com/docs/git-gc (`--prune=<date>`, `gc.pruneExpire`, NOTES) | 2026-10-15 |
| 34 | Quote: `--prune=now` "increases the risk of corruption if another process is writing to the repository concurrently" | https://git-scm.com/docs/git-gc (`--prune=<date>`) | 2026-10-15 |
| 35 | Dropped stashes stay recoverable while unreachable objects remain | https://git-scm.com/docs/git-stash ("Recovering stash entries that were cleared/dropped erroneously") | 2026-10-15 |

## Conductor and Cursor

| # | Claim | Source | Checked |
|---|---|---|---|
| 36 | Conductor gives each workspace its own Git worktree, usually under `~/conductor/workspaces/<repo name>/<workspace name>` | https://www.conductor.build/docs/concepts/git-worktrees | 2026-10-15 |
| 37 | Older workspaces can be in a `.conductor` folder under the repository root | https://www.conductor.build/docs/troubleshooting/issues ("Old nested .conductor workspaces") | 2026-10-15 |
| 38 | Archive finished workspaces; restore from the History pane | https://www.conductor.build/docs/concepts/workflow ; https://www.conductor.build/docs/troubleshooting/issues ("Restore an archived workspace") | 2026-10-15 |
| 39 | Cursor creates worktrees under `~/.cursor/worktrees/<reponame>/<name>`, alongside editor worktrees | https://cursor.com/docs/cli/using ("CLI worktrees") | 2026-10-15 |
| 40 | Cursor 3.5+: cleanup keeps newest worktrees up to a machine-wide cap, default 25, all workspaces counted; `cursor.worktreeMaxCount`; worktrees "created by /worktree skills or git worktree add" are eligible for deletion; `/delete-worktree` in the IDE | https://cursor.com/docs/configuration/worktrees ("Worktrees cleanup", "Worktree Skills in IDE") | 2026-10-15 |

## node_modules and virtual environments

| # | Claim | Source | Checked |
|---|---|---|---|
| 41 | Quote: "When using npm, if you have 100 projects using a dependency, you will have 100 copies of that dependency saved on disk." | https://pnpm.io/motivation (pnpm's statement about npm) | 2026-10-15 |
| 42 | pnpm store default on macOS: `~/Library/pnpm/store` (unless `PNPM_HOME`/`XDG_DATA_HOME` set); `pnpm store path` prints the active store | https://pnpm.io/settings/store#storedir ; https://pnpm.io/cli/store (`path`) | 2026-10-15 |
| 43 | pnpm `packageImportMethod: auto` on macOS: clone, then hardlink, then copy | https://pnpm.io/settings/node-modules#packageimportmethod ("What auto tries first" table); cross-checked with Context7 `/pnpm/pnpm.io`, including the pnpm 12 blog post ("macOS keeps clone-first because APFS clonefile is fast") | 2026-10-15 |
| 44 | `pnpm store prune` removes packages not used by any project; quote "is not harmful and has no side effects on your projects"; re-downloads if needed | https://pnpm.io/cli/store (`prune`) | 2026-10-15 |
| 45 | Bun global cache `~/.bun/install/cache` (or `BUN_INSTALL_CACHE_DIR`); `bun pm cache` prints the path | https://bun.com/docs/pm/global-cache ; https://bun.com/docs/pm/cli/pm | 2026-10-15 |
| 46 | Bun install backend default on macOS is `clonefile` (hardlink on Linux and Windows) | https://bun.com/docs/pm/global-cache ("Installation strategies") ; https://bun.com/docs/pm/cli/install ("Platform-specific backends"); cross-checked with Context7 `/oven-sh/bun` | 2026-10-15 |
| 47 | `bun pm cache rm` clears the whole cache; `bun pm cache prune` removes packages older than 30 days, age = time since download on macOS, even ones still used; re-downloaded when needed | https://bun.com/docs/pm/cli/pm | 2026-10-15 |
| 48 | uv cache: `$XDG_CACHE_HOME/uv` or `$HOME/.cache/uv` on Unix (macOS); `uv cache dir` prints it | https://docs.astral.sh/uv/concepts/cache/ ("Cache directory") ; https://docs.astral.sh/uv/reference/storage/ | 2026-10-15 |
| 49 | uv `link-mode` default: `clone` on macOS and Linux | https://docs.astral.sh/uv/reference/settings/#link-mode | 2026-10-15 |
| 50 | `uv cache prune` removes unused entries, "is safe to run periodically"; `uv cache clean` removes all | https://docs.astral.sh/uv/concepts/cache/ ("Clearing the cache") | 2026-10-15 |
| 51 | Quote: a clone "occupies no additional space on disk"; both files share unmodified blocks | https://developer.apple.com/documentation/foundation/about-apple-file-system ("Clones Reduce the Cost of Copying") | 2026-10-15 |
| 52 | Hard links point to the same data; quote "that 1MB is the same space on the disk addressed from two different locations" | https://pnpm.io/faq | 2026-10-15 |
| 53 | Deleting a cloned or hard-linked node_modules frees only the unshared part; the rest is freed when nothing else uses it | Follows from rows 43, 46, 49, 51, 52; Bun's docs say the same for hard links ("A file that a node_modules tree hardlinks stays on disk until that tree is removed too", https://bun.com/docs/pm/cli/pm); uv offers a `cache-physical-space` preview because cleanup estimates otherwise miss "hardlinks and copy-on-write clones" (https://docs.astral.sh/uv/concepts/cache/) | 2026-10-15 |

## Rust

| # | Claim | Source | Checked |
|---|---|---|---|
| 54 | Cargo builds into `target` at the workspace root by default | https://doc.rust-lang.org/cargo/reference/build-cache.html | 2026-10-15 |
| 55 | Automatic cleanup covers only the global cache in Cargo home; build artifacts are not tracked | https://doc.rust-lang.org/cargo/reference/config.html#cache ("Support for tracking build artifacts is not yet implemented") | 2026-10-15 |
| 56 | `cargo clean` with no options deletes the entire target directory; `--dry-run` summarizes what would be deleted | https://doc.rust-lang.org/cargo/commands/cargo-clean.html | 2026-10-15 |
| 57 | `~/.cargo/registry/cache` holds `.crate` gzip archives; `registry/src` holds unpacked sources | https://doc.rust-lang.org/cargo/guide/cargo-home.html | 2026-10-15 |
| 58 | Cargo deletes network-downloaded files unused for 3 months and locally generated ones unused for 1 month, during build commands, not when offline | https://doc.rust-lang.org/cargo/reference/config.html#cache | 2026-10-15 |

## Browsers and models

| # | Claim | Source | Checked |
|---|---|---|---|
| 59 | Playwright browsers in `~/Library/Caches/ms-playwright` on macOS; "a few hundred megabytes of disk space" | https://playwright.dev/docs/browsers#managing-browser-binaries | 2026-10-15 |
| 60 | Stale browser versions deleted when no client needs them | https://playwright.dev/docs/browsers ("Stale browser removal") | 2026-10-15 |
| 61 | `npx playwright uninstall` (current installation), `--all` (every installation); `npx playwright install` downloads | https://playwright.dev/docs/browsers#uninstall-browsers | 2026-10-15 |
| 62 | Hugging Face cache default `~/.cache/huggingface/hub`; `HF_HOME`, `HF_HUB_CACHE` | https://huggingface.co/docs/huggingface_hub/guides/manage-cache ; https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables | 2026-10-15 |
| 63 | `hf cache ls`, `hf cache rm <repo id>` (example `model/bert-base-cased`), `hf cache prune` (unreferenced revisions, `.incomplete` downloads), `--dry-run` | https://huggingface.co/docs/huggingface_hub/guides/manage-cache ("Clean your cache") | 2026-10-15 |
| 64 | huggingface_hub 1.0 removed `huggingface-cli`; older docs used `huggingface-cli delete-cache` | https://huggingface.co/docs/huggingface_hub/concepts/migration ; https://huggingface.co/docs/huggingface_hub/v0.30.0/en/guides/manage-cache | 2026-10-15 |
| 65 | Ollama models in `~/.ollama/models` on macOS; `OLLAMA_MODELS` changes it | https://docs.ollama.com/faq ("Where are models stored?") | 2026-10-15 |
| 66 | `ollama ls`, `ollama rm <model>`, `ollama pull <model>` | https://docs.ollama.com/cli | 2026-10-15 |
| 67 | LM Studio expected structure `~/.lmstudio/models/<publisher>/<model>/` | https://lmstudio.ai/docs/app/advanced/import-model | 2026-10-15 |
| 68 | Models directory can be changed in My Models | https://lmstudio.ai/docs/app/basics/download-model ("Changing the models directory") | 2026-10-15 |
| 69 | `lms ls` lists downloaded models with size, and a total ("You have 47 models, taking up 160.78 GB of disk space.") | https://lmstudio.ai/docs/cli/local-models/ls | 2026-10-15 |
| 70 | LM Studio docs describe no command to delete a model | Searched https://lmstudio.ai/llms-full.txt (only `lms unload`, which frees memory) | 2026-10-15 |

## Other guides, advice to skip, Sizewise

| # | Claim | Source | Checked |
|---|---|---|---|
| 71 | Linked Sizewise guides exist: /xcode-storage, /docker-disk, /developer-caches, /android-storage | https://getsizewise.app/sitemap.xml (all return 200) | 2026-10-15 |
| 72 | Quote: "please do not move or delete workspace or repo directories outside Conductor" | https://www.conductor.build/changelog/0.36.2-model-picker-bug-fixes (Feb 18, 2026) | 2026-10-15 |
| 73 | The issue's Workaround section labels `rm -rf .git && git init` "# Nuclear: delete .git and reinitialize" | https://github.com/openai/codex/issues/29388 | 2026-10-15 |
| 74 | Quote: "it's never safe to modify the cache directly (e.g., by removing a file or directory)" | https://docs.astral.sh/uv/concepts/cache/ | 2026-10-15 |
| 75 | Quote: `~/.claude.json`, `~/.claude/settings.json`, `~/.claude/plugins/` "hold your auth, preferences, and installed plugins" | https://code.claude.com/docs/en/claude-directory ("Clear local data") | 2026-10-15 |
| 76 | `~/.codex` holds `config.toml` and, with file-based credential storage, `auth.json` | https://learn.chatgpt.com/docs/config-file/config-advanced ("Config and state locations") | 2026-10-15 |
| 77 | Sizewise text (lock a folder, what keeps the rest, the change strip, Trash-only moves, price line) is reused verbatim or near-verbatim from existing pages | https://getsizewise.app/developer-caches ; https://getsizewise.app/xcode-storage ; https://getsizewise.app/compare ; https://getsizewise.app/release-notes.html | 2026-10-15 |

## Verification notes

- Primary sources were fetched directly (curl) and read in full where possible; Claude Code, Codex (learn.chatgpt.com), Bun and Cursor publish Markdown twins of their pages, which were used.
- GitHub pages are blocked for curl and the GitHub API from this machine, so issue #29388 was read with WebFetch (three passes for exact quotes). The Codex source was read from a shallow clone at commit `e89b7c442c0433ad5167e72a5a25bb6d0712766a` (2026-10-15).
- pnpm and Bun claims were cross-checked with Context7 (`/pnpm/pnpm.io`, `/oven-sh/bun`); both matched the live sites.
- `git worktree remove` behaviour with ignored folders was tested locally with git 2.43.0.

## Left out, and why

- **Codex "ghost snapshots" (the old `/undo` feature):** the current source treats them as legacy and strips them from rollouts, so they no longer apply.
- **Where Codex stores the snapshot it saves before deleting a worktree:** not documented.
- **Codex rollout compression (`.zst`):** present in source, not documented for users.
- **Whether archiving a Conductor workspace deletes its folder:** the docs don't say. Changelog lines hint at "archive cleanup", but that is not explicit enough to state.
- **Cursor checkpoints and chat storage:** no page in Cursor's docs index covers where they live.
- **How to delete a model in LM Studio:** no documented command or steps; the page says so instead of guessing.
- **Ollama models sharing layers (so `ollama rm` can free less than the listed size):** not documented.
- **npm's own statement that each project gets a full copy:** npm's docs don't say it directly, so the page quotes pnpm's docs and attributes it.
- **Hugging Face shared blobs across repos ("Per-repo sizes stay logical"):** documented and on-theme, but left out for length.
- **pnpm's per-disk store on external drives and global virtual store, Bun's global store, Cargo `build-dir`:** off by default or edge cases; left out for length.
- **Sizewise's 17.5-million-item scan claim:** allowed but not used, to match the other guides' "How to see yours" sections.

## Publishing notes

- Slug assumed: `/agent-disk` (canonical and og:url set to https://getsizewise.app/agent-disk). Add it to sitemap.xml, and consider a footer or in-page link from /developer-caches.
- Head, header, footer, classes and the inline speculation-rules script are copied byte-for-byte from the live guides. The trailing `window.__CF$cv$params` script was left out on purpose: it differs on every request (ray ID and timestamp), so Cloudflare injects it at the edge and it is not part of the page source.
