# Unbuilt demand in AI coding-agent tools: issue-tracker research

**Checked:** 2026-10-15. All reaction counts are 👍 (`+1`) as returned by GitHub's issue search on that date unless marked otherwise ("votes" = Cursor forum topic votes; "upvotes" = GitHub Discussions upvotes).
**Question:** Which features are most requested in developer tools used by solo developers who build with coding agents (and by pro Mac-tool buyers), which of them the maintainers declined or left alone for months, and which could be delivered by a separate paid product (hooks, MCP, OS features, a menu bar app, a local proxy, a wrapper)?

---

## 0. Method, sources, caveats

**How the data was collected**
- **GitHub issues:** the GitHub MCP `search_issues` tool (GitHub search API), sorted `reactions-+1` descending, with queries `is:issue is:open` and `is:issue is:closed reason:not-planned` per repo. Direct `curl`/`gh api` to github.com was blocked from this machine (403).
- **Check on ordering:** the MCP order for `anthropics/claude-code` open issues was compared against the GitHub web UI page sorted by 👍 ([link](https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc)). The top 25 were identical.
- **Cursor:** the GitHub issues for `cursor/cursor` (formerly `getcursor/cursor`) are hidden: search reports 3,729 closed issues and 0 open, but lists none. The README sends feature requests to the forum. Forum data came from Discourse JSON: `https://forum.cursor.com/c/ideas/feature-requests/5/l/latest.json?order=votes`. The category has 6,767 topics with topic voting enabled. 240 topics were saved to `research/cursor_forum/cursor_fr_by_votes.tsv`.
- **Discussions (Ghostty, Cline, Zed):** WebFetch of the "Top" sort pages. Upvote counts are as rendered on those pages.
- **Thread deep-dives:** WebFetch summaries of issue pages, which come from a small model reading the page. Treat paraphrased quotes and commenter claims as leads, and re-read the thread before quoting it publicly. Commenter claims are marked as such below.
- **Third-party traction:** GitHub repository search (stars as of 2026-10-15). Prices come from vendor pages where fetched; otherwise the source is named.

**Caveats that change how "closed as not planned" should be read**
1. **claude-code:** most "not planned" closures come from a stale bot. It closes issues after 60 days without activity and then locks them. Examples: ACP [#6686](https://github.com/anthropics/claude-code/issues/6686) and context-% [#516](https://github.com/anthropics/claude-code/issues/516) were both bot-closed despite recent human "+1" comments. These closures are evidence of neglect, not of a decision.
2. **opencode:** on 2026-10-11 to 2026-10-13 the maintainer bulk-closed v1-era issues as "not planned" when v2 shipped ("development is focused on V2"). See [#6231](https://github.com/anomalyco/opencode/issues/6231).
3. **gemini-cli:** only 497 issues are open, against 4,322 closed as not planned. Mass closures in May 2026 (for example on 2026-05-06) suggest housekeeping. Users also ask about "Antigravity CLI" ([#27304](https://github.com/google-gemini/gemini-cli/issues/27304)), which hints at a product shift.
4. **Explicit maintainer declines or deprioritizations are rarer.** Those found: Codex `/undo` ("will need to be redesigned"), Codex LSP (maintainer skeptical), Cursor account switching ("very low priority"), Cursor rate meter ("would also lead to more complaints"), Codex multi-account ("we prioritize by upvotes").
5. **Platform shift on 2026-10-01:** Claude Code "Mods" (function hooks with UI panes, a `$.session.usage()` API, and event hooks) went live per [#91870](https://github.com/anthropics/claude-code/issues/91870), on CLI 2.1.287+ per commenters. Mods make in-agent add-ons easier to build, and they also make it easier for Anthropic or hobbyists to absorb small gaps for free.

---

## 1. Per-repo top issues

### 1.1 anthropics/claude-code ([open by 👍](https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc), [closed not-planned by 👍](https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20is%3Aclosed%20reason%3Anot-planned%20sort%3Areactions-%2B1-desc))
Open issues total: 14,365. Closed as not planned: 47,962.

**Open, top 30 by 👍 (all types)**

| # | 👍 | Created | Underlying need |
|---|---:|---|---|
| [45596](https://github.com/anthropics/claude-code/issues/45596) | 1,191 (2,110 total reactions) | 2026-04-09 | Bring back "Buddy", the ASCII companion removed in v2.1.97 |
| [18435](https://github.com/anthropics/claude-code/issues/18435) | 902 | 2026-01-15 | Multiple accounts / profile switching in Claude Desktop |
| [34229](https://github.com/anthropics/claude-code/issues/34229) | 819 | 2026-03-14 | Phone verification failing (account access; labeled invalid) |
| [36151](https://github.com/anthropics/claude-code/issues/36151) | 755 | 2026-03-19 | Multi-account switching in the mobile app |
| [16157](https://github.com/anthropics/claude-code/issues/16157) | 695 | 2026-01-03 | Max subscribers hit usage limits instantly (bug) |
| [826](https://github.com/anthropics/claude-code/issues/826) | 690 | 2025-04-19 | TUI jumps to top of scrollback while streaming (bug) |
| [17432](https://github.com/anthropics/claude-code/issues/17432) | 500 | 2026-01-11 | INR pricing for India |
| [38335](https://github.com/anthropics/claude-code/issues/38335) | 476 | 2026-03-24 | Max session limits exhausted abnormally fast (bug) |
| [15942](https://github.com/anthropics/claude-code/issues/15942) | 463 | 2026-01-01 | Visual Studio 2026 integration |
| [1455](https://github.com/anthropics/claude-code/issues/1455) | 441 | 2025-05-31 | Respect the XDG base-directory spec |
| [2511](https://github.com/anthropics/claude-code/issues/2511) | 421 | 2025-06-24 | Use claude.ai Projects knowledge inside Claude Code |
| [27302](https://github.com/anthropics/claude-code/issues/27302) | 414 | 2026-02-21 | Multiple accounts per connector (same service, different accounts) |
| [31005](https://github.com/anthropics/claude-code/issues/31005) | 411 | 2026-03-05 | Read AGENTS.md and `.agents/skills/` |
| [1913](https://github.com/anthropics/claude-code/issues/1913) | 321 | 2025-06-10 | Terminal flicker (bug) |
| [769](https://github.com/anthropics/claude-code/issues/769) | 300 | 2025-04-12 | Screen flicker during tool calls (bug) |
| [18170](https://github.com/anthropics/claude-code/issues/18170) | 300 | 2026-01-14 | Copied output carries TUI indentation and trailing spaces |
| [85891](https://github.com/anthropics/claude-code/issues/85891) | 290 | 2026-08-11 | Desktop window always on top on Windows (bug) |
| [24726](https://github.com/anthropics/claude-code/issues/24726) | 268 | 2026-02-10 | VS Code: stop auto-attaching the open file or selection |
| [65961](https://github.com/anthropics/claude-code/issues/65961) | 251 | 2026-06-07 | Model writes verbose comments despite instructions |
| [30154](https://github.com/anthropics/claude-code/issues/30154) | 246 | 2026-03-02 | Multiple windows in Claude Code Desktop |
| [1547](https://github.com/anthropics/claude-code/issues/1547) | 243 | 2025-06-04 | IME input performance and duplicate candidates (bug) |
| [22543](https://github.com/anthropics/claude-code/issues/22543) | 233 | 2026-02-02 | Cowork's 10 GB VM bundle degrades performance (bug) |
| [46917](https://github.com/anthropics/claude-code/issues/46917) | 215 | 2026-04-12 | v2.1.100+ inflates cache_creation by ~20K tokens (cost bug) |
| [13354](https://github.com/anthropics/claude-code/issues/13354) | 209 | 2025-12-08 | Resume automatically when the session limit resets |
| [28240](https://github.com/anthropics/claude-code/issues/28240) | 209 | 2026-02-24 | Permission prompt triggers on `cd` in compound commands (bug) |
| [33932](https://github.com/anthropics/claude-code/issues/33932) | 206 | 2026-03-13 | VS Code: per-hunk diff review UI like Copilot Edits |
| [21151](https://github.com/anthropics/claude-code/issues/21151) | 186 | 2026-01-27 | Show which file the Read tool is reading |
| [32733](https://github.com/anthropics/claude-code/issues/32733) | 178 | 2026-03-10 | Secure secrets injection for Claude Code on the web |
| [16082](https://github.com/anthropics/claude-code/issues/16082) | 176 | 2026-01-02 | Desktop: menu-bar-only mode (hide Dock icon) |
| [47509](https://github.com/anthropics/claude-code/issues/47509) | 176 | 2026-04-13 | Team plan tier equivalent to Max 20x |

**Open, `label:enhancement`, next 35 by 👍** (2,934 open enhancement issues)

| # | 👍 | Created | Underlying need |
|---|---:|---|---|
| [20697](https://github.com/anthropics/claude-code/issues/20697) | 161 | 2026-01-25 | Sync skills between Desktop and CLI |
| [28791](https://github.com/anthropics/claude-code/issues/28791) | 150 | 2026-02-26 | Sync conversation history between CLI and Desktop |
| [16446](https://github.com/anthropics/claude-code/issues/16446) | 150 | 2026-01-06 | LaTeX rendering in VS Code |
| [12925](https://github.com/anthropics/claude-code/issues/12925) | 148 | 2025-12-03 | Linear: assign issues to a Claude Code cloud agent |
| [23134](https://github.com/anthropics/claude-code/issues/23134) | 146 | 2026-02-04 | Option to disable collapsing of pasted text |
| [12346](https://github.com/anthropics/claude-code/issues/12346) | 143 | 2025-11-25 | GitLab integration (repos, MRs, mobile) |
| [25045](https://github.com/anthropics/claude-code/issues/25045) | 132 | 2026-02-11 | Let skills rename sessions |
| [91870](https://github.com/anthropics/claude-code/issues/91870) | 131 | 2026-09-03 | "Mods" extensibility (went live 2026-10-01) |
| [7490](https://github.com/anthropics/claude-code/issues/7490) | 128 | 2025-09-12 | Choose the shell used by the Bash tool |
| [13585](https://github.com/anthropics/claude-code/issues/13585) | 128 | 2025-12-10 | Quota information in the CLI, as JSON |
| [1785](https://github.com/anthropics/claude-code/issues/1785) | 124 | 2025-06-08 | MCP sampling billed to the Max subscription |
| [13843](https://github.com/anthropics/claude-code/issues/13843) | 123 | 2025-12-12 | Bring claude.ai conversation context into Claude Code |
| [16128](https://github.com/anthropics/claude-code/issues/16128) | 122 | 2026-01-03 | Bedrock auth for the Chrome extension |
| [12619](https://github.com/anthropics/claude-code/issues/12619) | 121 | 2025-11-28 | Per-repo plan-file naming |
| [2254](https://github.com/anthropics/claude-code/issues/2254) | 121 | 2025-06-18 | Disable the welcome banner |
| [19649](https://github.com/anthropics/claude-code/issues/19649) | 120 | 2026-01-21 | Model uses `sed`/`grep` instead of built-in tools |
| [34196](https://github.com/anthropics/claude-code/issues/34196) | 116 | 2026-03-13 | Font size setting for the VS Code chat panel |
| [44243](https://github.com/anthropics/claude-code/issues/44243) | 115 | 2026-04-06 | Multiple Slack workspaces in the connector |
| [34235](https://github.com/anthropics/claude-code/issues/34235) | 113 | 2026-03-14 | AGENTS.md as a native context file |
| [14200](https://github.com/anthropics/claude-code/issues/14200) | 112 | 2025-12-16 | Rules support in plugins |
| [84862](https://github.com/anthropics/claude-code/issues/84862) | 109 | 2026-08-07 | Passkey sign-in |
| [37951](https://github.com/anthropics/claude-code/issues/37951) | 107 | 2026-03-23 | Hide inline diffs for Edit/Write output |
| [40043](https://github.com/anthropics/claude-code/issues/40043) | 104 | 2026-03-27 | Remove folders from a Cowork project |
| [35744](https://github.com/anthropics/claude-code/issues/35744) | 103 | 2026-03-18 | Auto-continue after the subscription limit resets |
| [20944](https://github.com/anthropics/claude-code/issues/20944) | 102 | 2026-01-26 | Disable automatic IDE selection context |
| [28795](https://github.com/anthropics/claude-code/issues/28795) | 101 | 2026-02-26 | Bedrock + AWS SSO in `claude remote-control` |
| [28729](https://github.com/anthropics/claude-code/issues/28729) | 99 | 2026-02-25 | Use a git repo as the source of org skills |
| [45132](https://github.com/anthropics/claude-code/issues/45132) | 98 | 2026-04-08 | Scala (Metals) in the native LSP plugin lineup |
| [2350](https://github.com/anthropics/claude-code/issues/2350) | 97 | 2025-06-20 | XDG: move cache and runtime files out of the config dir |
| [38005](https://github.com/anthropics/claude-code/issues/38005) | 96 | 2026-03-23 | Right-to-left text in Desktop and Cowork |
| [15542](https://github.com/anthropics/claude-code/issues/15542) | 96 | 2025-12-27 | Let Claude Code read Claude app chat history |
| [26904](https://github.com/anthropics/claude-code/issues/26904) | 96 | 2026-02-19 | `/delete` to delete the current session |
| [14920](https://github.com/anthropics/claude-code/issues/14920) | 95 | 2025-12-20 | Disable individual plugin skills |
| [44763](https://github.com/anthropics/claude-code/issues/44763) | 94 | 2026-04-07 | Timestamps on conversation messages |

**Closed as "not planned", top by 👍** (28 shown; closures at ~10:xx UTC are the stale bot)

| # | 👍 | Created → closed | Underlying need |
|---|---:|---|---|
| [6686](https://github.com/anthropics/claude-code/issues/6686) | 437 | 2025-08-27 → 2026-02-09 (bot) | Agent Client Protocol (ACP) support |
| [46829](https://github.com/anthropics/claude-code/issues/46829) | 244 | 2026-04-12 → 2026-04-12 | Cache TTL silently regressed from 1h to 5m (cost) |
| [516](https://github.com/anthropics/claude-code/issues/516) | 130 | 2025-03-15 → 2026-01-20 (bot) | Always show remaining context % |
| [2562](https://github.com/anthropics/claude-code/issues/2562) | 129 | 2025-06-25 → 2026-02-22 | Title is "m" (content not reviewed) |
| [21371](https://github.com/anthropics/claude-code/issues/21371) | 79 | 2026-01-28 → 2026-05-05 | Chrome extension won't connect (bug) |
| [1731](https://github.com/anthropics/claude-code/issues/1731) | 76 | 2025-06-06 → 2026-01-09 | Recognize the Positron IDE |
| [1454](https://github.com/anthropics/claude-code/issues/1454) | 73 | 2025-05-31 → 2026-01-16 | Machine-to-machine auth for Max subscriptions |
| [17067](https://github.com/anthropics/claude-code/issues/17067) | 73 | 2026-01-09 → 2026-03-16 | Allow Max subscription use in OpenCode |
| [8371](https://github.com/anthropics/claude-code/issues/8371) | 69 | 2025-09-29 → 2026-01-15 | Restore the pre-2.0 thinking display |
| [1315](https://github.com/anthropics/claude-code/issues/1315) | 67 | 2025-05-26 → 2026-01-14 | Semantic, IDE-style refactoring (LSP) |
| [29368](https://github.com/anthropics/claude-code/issues/29368) | 66 | 2026-02-27 → 2026-06-09 | Hide unused cloud connectors |
| [5515](https://github.com/anthropics/claude-code/issues/5515) | 62 | 2025-08-10 → 2026-01-09 | Missing API key over SSH to a Mac (Keychain) |
| [2407](https://github.com/anthropics/claude-code/issues/2407) | 59 | 2025-06-21 → 2026-01-10 | Inherit shell functions (zoxide) in the Bash tool |
| [729](https://github.com/anthropics/claude-code/issues/729) | 52 | 2025-04-07 → 2025-04-07 | Don't submit on Enter (multi-line prompts) |
| [2571](https://github.com/anthropics/claude-code/issues/2571) | 51 | 2025-06-25 → 2026-02-11 | Load CLAUDE.md files in subdirectories |
| [6759](https://github.com/anthropics/claude-code/issues/6759) | 50 | 2025-08-28 → 2026-01-08 | Disable individual MCP tools to save context |
| [2527](https://github.com/anthropics/claude-code/issues/2527) | 49 | 2025-06-24 → 2026-01-30 | OAuth dynamic client registration blocks Entra ID |
| [5621](https://github.com/anthropics/claude-code/issues/5621) | 47 | 2025-08-12 → 2026-02-05 | Expose quota in the statusline JSON (later shipped as `rate_limits`, per [#13585](https://github.com/anthropics/claude-code/issues/13585) commenters) |
| [2707](https://github.com/anthropics/claude-code/issues/2707) | 44 | 2025-06-28 → 2026-01-26 | Trailing whitespace and missing EOF newline |
| [45517](https://github.com/anthropics/claude-code/issues/45517) | 44 | 2026-04-09 → 2026-04-09 | `/buddy` missing in v2.1.97 |
| [87](https://github.com/anthropics/claude-code/issues/87) | 42 | 2025-02-25 → 2026-02-01 | Advanced memory tool |
| [9127](https://github.com/anthropics/claude-code/issues/9127) | 39 | 2025-10-08 → 2026-01-12 | Jira authentication fails |
| [2794](https://github.com/anthropics/claude-code/issues/2794) | 38 | 2025-07-01 → 2026-01-12 | Scheduled actions |
| [4580](https://github.com/anthropics/claude-code/issues/4580) | 38 | 2025-07-28 → 2026-01-18 | 100% CPU freeze with multiple agents (bug) |
| [418](https://github.com/anthropics/claude-code/issues/418) | 37 | 2025-03-10 → 2025-12-10 | Aider-style `--watch-files` |
| [2335](https://github.com/anthropics/claude-code/issues/2335) | 37 | 2025-06-19 → 2025-08-22 | Option for Enter to insert a newline |
| [6638](https://github.com/anthropics/claude-code/issues/6638) | 35 | 2025-08-27 → 2026-02-14 | Load and unload MCP servers mid-session |
| [1931](https://github.com/anthropics/claude-code/issues/1931) | 34 | 2025-06-11 → 2026-01-11 | Better, fuzzy file search |

### 1.2 openai/codex ([open](https://github.com/openai/codex/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc), [closed not-planned](https://github.com/openai/codex/issues?q=is%3Aissue%20is%3Aclosed%20reason%3Anot-planned%20sort%3Areactions-%2B1-desc))
Open: 22,485. Closed as not planned: 2,044.

| # | 👍 | Created | Underlying need |
|---|---:|---|---|
| [8745](https://github.com/openai/codex/issues/8745) | 503 | 2026-01-05 | LSP integration: diagnostics and symbol navigation for the agent |
| [9203](https://github.com/openai/codex/issues/9203) | 482 | 2026-01-14 | Bring back `/undo` (removed; maintainer: "will need to be redesigned") |
| [25719](https://github.com/openai/codex/issues/25719) | 399 | 2026-06-01 | macOS Desktop triggers syspolicyd/trustd CPU runaway (bug) |
| [3000](https://github.com/openai/codex/issues/3000) | 241 | 2025-08-31 | Voice dictation in the IDE extension |
| [2998](https://github.com/openai/codex/issues/2998) | 236 | 2025-08-31 | Approve or reject diffs inside the IDE |
| [11626](https://github.com/openai/codex/issues/11626) | 228 | 2026-02-12 | `/rewind` that restores both chat and file edits |
| [28969](https://github.com/openai/codex/issues/28969) | 215 | 2026-06-18 | Disable the 60-second auto-resolve of questions |
| [13993](https://github.com/openai/codex/issues/13993) | 204 | 2026-03-08 | Standalone Windows installer |
| [17827](https://github.com/openai/codex/issues/17827) | 203 | 2026-04-14 | Customizable status line |
| [3962](https://github.com/openai/codex/issues/3962) | 201 | 2025-09-20 | Sound or notification when a task finishes |
| [1797](https://github.com/openai/codex/issues/1797) | 194 | 2025-08-02 | PDF input |
| [48195](https://github.com/openai/codex/issues/48195) | 179 | 2026-09-25 | Make the self-updating background daemon opt-in |
| [19464](https://github.com/openai/codex/issues/19464) | 168 | 2026-04-24 | 1M-token context for GPT-5.5 |
| [34035](https://github.com/openai/codex/issues/34035) | 166 | 2026-07-18 | Make the removal of the 5-hour limit permanent |
| [2952](https://github.com/openai/codex/issues/2952) | 147 | 2025-08-30 | `@` search inside gitignored directories |
| [28058](https://github.com/openai/codex/issues/28058) | 136 | 2026-06-13 | Readable audit trail for multi-agent messages |
| [1980](https://github.com/openai/codex/issues/1980) | 134 | 2025-08-08 | XDG base directories on Linux |
| [4432](https://github.com/openai/codex/issues/4432) | 130 | 2025-09-29 | Multi-account auth profiles (`--auth-profile`) |
| [4106](https://github.com/openai/codex/issues/4106) | 123 | 2025-09-23 | Control over auto-compaction |
| [12115](https://github.com/openai/codex/issues/12115) | 121 | 2026-02-18 | Load nested AGENTS.md files dynamically |
| [20500](https://github.com/openai/codex/issues/20500) | 116 | 2026-04-30 | Multiple named accounts per connector |
| [25319](https://github.com/openai/codex/issues/25319) | 109 | 2026-05-30 | Scope VS Code chats to the current workspace |
| [48237](https://github.com/openai/codex/issues/48237) | 105 | 2026-09-25 | 401 Unauthorized (bug) |
| [21653](https://github.com/openai/codex/issues/21653) | 102 | 2026-05-08 | Multi-line status line |
| [4323](https://github.com/openai/codex/issues/4323) | 97 | 2025-09-26 | Changelog for the IDE extension |
| [4242](https://github.com/openai/codex/issues/4242) | 93 | 2025-09-25 | Honor proxy environment variables |
| [25144](https://github.com/openai/codex/issues/25144) | 88 | 2026-05-29 | Stop converting long pastes into .txt attachments |
| [10665](https://github.com/openai/codex/issues/10665) | 88 | 2026-02-04 | Azure DevOps (Azure Repos) integration |
| [29451](https://github.com/openai/codex/issues/29451) | 87 | 2026-06-22 | Show image artifacts inline in the TUI |
| [14601](https://github.com/openai/codex/issues/14601) | 86 | 2026-03-13 | Keep project trust levels out of `config.toml` |
| [5547](https://github.com/openai/codex/issues/5547) | 85 | 2025-10-23 | Configurable `/review` |
| [44561](https://github.com/openai/codex/issues/44561) | 85 | 2026-09-10 | Turn off the "whimsy" effect by default |
| [34349](https://github.com/openai/codex/issues/34349) | 84 | 2026-07-20 | Disable Pets entirely |
| [10599](https://github.com/openai/codex/issues/10599) | 76 | 2026-02-04 | Configure the worktree location |
| [21073](https://github.com/openai/codex/issues/21073) | 76 | 2026-05-04 | Auto-resume the CLI session when the usage limit resets |
| [2948](https://github.com/openai/codex/issues/2948) | 75 | 2025-08-30 | Edit past messages |

**Closed as "not planned", top by 👍** (low counts overall)
[2901](https://github.com/openai/codex/issues/2901) VS Code `mcp.json` integration (68) · [2129](https://github.com/openai/codex/issues/2129) native SSE MCP transport (65) · [4734](https://github.com/openai/codex/issues/4734) project-level custom prompts (48) · [11898](https://github.com/openai/codex/issues/11898) inline ghost-text completions (48) · [48122](https://github.com/openai/codex/issues/48122) Cmd+C copy broken on Mac (47) · [13942](https://github.com/openai/codex/issues/13942) start in Plan mode (39) · [15679](https://github.com/openai/codex/issues/15679) `/loop` recurring prompt (38) · [12939](https://github.com/openai/codex/issues/12939) accidental prompts via Tab (35) · [8361](https://github.com/openai/codex/issues/8361) log in with a Copilot subscription (29) · [48125](https://github.com/openai/codex/issues/48125) cannot copy text (27) · [10486](https://github.com/openai/codex/issues/10486) export plan to Markdown (23) · [47996](https://github.com/openai/codex/issues/47996) Cmd+C no longer copies in iTerm2 (21) · [4825](https://github.com/openai/codex/issues/4825) share chats across PCs (19).

### 1.3 google-gemini/gemini-cli ([open](https://github.com/google-gemini/gemini-cli/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc), [closed not-planned](https://github.com/google-gemini/gemini-cli/issues?q=is%3Aissue%20is%3Aclosed%20reason%3Anot-planned%20sort%3Areactions-%2B1-desc))
Only 497 issues are open, so the open list is thin. The top open items are [19532](https://github.com/google-gemini/gemini-cli/issues/19532) "Add gemini-3.1-pro-preview" (110), [28625](https://github.com/google-gemini/gemini-cli/issues/28625) enterprise users missing the latest models (58), [3132](https://github.com/google-gemini/gemini-cli/issues/3132) agents epic (50), [1982](https://github.com/google-gemini/gemini-cli/issues/1982) audio input (15), [13852](https://github.com/google-gemini/gemini-cli/issues/13852) GEMINI.md ignored (16), [3375](https://github.com/google-gemini/gemini-cli/issues/3375) tool-call timeout setting (9), and [15542](https://github.com/google-gemini/gemini-cli/issues/15542) fine-grained permissions (3).

**Closed as "not planned" (4,322 total)**

| # | 👍 | Created → closed | Underlying need |
|---|---:|---|---|
| [22141](https://github.com/google-gemini/gemini-cli/issues/22141) | 164 | 2026-03-12 → 2026-08-11 | Agent loop stuck for an hour or more on small edits (bug) |
| [1825](https://github.com/google-gemini/gemini-cli/issues/1825) | 101 | 2025-06-26 → 2026-05-06 | Respect XDG |
| [24517](https://github.com/google-gemini/gemini-cli/issues/24517) | 65 | 2026-04-02 → 2026-05-04 | 403 for Google One AI Premium subscribers |
| [2208](https://github.com/google-gemini/gemini-cli/issues/2208) | 58 | 2025-06-27 → 2026-04-09 | Disable automatic Pro-to-Flash fallback |
| [1698](https://github.com/google-gemini/gemini-cli/issues/1698) | 55 | 2025-06-26 → 2026-07-24 | Honor VISUAL/EDITOR for the external editor |
| [1679](https://github.com/google-gemini/gemini-cli/issues/1679) | 54 | 2025-06-26 → 2026-05-14 | Custom API endpoint and auth header |
| [19430](https://github.com/google-gemini/gemini-cli/issues/19430) | 44 | 2026-02-18 → 2026-10-03 | Parallel agent teams |
| [5874](https://github.com/google-gemini/gemini-cli/issues/5874) | 42 | 2025-08-09 → 2026-05-06 | Neovim integration |
| [4556](https://github.com/google-gemini/gemini-cli/issues/4556) | 39 | 2025-07-20 → 2026-09-25 | Less sycophancy |
| [5938](https://github.com/google-gemini/gemini-cli/issues/5938) | 37 | 2025-08-10 → 2026-10-04 | Local/offline models (Ollama, LM Studio) |
| [2065](https://github.com/google-gemini/gemini-cli/issues/2065) | 35 | 2025-06-27 → 2026-05-06 | Codebase indexing |
| [27304](https://github.com/google-gemini/gemini-cli/issues/27304) | 35 | 2026-05-20 → 2026-08-04 | "Antigravity CLI: is it open source?" |
| [4168](https://github.com/google-gemini/gemini-cli/issues/4168) | 34 | 2025-07-14 → 2026-05-15 | Autonomous background agents |
| [22559](https://github.com/google-gemini/gemini-cli/issues/22559) | 27 | 2026-03-15 → 2026-04-21 | Remote control |
| [2094](https://github.com/google-gemini/gemini-cli/issues/2094) | 20 | 2025-06-27 → 2026-05-04 | Show costs |

### 1.4 anomalyco/opencode (formerly sst/opencode; `sst/opencode` no longer resolves) ([open](https://github.com/anomalyco/opencode/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc), [closed not-planned](https://github.com/anomalyco/opencode/issues?q=is%3Aissue%20is%3Aclosed%20reason%3Anot-planned%20sort%3Areactions-%2B1-desc))

**Open (3,337)**

| # | 👍 | Created | Underlying need |
|---|---:|---|---|
| [11176](https://github.com/anomalyco/opencode/issues/11176) | 162 | 2026-01-29 | Official VS Code extension |
| [27167](https://github.com/anomalyco/opencode/issues/27167) | 153 | 2026-05-12 | Native session goals (`/goal`) |
| [1168](https://github.com/anomalyco/opencode/issues/1168) | 145 | 2025-07-20 | Clickable links in the TUI |
| [6152](https://github.com/anomalyco/opencode/issues/6152) | 140 | 2025-12-25 | Show session context usage (like `/context`) |
| [10288](https://github.com/anomalyco/opencode/issues/10288) | 97 | 2026-01-23 | Mobile or web client |
| [2242](https://github.com/anomalyco/opencode/issues/2242) | 79 | 2025-08-25 | Sandbox the agent |
| [38281](https://github.com/anomalyco/opencode/issues/38281) | 63 | 2026-07-22 | List "opencode-quota" in the ecosystem (a quota plugin) |
| [4714](https://github.com/anomalyco/opencode/issues/4714) | 61 | 2025-11-24 | Search inside the session buffer |
| [23153](https://github.com/anomalyco/opencode/issues/23153) | 58 | 2026-04-17 | Pay for Go with crypto |
| [10884](https://github.com/anomalyco/opencode/issues/10884) | 57 | 2026-01-27 | MCP Apps in the desktop app |
| [7624](https://github.com/anomalyco/opencode/issues/7624) | 52 | 2026-01-10 | Base-path routing for the web UI |
| [37564](https://github.com/anomalyco/opencode/issues/37564) | 42 | 2026-07-17 | Classifier-based auto-approval of permissions |
| [12472](https://github.com/anomalyco/opencode/issues/12472) | 41 | 2026-02-06 | Claude Code hooks compatibility |
| [785](https://github.com/anomalyco/opencode/issues/785) | 39 | 2025-07-08 | Disable streaming |
| [27110](https://github.com/anomalyco/opencode/issues/27110) | 38 | 2026-05-12 | Cap the number of parallel subagents |
| [28696](https://github.com/anomalyco/opencode/issues/28696) | 36 | 2026-05-21 | Plugin, agent and skill marketplace |
| [48882](https://github.com/anomalyco/opencode/issues/48882) | 35 | 2026-09-14 | Restore the legacy sidebar UI |
| [6680](https://github.com/anomalyco/opencode/issues/6680) | 29 | 2026-01-02 | View archived sessions on desktop |
| [15988](https://github.com/anomalyco/opencode/issues/15988) | 28 | 2026-03-04 | "Retry now" button to skip the rate-limit countdown |

**Closed as "not planned" (14,124)** (many are v1-cutoff or bot closures; see caveat 2)

| # | 👍 | Created → closed | Underlying need |
|---|---:|---|---|
| [7410](https://github.com/anomalyco/opencode/issues/7410) | 357 | 2026-01-09 → 2026-03-29 | Claude Max login broken (Anthropic blocked third-party use) |
| [6231](https://github.com/anomalyco/opencode/issues/6231) | 244 | 2025-12-27 → 2026-10-11 | Auto-discover models from OpenAI-compatible endpoints |
| [2072](https://github.com/anomalyco/opencode/issues/2072) | 195 | 2025-08-19 → 2026-09-14 | Use a Cursor subscription |
| [1764](https://github.com/anomalyco/opencode/issues/1764) | 189 | 2025-08-09 → 2026-09-14 | Vim motions in the input box |
| [4695](https://github.com/anomalyco/opencode/issues/4695) | 176 | 2025-11-24 → 2026-06-04 | Speech-to-text input |
| [1543](https://github.com/anomalyco/opencode/issues/1543) | 149 | 2025-08-02 → 2026-04-27 | Add directories or workspaces |
| [4283](https://github.com/anomalyco/opencode/issues/4283) | 133 | 2025-11-13 → 2026-10-11 | Copy to clipboard not working |
| [2177](https://github.com/anomalyco/opencode/issues/2177) | 128 | 2025-08-22 → 2026-08-16 | Change the working directory explicitly |
| [7101](https://github.com/anomalyco/opencode/issues/7101) | 128 | 2026-01-06 → 2026-07-23 | Custom system prompts (global/project) |
| [7602](https://github.com/anomalyco/opencode/issues/7602) | 120 | 2026-01-10 → 2026-10-13 | Native model fallback/failover |
| [12661](https://github.com/anomalyco/opencode/issues/12661) | 119 | 2026-02-08 → 2026-08-07 | Equivalent of Claude Code agent teams |
| [7846](https://github.com/anomalyco/opencode/issues/7846) | 119 | 2026-01-11 → 2026-10-01 | `/skills` command |
| [6815](https://github.com/anomalyco/opencode/issues/6815) | 92 | 2026-01-04 → 2026-05-22 | Reload config without restarting |
| [5887](https://github.com/anomalyco/opencode/issues/5887) | 83 | 2025-12-21 → 2026-08-20 | True async background subagents |
| [8003](https://github.com/anomalyco/opencode/issues/8003) | 82 | 2026-01-12 → 2026-09-01 | VS Code diff preview for reviewing changes |
| [2755](https://github.com/anomalyco/opencode/issues/2755) | 80 | 2025-09-24 → 2026-06-14 | Copy mode |
| [6096](https://github.com/anomalyco/opencode/issues/6096) | 73 | 2025-12-24 → 2026-09-09 | Tokens-per-second display |
| [19515](https://github.com/anomalyco/opencode/issues/19515) | 72 | 2026-03-28 → 2026-09-17 | Explicit multi-directory workspaces |
| [768](https://github.com/anomalyco/opencode/issues/768) | 70 | 2025-07-08 → 2026-05-14 | Track GitHub Copilot premium requests |
| [8140](https://github.com/anomalyco/opencode/issues/8140) | 63 | 2026-01-13 → 2026-07-06 | Configurable context limit and compaction threshold |
| [5076](https://github.com/anomalyco/opencode/issues/5076) | 61 | 2025-12-04 → 2026-06-14 | Safer, security-minded defaults |
| [459](https://github.com/anomalyco/opencode/issues/459) | 60 | 2025-06-27 → 2026-08-02 | Clarify privacy and data collection |
| [1302](https://github.com/anomalyco/opencode/issues/1302) | 58 | 2025-07-25 → 2026-07-11 | Dynamic API keys via `apiKeyHelper` |

### 1.5 cline/cline (issues are low-signal; feature requests live in Discussions)
- **Issues:** the top open issue is [5915](https://github.com/cline/cline/issues/5915) (57), a request to remove the "use Claude 4 Sonnet" warning. The rest are 14 or fewer. The top closed-not-planned issue is [6398](https://github.com/cline/cline/issues/6398), a JetBrains healthcheck bug (21).
- **[Discussions, Feature Requests, sorted top](https://github.com/cline/cline/discussions/categories/feature-requests?discussions_q=category%3A%22Feature+Requests%22+sort%3Atop)** (40 pages; upvotes):

| # | Upvotes | Created | State | Need |
|---|---:|---|---|---|
| [581](https://github.com/cline/cline/discussions/581) | 1,193 | 2024-10-21 | closed | IntelliJ plugin |
| [387](https://github.com/cline/cline/discussions/387) | 212 | 2024-09-24 | closed | Separate models for planning and coding |
| [1243](https://github.com/cline/cline/discussions/1243) | 160 | 2025-01-10 | closed | Zed extension |
| [527](https://github.com/cline/cline/discussions/527) | 157 | 2024-10-13 | open | Visual Studio 2022 |
| [1083](https://github.com/cline/cline/discussions/1083) | 151 | 2024-12-30 | open | Tab autocomplete |
| [1344](https://github.com/cline/cline/discussions/1344) | 104 | 2025-01-20 | open | Vim/Emacs |
| [386](https://github.com/cline/cline/discussions/386) | 100 | 2024-09-24 | open | Multiple OpenAI-compatible provider slots |
| [2790](https://github.com/cline/cline/discussions/2790) | 99 | 2025-04-10 | open | Neovim |
| [401](https://github.com/cline/cline/discussions/401) | 81 | 2024-09-25 | open | Prompt library |
| [6162](https://github.com/cline/cline/discussions/6162) | 79 | 2025-09-12 | open | AGENTS.md support |
| [2418](https://github.com/cline/cline/discussions/2418) | 68 | 2025-03-25 | open | Project-level MCP configuration |
| [869](https://github.com/cline/cline/discussions/869) | 62 | 2024-12-07 | open | Multiple API keys with easy switching |
| [499](https://github.com/cline/cline/discussions/499) | 61 | 2024-10-11 | open | Better options when context length is exceeded |
| [3415](https://github.com/cline/cline/discussions/3415) | 55 | 2025-05-09 | open | Use MCP server prompts |
| [414](https://github.com/cline/cline/discussions/414) | 43 | 2024-09-27 | open | Longer prompt caching |

### 1.6 Cursor (forum Feature Requests by votes; GitHub issues hidden)
Model-addition requests (45 of the top 240, such as "Kimi K2" or "GLM 5") are excluded below, because no outside product can add a model to Cursor. Staff stance seen: account switching "very low priority unless a lot of people want this" (2025-06-11, [58411](https://forum.cursor.com/t/seamless-account-switching-in-cursor/58411)). On a rate meter, a company-side reply said it "would also lead to more complaints" (2025-06-20, [106556](https://forum.cursor.com/t/request-to-add-a-rate-limit-meter-for-pro-plan/106556)).

Top 75 non-model feature requests by votes (votes / likes as of 2026-10-15):

| Votes | Likes | Created | Closed? | Request (title) |
|---:|---:|---|---|---|
| 614 | 2436 | 2025-09-17 | closed | [Student Verifications outside USA and organizations without .edu email](https://forum.cursor.com/t/student-verifications-outside-usa-and-organizations-without-edu-email/133736) |
| 307 | 362 | 2024-09-04 | open | [Jupyter Notebook support](https://forum.cursor.com/t/jupyter-notebook-support/14851) |
| 297 | 195 | 2025-03-30 | open | [Increase the 25 tool calls limit](https://forum.cursor.com/t/increase-the-25-tool-calls-limit/72553) |
| 219 | 149 | 2025-06-20 | closed | [Background Agent + Bugbot for Bitbucket](https://forum.cursor.com/t/background-agent-bugbot-for-bitbucket/106759) |
| 178 | 287 | 2025-03-03 | open | [Seamless Account Switching in Cursor](https://forum.cursor.com/t/seamless-account-switching-in-cursor/58411) |
| 166 | 167 | 2024-09-16 | closed | [Please consider a JetBrains plugin](https://forum.cursor.com/t/please-consider-a-jetbrains-plugin/17042) |
| 165 | 112 | 2025-06-06 | open | [Bugbot for GitLab](https://forum.cursor.com/t/bugbot-for-gitlab/100885) |
| 131 | 99 | 2024-11-11 | open | [Add Support for Ollama natively](https://forum.cursor.com/t/add-support-for-ollama-natively/27291) |
| 125 | 122 | 2023-12-06 | closed | [Add local PDF via @Docs](https://forum.cursor.com/t/add-local-pdf-via-docs/1945) |
| 111 | 37 | 2025-07-03 | open | [Enhanced GitLab Integration for Cursor](https://forum.cursor.com/t/enhanced-gitlab-integration-for-cursor/112962) |
| 105 | 55 | 2025-06-19 | open | [Bugbot and Background Agents for Azure Devops](https://forum.cursor.com/t/bugbot-and-background-agents-for-azure-devops/105680) |
| 98 | 93 | 2025-06-24 | open | [Add sound when a confirmation is needed](https://forum.cursor.com/t/add-sound-when-a-confirmation-is-needed/108718) |
| 95 | 234 | 2023-08-23 | open | [Sync of keybindings and settings](https://forum.cursor.com/t/sync-of-keybindings-and-settings/31) |
| 95 | 84 | 2025-06-20 | open | [Request to add a rate limit meter for PRO PLAN](https://forum.cursor.com/t/request-to-add-a-rate-limit-meter-for-pro-plan/106556) |
| 91 | 168 | 2024-10-10 | open | [Please send me an email each billing cycle](https://forum.cursor.com/t/please-send-me-an-email-each-billing-cycle/22101) |
| 86 | 171 | 2024-07-05 | closed | [Cursor plugin for Neovim?](https://forum.cursor.com/t/cursor-plugin-for-neovim/6234) |
| 82 | 186 | 2025-04-04 | open | [Update vscode version to latest](https://forum.cursor.com/t/update-vscode-version-to-latest/75154) |
| 81 | 189 | 2024-10-07 | closed | [Submit prompt with control+enter in composer](https://forum.cursor.com/t/submit-prompt-with-control-enter-in-composer/21405) |
| 80 | 80 | 2025-11-25 | open | [Return the Custom Modes features](https://forum.cursor.com/t/return-the-custom-modes-features/144170) |
| 78 | 118 | 2025-09-06 | closed | [Does Cursor Cli support ACP?](https://forum.cursor.com/t/does-cursor-cli-support-acp/132783) |
| 78 | 52 | 2024-12-04 | open | [Feature request: Long context mode](https://forum.cursor.com/t/feature-request-long-context-mode/32187) |
| 64 | 70 | 2025-06-07 | open | [Cursor needs awareness of the UI 👀](https://forum.cursor.com/t/cursor-needs-awareness-of-the-ui/101532) |
| 56 | 17 | 2024-11-29 | open | [Online Cursor IDE](https://forum.cursor.com/t/online-cursor-ide/31178) |
| 56 | 45 | 2025-09-16 | open | [Team Cursor, we want pre-release changelogs](https://forum.cursor.com/t/team-cursor-we-want-pre-release-changelogs/133634) |
| 52 | 30 | 2025-10-15 | open | [Cloud Sync for Chat History](https://forum.cursor.com/t/cloud-sync-for-chat-history/137456) |
| 52 | 36 | 2025-07-03 | open | [Ability to get invoice via (additional) email address(es)](https://forum.cursor.com/t/ability-to-get-invoice-via-additional-email-address-es/112720) |
| 49 | 44 | 2025-08-08 | closed | [Does Cursor support SubAgents?](https://forum.cursor.com/t/does-cursor-support-subagents/127331) |
| 46 | 43 | 2025-02-09 | open | [Supervisory agent to guide "worker" agent](https://forum.cursor.com/t/supervisory-agent-to-guide-worker-agent/49395) |
| 44 | 188 | 2026-07-12 | open | [Cursor Android mobile app](https://forum.cursor.com/t/cursor-android-mobile-app/165496) |
| 42 | 46 | 2024-12-26 | open | [Custom model section in Settings > Models](https://forum.cursor.com/t/custom-model-section-in-settings-models/37487) |
| 41 | 79 | 2024-10-04 | open | [Suggestions delay](https://forum.cursor.com/t/suggestions-delay/21023) |
| 41 | 19 | 2025-01-10 | closed | [Subdirectory-Specific .cursorrules Support](https://forum.cursor.com/t/subdirectory-specific-cursorrules-support/40566) |
| 40 | 41 | 2025-06-17 | open | [Self-hosted Git support](https://forum.cursor.com/t/self-hosted-git-support/104707) |
| 40 | 45 | 2025-06-17 | open | [Disable the Enter key to send the chat](https://forum.cursor.com/t/disable-the-enter-key-to-send-the-chat/104598) |
| 38 | 28 | 2025-07-27 | closed | [Sub agents for the agent to delegate tasks to](https://forum.cursor.com/t/sub-agents-for-the-agent-to-delegate-tasks-to/123265) |
| 38 | 119 | 2025-05-24 | closed | [Cursor Students for Brazil](https://forum.cursor.com/t/cursor-students-for-brazil/96275) |
| 38 | 55 | 2025-06-04 | open | [Cursor needs to be aware of the current date](https://forum.cursor.com/t/cursor-needs-to-be-aware-of-the-current-date/100297) |
| 37 | 49 | 2024-12-04 | open | [Option to hear a sound when response is complete](https://forum.cursor.com/t/option-to-hear-a-sound-when-response-is-complete/32409) |
| 37 | 36 | 2024-12-04 | open | [Add back full screen Compose window with side-by-side diffs](https://forum.cursor.com/t/add-back-full-screen-compose-window-with-side-by-side-diffs/32416) |
| 36 | 65 | 2023-11-06 | open | [Word wrap in chat sidebar](https://forum.cursor.com/t/word-wrap-in-chat-sidebar/1435) |
| 36 | 33 | 2025-06-04 | open | [Timestamp for Chat Messages & Tool Calls](https://forum.cursor.com/t/timestamp-for-chat-messages-tool-calls/100135) |
| 36 | 41 | 2025-04-15 | open | [Resolve local environment variables in MCP server definitions](https://forum.cursor.com/t/resolve-local-environment-variables-in-mcp-server-definitions/79639) |
| 35 | 77 | 2023-10-16 | open | [Support local LLM's](https://forum.cursor.com/t/support-local-llms/1099) |
| 35 | 26 | 2024-10-30 | open | [Customize @Git Diff Base Branch](https://forum.cursor.com/t/customize-git-diff-base-branch/25434) |
| 34 | 29 | 2025-04-01 | open | [Public roadmap?](https://forum.cursor.com/t/public-roadmap/73472) |
| 34 | 24 | 2025-03-17 | open | [Feature Request: Add the ability to switch between multiple GitHub accounts (work/personal) within Cursor IDE without logging out and back in](https://forum.cursor.com/t/feature-request-add-the-ability-to-switch-between-multiple-github-accounts-work-personal-within-cursor-ide-without-logging-out-and-back-in/65329) |
| 34 | 100 | 2023-10-12 | open | [AI git commit messages](https://forum.cursor.com/t/ai-git-commit-messages/1027) |
| 34 | 32 | 2025-05-29 | open | [Show Current Context Window Size - Feature Request](https://forum.cursor.com/t/show-current-context-window-size-feature-request/98127) |
| 33 | 28 | 2025-10-30 | open | [Enable Multi-Agents Support for Multi-root Workspaces](https://forum.cursor.com/t/enable-multi-agents-support-for-multi-root-workspaces/139703) |
| 33 | 154 | 2023-08-25 | closed | [How do I export chat with AI?](https://forum.cursor.com/t/how-do-i-export-chat-with-ai/144) |
| 31 | 55 | 2025-07-01 | open | [Just cusor tab plan](https://forum.cursor.com/t/just-cusor-tab-plan/111607) |
| 31 | 38 | 2025-06-24 | open | [Discord integration for Background Agent](https://forum.cursor.com/t/discord-integration-for-background-agent/108638) |
| 31 | 114 | 2024-08-16 | open | [Ambiguity with the Tab Key in Cursor](https://forum.cursor.com/t/ambiguity-with-the-tab-key-in-cursor/7663) |
| 30 | 9 | 2025-04-09 | open | [Implement Support for Google’s Agent2Agent (A2A) Protocol](https://forum.cursor.com/t/implement-support-for-google-s-agent2agent-a2a-protocol/77192) |
| 30 | 53 | 2024-10-15 | open | [Text to Speech feature request for reading out generated code and explanations](https://forum.cursor.com/t/text-to-speech-feature-request-for-reading-out-generated-code-and-explanations/23000) |
| 30 | 24 | 2025-10-12 | open | [Multi-repository background agent mode](https://forum.cursor.com/t/multi-repository-background-agent-mode/137147) |
| 29 | 44 | 2025-08-23 | open | [Option to disable "Diffs & Review" interface in editor](https://forum.cursor.com/t/option-to-disable-diffs-review-interface-in-editor/131728) |
| 28 | 36 | 2025-03-19 | open | [Transparency on "auto" model selection](https://forum.cursor.com/t/transparency-on-auto-model-selection/66961) |
| 28 | 24 | 2025-07-07 | open | [Request: Hooks support (post-edit, pre-edit, etc...)](https://forum.cursor.com/t/request-hooks-support-post-edit-pre-edit-etc/114716) |
| 28 | 29 | 2025-02-10 | closed | [Cursor memory bank](https://forum.cursor.com/t/cursor-memory-bank/49776) |
| 27 | 21 | 2025-08-19 | open | [Enable Early Subscription Renewal (Manual Top-Up) to Avoid Pay-As-You-Go Between Cycles](https://forum.cursor.com/t/enable-early-subscription-renewal-manual-top-up-to-avoid-pay-as-you-go-between-cycles/130769) |
| 27 | 29 | 2025-10-14 | open | [Windsurf has released Codemaps feature](https://forum.cursor.com/t/windsurf-has-released-codemaps-feature/137416) |
| 27 | 35 | 2025-08-08 | open | [Add back the "Reapply" feature for code snippets](https://forum.cursor.com/t/add-back-the-reapply-feature-for-code-snippets/127349) |
| 27 | 37 | 2024-07-22 | open | [AI-generated commit message](https://forum.cursor.com/t/ai-generated-commit-message/6650) |
| 26 | 39 | 2025-08-12 | open | [1M context sonnet 4](https://forum.cursor.com/t/1m-context-sonnet-4/128867) |
| 26 | 15 | 2025-01-10 | closed | [Supabase Integration](https://forum.cursor.com/t/supabase-integration/40572) |
| 25 | 82 | 2026-07-17 | open | [Please bring back the CSS Inspector+panel it was the best feature any designer needed](https://forum.cursor.com/t/please-bring-back-the-css-inspector-panel-it-was-the-best-feature-any-designer-needed/165970) |
| 25 | 27 | 2025-11-24 | open | [typescript.experimental.expandableHover](https://forum.cursor.com/t/typescript-experimental-expandablehover/143948) |
| 25 | 25 | 2025-04-14 | open | [MCP tools allowlist to autorun](https://forum.cursor.com/t/mcp-tools-allowlist-to-autorun/79051) |
| 25 | 6 | 2026-01-01 | open | [Introduce ralph in cursor](https://forum.cursor.com/t/introduce-ralph-in-cursor/147764) |
| 25 | 27 | 2024-12-05 | open | [Request - spell check in chats!](https://forum.cursor.com/t/request-spell-check-in-chats/32569) |
| 25 | 148 | 2025-08-03 | closed | [Request to Extend Student Discount to additional countries or universities](https://forum.cursor.com/t/request-to-extend-student-discount-to-additional-countries-or-universities/125379) |
| 25 | 4 | 2025-07-01 | open | [Add gitlab support](https://forum.cursor.com/t/add-gitlab-support/111501) |
| 24 | 10 | 2024-09-25 | open | [Gift subscriptions](https://forum.cursor.com/t/gift-subscriptions/18753) |
| 23 | 20 | 2026-02-19 | open | [Option to save Plans in project-level .cursor directory](https://forum.cursor.com/t/option-to-save-plans-in-project-level-cursor-directory/152291) |

### 1.7 zed-industries/zed (AI/agent focus)
- **Overall open top** (2,271 open; mostly editor features): [4355](https://github.com/zed-industries/zed/issues/4355) smooth scrolling (886) · [5242](https://github.com/zed-industries/zed/issues/5242) test runner (883) · [21538](https://github.com/zed-industries/zed/issues/21538) jj (563) · [9662](https://github.com/zed-industries/zed/issues/9662) multi-monitor windows (459) · [21208](https://github.com/zed-industries/zed/issues/21208) webviews in extensions (449) · [12589](https://github.com/zed-industries/zed/issues/12589) downloads Node/npm without consent (305) · [5010](https://github.com/zed-industries/zed/issues/5010) settings sync (179) · [24878](https://github.com/zed-industries/zed/issues/24878) offline support (168) · [59157](https://github.com/zed-industries/zed/issues/59157) **PR-style review comments in the git diff that feed the active agent thread (116, 2026-06-11)**.
- **`label:"area:ai"` open** (45 open; low counts): [18274](https://github.com/zed-industries/zed/issues/18274) Amazon Q (64) · [34154](https://github.com/zed-industries/zed/issues/34154) plaintext Rules Library instead of LMDB (63) · [31788](https://github.com/zed-industries/zed/issues/31788) Ollama slow (42) · [42074](https://github.com/zed-industries/zed/issues/42074) AI rewrites whole files (33) · [16156](https://github.com/zed-industries/zed/issues/16156) per-project AI controls (32) · [40439](https://github.com/zed-industries/zed/issues/40439) API keys in plaintext settings (22) · [28676](https://github.com/zed-industries/zed/issues/28676) checkpoint restore is irreversibly destructive (16) · [58676](https://github.com/zed-industries/zed/issues/58676) search thread history (11).
- **`area:ai/agent thread`** (138 open): [15862](https://github.com/zed-industries/zed/issues/15862) render markdown in the assistant (54) · [16410](https://github.com/zed-industries/zed/issues/16410) dictation (52) · [28473](https://github.com/zed-industries/zed/issues/28473) rules-file selection (22). **`area:ai/acp`** (93 open): [51341](https://github.com/zed-industries/zed/issues/51341) ACP sessions missing from history (18) · [53201](https://github.com/zed-industries/zed/issues/53201) prompts repeated (17).
- **`area:ai` closed not-planned** (291): [4504](https://github.com/zed-industries/zed/issues/4504) Tabnine (92) · [4536](https://github.com/zed-industries/zed/issues/4536) Cody (69) · [4421](https://github.com/zed-industries/zed/issues/4421) Tabby (50).
- **[Discussions sorted top](https://github.com/zed-industries/zed/discussions?discussions_q=sort%3Atop)** (feature requests moved here): [34759](https://github.com/zed-industries/zed/discussions/34759) review GitHub PRs inside Zed (605) · [35996](https://github.com/zed-industries/zed/discussions/35996) devenv (311) · [25936](https://github.com/zed-industries/zed/discussions/25936) Jupyter (293) · [34436](https://github.com/zed-industries/zed/discussions/34436) planning mode / specs (139) · [49313](https://github.com/zed-industries/zed/discussions/49313) mobile app to control agent runs remotely (80) · [54965](https://github.com/zed-industries/zed/discussions/54965) fork a conversation into a new thread (71) · [58333](https://github.com/zed-industries/zed/discussions/58333) collapse ACP transcript blocks (67) · [57428](https://github.com/zed-industries/zed/discussions/57428) persistent terminal threads (62) · [53879](https://github.com/zed-industries/zed/discussions/53879) show the actual command the AI runs (59).

### 1.8 warpdotdev/Warp ([open](https://github.com/warpdotdev/Warp/issues?q=is%3Aissue%20is%3Aopen%20sort%3Areactions-%2B1-desc))
Open: 3,937.

| # | 👍 | Created | Underlying need |
|---|---:|---|---|
| [4339](https://github.com/warpdotdev/warp/issues/4339) | 1,233 | 2024-02-26 | Local LLMs (Ollama) for Warp AI |
| [257](https://github.com/warpdotdev/warp/issues/257) | 478 | 2021-10-08 | Embed in VS Code |
| [1811](https://github.com/warpdotdev/warp/issues/1811) | 372 | 2022-09-07 | Bypass Warp completions for the shell's own tab completion |
| [2038](https://github.com/warpdotdev/warp/issues/2038) | 282 | 2022-11-02 | NuShell |
| [537](https://github.com/warpdotdev/warp/issues/537) | 281 | 2021-12-17 | `bindkey` support |
| [1194](https://github.com/warpdotdev/warp/issues/1194) | 253 | 2022-04-26 | UI localization |
| [4860](https://github.com/warpdotdev/warp/issues/4860) | 189 | 2024-05-01 | Amazon Q integration |
| [4008](https://github.com/warpdotdev/warp/issues/4008) | 176 | 2023-12-28 | Disable line wrapping |
| [3935](https://github.com/warpdotdev/warp/issues/3935) | 169 | 2023-12-05 | Zellij |
| [4939](https://github.com/warpdotdev/warp/issues/4939) | 164 | 2024-05-21 | Change account email/name |
| [472](https://github.com/warpdotdev/warp/issues/472) | 154 | 2021-12-01 | Embed in JetBrains |
| [5640](https://github.com/warpdotdev/warp/issues/5640) | 113 | 2024-12-31 | Full offline support |
| [7326](https://github.com/warpdotdev/warp/issues/7326) | 75 | 2025-09-05 | Agent Client Protocol (ACP) |
| [6831](https://github.com/warpdotdev/warp/issues/6831) | 72 | 2025-07-14 | AI features over SSH |
| [6744](https://github.com/warpdotdev/warp/issues/6744) | 71 | 2025-07-02 | AI features in WSL |
| [8506](https://github.com/warpdotdev/warp/issues/8506) | 68 | 2026-01-25 | Bedrock (Claude) as a first-class provider |
| [8803](https://github.com/warpdotdev/warp/issues/8803) | 60 | 2026-03-02 | Custom language servers |
| [1862](https://github.com/warpdotdev/warp/issues/1862) | 60 | 2022-09-22 | Show execution time |
| [6957](https://github.com/warpdotdev/warp/issues/6957) | 58 | 2025-08-01 | Unlimited scrollback |

**Closed as "not planned":** [1823](https://github.com/warpdotdev/warp/issues/1823) Chinese UI (207) · [1979](https://github.com/warpdotdev/warp/issues/1979) zsh/bash completions (76) · [6629](https://github.com/warpdotdev/warp/issues/6629) previous tab-bar style (44).
**#4339 status (thread):** first closed as not planned on 2024-04-03, then reopened and pinned on 2025-01-17. Custom OpenAI-compatible endpoints shipped around 2026-05-22. On 2026-09-13 a contributor explained that agent requests are proxied through Warp's servers, so `localhost` endpoints fail without a public tunnel. A community "Local-Warp" fork exists ([wolverine2k/warp](https://github.com/wolverine2k/warp)).

### 1.9 ghostty-org/ghostty ([Discussions, Feature Requests, sorted top](https://github.com/ghostty-org/ghostty/discussions/categories/feature-requests-ideas?discussions_q=category%3A%22Feature+Requests%2C+Ideas%22+sort%3Atop))
[3227](https://github.com/ghostty-org/ghostty/discussions/3227) send input to multiple panes (410, open since 2024-12-27; collaborator jcollie pointed to PR #13745 on 2026-09-30) · [2355](https://github.com/ghostty-org/ghostty/discussions/2355) smooth scrolling (136) · [3206](https://github.com/ghostty-org/ghostty/discussions/3206) sub-cell scrolling (110) · [7607](https://github.com/ghostty-org/ghostty/discussions/7607) command blocks (17) · [13450](https://github.com/ghostty-org/ghostty/discussions/13450) quick-select to open links (16) · [10603](https://github.com/ghostty-org/ghostty/discussions/10603) `GHOSTTY_SESSION_ID` plus external focus (15; agent tools like revdiff can't target their own pane) · [5209](https://github.com/ghostty-org/ghostty/discussions/5209) automatic session output logging (9).

### 1.10 Secondary segment: native Mac dev tools (quick pass)
- **orbstack/orbstack** (394 open): [88](https://github.com/orbstack/orbstack/issues/88) Podman (568) · [11](https://github.com/orbstack/orbstack/issues/11) custom VM images (411) · **[2295](https://github.com/orbstack/orbstack/issues/2295) support `docker sandbox` for AI agent sandboxing (233, 2026-01-07; no maintainer reply shown; users say they may switch runtimes)** · **[2056](https://github.com/orbstack/orbstack/issues/2056) Docker MCP Gateway (96)** · [2175](https://github.com/orbstack/orbstack/issues/2175) MCP gateway/toolkit (18).
- **ProxymanApp/Proxyman** (1,912 open): top requests are protocol coverage, none agent-related: [565](https://github.com/ProxymanApp/Proxyman/issues/565) TCP/UDP (45) · [138](https://github.com/ProxymanApp/Proxyman/issues/138) Linux (40) · [416](https://github.com/ProxymanApp/Proxyman/issues/416) HTTP/2 (29).
- **TablePlus/TablePlus** (1,435 open): database drivers dominate, such as [666](https://github.com/TablePlus/TablePlus/issues/666) DynamoDB (276) and [1237](https://github.com/TablePlus/TablePlus/issues/1237) Vim keybindings (184). Also [3065](https://github.com/TablePlus/TablePlus/issues/3065) AI SQL completion (39).

---

## 2. Thread deep-dives: maintainer stance and workarounds
(Source: WebFetch reads of each thread on 2026-10-15. "Commenter" means an unverified user claim.)

- **Multi-account, CC [#18435](https://github.com/anthropics/claude-code/issues/18435) (902):** no Anthropic reply. A commenter says mobile shipped switching on 2026-09-13 ([#36151](https://github.com/anthropics/claude-code/issues/36151)). Another commenter says the Desktop bundle contains multi-account code behind a flag, plus an `authentication.disableMultiAccount` policy. Workarounds include a second Electron instance with `--user-data-dir`, which shares the bundle ID, so the `claude://` sign-in callback can land in the wrong instance. Tools: [Lanes](https://github.com/synthetixis/lanes) (12★, MIT), [multi-claude](https://github.com/thomasog/multi-claude), [cloak](https://github.com/synth1s/cloak).
- **Multi-account, Codex [#4432](https://github.com/openai/codex/issues/4432) (130):** maintainer, 2026-03-06: "we generally prioritize feature requests based on upvotes". Some users rotate subscriptions when a weekly quota runs out. Tools: [aisw](https://github.com/burakdede/aisw), codexmux, aistat (auto-picks the account with the most 5-hour headroom), [clausona](https://github.com/larcane97/clausona), multi-codex.
- **Auto-resume, CC [#13354](https://github.com/anthropics/claude-code/issues/13354) (209):** no maintainer reply. Commenters report the **Desktop app** gained a "resume on budget renewal" checkbox around 2026-08-15, while the CLI still doesn't resume (v2.1.233). Tools: softcane/cc-session-recover, rohanprichard/claude-overnight, MagicYangG/claude-limit-relay (Windows only; uses `claude --resume -p` and pre-warms the 5-hour window).
- **Quota, CC [#13585](https://github.com/anthropics/claude-code/issues/13585) (128):** no maintainer reply. Partial native support: statusline `rate_limits` (v2.1.80, per commenter), headless `/usage` returns prose, and the Mod usage API (2.1.287). Many tools call the undocumented `api.anthropic.com/api/oauth/usage`, which carries ToS and breakage risk.
- **Diff review, CC [#33932](https://github.com/anthropics/claude-code/issues/33932) (206):** no maintainer reply. Root cause per a commenter: Claude Code writes to disk directly, bypassing VS Code's edit API, so it gets no gutter or per-hunk accept/reject. Tools: [hunkwise](https://github.com/molon/hunkwise) (94★), `dfarkash.claude-edits-scm` (VS Code Marketplace).
- **Diff approval, Codex [#2998](https://github.com/openai/codex/issues/2998) (236):** maintainer, 2025-09-18, pointed to "View all changes" and said "We will also be iterating on this surface over time". Users still report no approve/reject-with-feedback as of 2026-09-08.
- **Undo, Codex [#9203](https://github.com/openai/codex/issues/9203) (482):** maintainer, 2026-01-16: "the previous experimental implementation had problems... If we bring it back, it will need to be redesigned". Pain points: untracked and gitignored files lost, and the agent deleting files. Tools: snap-back (0★), agentckpt (1★).
- **Rewind, Codex [#11626](https://github.com/openai/codex/issues/11626) (228):** open with no roadmap. Pain points per commenters: shell-made edits (`cat << EOF`) are untracked, ghost commits caused index-clobbering data loss (#8214), and Desktop checkpoints left 100+ GB of orphaned objects (#29388). Tool: [codex-rewind](https://github.com/extracurricular-ai/codex-rewind) (54★, a fork installed as `codexr`).
- **Claude Code's own rewind has gaps** ([official docs](https://code.claude.com/docs/en/checkpointing)): "Checkpointing does not track files modified by Bash commands." Subagent edits are usually not restored, external changes are not tracked, symlinked and hard-linked files are skipped, and snapshots are swept after about 30 days.
- **Notifications, Codex [#3962](https://github.com/openai/codex/issues/3962) (201):** desktop and IDE notification requests were merged into this issue. The `notify` hook exists, and the status of a native sound setting is unclear. Open pain points: telling "needs approval" apart from "done", knowing which session or tab needs attention, and Remote-SSH. Tools: codex-attention-notifier, ai-agent-notifier, Bellows (a desktop app, author-disclosed).
- **Notifications, Cursor [108718](https://forum.cursor.com/t/add-sound-when-a-confirmation-is-needed/108718) (98 votes):** staff said "we'll consider it" (2025-06-25). A completion sound exists, but an approval sound is not confirmed. With several chats running, users can't tell which one needs them.
- **Copy/paste, CC [#18170](https://github.com/anthropics/claude-code/issues/18170) (300):** open since 2026-01-14 and regressed. The only maintainer action is a label (2026-08-20). It affects Terminal.app, iTerm2, the VS Code and JetBrains terminals, gnome-terminal, and cmux. Workarounds: `/copy`, Ghostty `copy_to_clipboard:plain`, the AH-Merii copy-code plugin, and a hook that writes output to a log file.
- **History sync, CC [#28791](https://github.com/anthropics/claude-code/issues/28791) (150):** no reply. The docs say each surface keeps its own history by design. Workarounds write into Desktop's internal index: BasedGPT/claude-code-session-recovery and viliusjask/claude-wsl-session-importer. Sharing `CLAUDE_CONFIG_DIR` across machines makes them clobber each other's tokens.
- **Sandbox, opencode [#2242](https://github.com/anomalyco/opencode/issues/2242) (79):** a maintainer said "we need better sandboxing" (2025-08-25) but gave no plan. Restricting to the working directory can be bypassed through bash. Tools: aicage, Anthropic sandbox-runtime, sandbox-exec gists, ocs, Fence, contai, SandVault, nono.sh, Grimdall, Vestige.
- **Sandbox, OrbStack [#2295](https://github.com/orbstack/orbstack/issues/2295) (233):** no maintainer reply in 9 months. Users reject installing Docker Desktop and fall back to a VPS, nested LXD, or [servusdei2018/sandbox](https://github.com/servusdei2018/sandbox) (12★).
- **AGENTS.md, CC [#31005](https://github.com/anthropics/claude-code/issues/31005) (411):** v2.1.277 (2026-09-18) reads AGENTS.md *only when no CLAUDE.md exists*. `.agents/skills/` is still unsupported. Whole-directory symlinks break because Claude Code writes `.system/` files into the directory.
- **Local LLMs, Warp [#4339](https://github.com/warpdotdev/warp/issues/4339) (1,233):** see 1.8. Requests are proxied through Warp's cloud, so an outside local proxy only works through a public tunnel.
- **LSP, Codex [#8745](https://github.com/openai/codex/issues/8745) (503):** maintainer, 2026-01-06: LSP "was not designed for coding agents", and internal experiments "hasn't provide the benefits" expected. Filled by MCP servers (see §3).
- **Linear, CC [#12925](https://github.com/anthropics/claude-code/issues/12925) (148):** no reply. Codex and Cursor have native Linear agents. Tools: [linear-claude-bridge](https://github.com/MPIsaac-Per/linear-claude-bridge) (MIT, uses the Agent SDK on your machine), [claude-linear-agent](https://github.com/ian-klopper/claude-linear-agent), Cyrus.
- **Claude Projects, CC [#2511](https://github.com/anthropics/claude-code/issues/2511) (421):** no reply in 16 months, and no public Projects API. Outside fit is poor (it would need scraping claude.ai).
- **Buddy, CC [#45596](https://github.com/anthropics/claude-code/issues/45596) (1,191):** an ASCII companion with species, rarity and personality, removed in v2.1.97 (about 2026-04-09). A second-hand report says it is "not planned to come back". Recreations: [Buddi](https://github.com/talkvalue/Buddi) (93★, macOS notch app), [claude-familiar](https://github.com/lucenity0/claude-familiar) (2★, a mod), and pixlings.
- **ACP, CC [#6686](https://github.com/anthropics/claude-code/issues/6686) (437):** bot-closed. Filled by Zed's [`@zed-industries/claude-code-acp`](https://www.npmjs.com/package/@zed-industries/claude-code-acp) adapter and others.

---

## 3. Gap clusters: demand, maintainer stance, outside fit, existing solutions

Fit scale: 5 = an outside app can deliver the full value without vendor cooperation; 1 = needs vendor changes.

| Gap | Demand evidence (👍 / votes) | Maintainer stance | Outside fit | Existing third-party (traction, price) | Verdict |
|---|---|---|---|---|---|
| **A. Agent-agnostic undo / time travel** (per-turn snapshots that include Bash edits, untracked and gitignored files, subagents; across agents) | Codex [#9203](https://github.com/openai/codex/issues/9203) 482 + [#11626](https://github.com/openai/codex/issues/11626) 228; Zed [#28676](https://github.com/zed-industries/zed/issues/28676) 16; Cursor ["Easy Roll Back"](https://forum.cursor.com/t/easy-roll-back-please-vote/73265) 17 votes; CC rewind gaps per [docs](https://code.claude.com/docs/en/checkpointing) | Codex: removed, "needs redesign" (2026-01-16); CC: partial by design | 5. Hooks exist in CC, Codex, Cursor and Gemini; add FSEvents and APFS clones for cheap whole-tree snapshots | [pi-rewind](https://github.com/arpagon/pi-rewind) 116★ (Pi only), [codex-rewind](https://github.com/extracurricular-ai/codex-rewind) 54★, [ckpt](https://github.com/mohshomis/ckpt) 7★, [sheep](https://github.com/gokay-ai/sheep) 6★, [agent-rollback](https://github.com/Nainish-Rai/agent-rollback) 6★, [quicksave](https://github.com/qorexdevs/quicksave) 4★, [bashback](https://github.com/trouties/bashback) 2★, [takeback](https://github.com/hichipli/takeback)/[turnback](https://github.com/MFaizR77/turnback)/[stepback](https://github.com/Archerkattri/stepback)/[agentckpt](https://github.com/Blackman99/agentckpt)/[preimage](https://github.com/muraa-p/preimage) 1★, [snap-back](https://github.com/Abelo9996/snap-back) 0★. Adjacent: [Mantra](https://mantra.gonewx.com) (git-anchored session replay, "core features free forever"). No paid product found. | **Open** |
| **B. Mac-native agent sandbox + secret isolation** | OrbStack [#2295](https://github.com/orbstack/orbstack/issues/2295) 233 + [#2056](https://github.com/orbstack/orbstack/issues/2056) 96; opencode [#2242](https://github.com/anomalyco/opencode/issues/2242) 79 + [#5076](https://github.com/anomalyco/opencode/issues/5076) 61; CC [#32733](https://github.com/anthropics/claude-code/issues/32733) 178 (web secrets); Cursor [env vars in MCP](https://forum.cursor.com/t/resolve-local-environment-variables-in-mcp-server-definitions/79639) 36 + [MCP secrets](https://forum.cursor.com/t/mcp-json-pass-secrets-securely/72942) 17 + [file lock](https://forum.cursor.com/t/protect-files-from-accidental-changes-with-a-lock-feature/53563) 15 votes; Zed [#40439](https://github.com/zed-industries/zed/issues/40439) 22 | OrbStack silent; opencode "need better sandboxing", no plan; CC web secrets partly shipped (Pro/Max only, per commenters) | 4. Apple Virtualization/containers or a Docker CE/OrbStack backend, plus Keychain-backed secret injection via a proxy | [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) (Docker Desktop only); [sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) (Anthropic, OSS); [sandvault](https://github.com/webcoyote/sandvault) 434★; [greywall](https://github.com/GreyhavenHQ/greywall) 309★; [clodpod](https://github.com/webcoyote/clodpod) 190★; [sandbox-shell](https://github.com/agentic-dev3o/sandbox-shell) 31★; [sidekernel](https://github.com/minoansecurity/sidekernel) 28★; [agents-sandbox](https://github.com/inoio/agents-sandbox) 23★; secret redaction ~0★ ([claude-redact-env](https://github.com/trevorstenson/claude-redact-env), [Vibesec](https://github.com/dj2313/Vibesec)) | **Open-ish** (OSS fragments; built-in agent sandboxes are weaker per users) |
| **C. PR-style review of agent diffs with feedback to the agent** (per-hunk accept/reject, comments sent back) | Codex [#2998](https://github.com/openai/codex/issues/2998) 236; CC [#33932](https://github.com/anthropics/claude-code/issues/33932) 206; Zed [#59157](https://github.com/zed-industries/zed/issues/59157) 116 (+ [disc 34759](https://github.com/zed-industries/zed/discussions/34759) 605, PR review in Zed); opencode [#8003](https://github.com/anomalyco/opencode/issues/8003) 82; Cursor [side-by-side diffs](https://forum.cursor.com/t/add-back-full-screen-compose-window-with-side-by-side-diffs/32416) 37 | Codex "iterating"; CC silent | 5 | [hunk](https://github.com/modem-dev/hunk) 9,612★; [plannotator](https://github.com/backnotprop/plannotator) 9,429★; [crit](https://github.com/tomasz-tomczyk/crit) 1,212★; [herdr-reviewr](https://github.com/persiyanov/herdr-reviewr) 889★; [diffity](https://github.com/nilbuild/diffity) 877★ (free MIT Mac app, comments go to Claude); [hunkwise](https://github.com/molon/hunkwise) 94★ | **Contested by strong free OSS** |
| **D. Cross-agent session history: search, export, resume, sync across surfaces and machines** | CC [#28791](https://github.com/anthropics/claude-code/issues/28791) 150, [#13843](https://github.com/anthropics/claude-code/issues/13843) 123, [#15542](https://github.com/anthropics/claude-code/issues/15542) 96, [#44763](https://github.com/anthropics/claude-code/issues/44763) 94; Codex [#25319](https://github.com/openai/codex/issues/25319) 109, [#4825](https://github.com/openai/codex/issues/4825) 19; opencode [#4714](https://github.com/anomalyco/opencode/issues/4714) 61; Cursor [cloud sync](https://forum.cursor.com/t/cloud-sync-for-chat-history/137456) 52, [export](https://forum.cursor.com/t/how-do-i-export-chat-with-ai/144) 33, chat search 23+22+19+12, timestamps 36+23; Zed [#58676](https://github.com/zed-industries/zed/issues/58676) 11 | CC: separate histories "by design" (docs) | 4. Local JSONL/SQLite; the Desktop index is internal | [claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer) 2,254★; [agent-sessions](https://github.com/jazzyalex/agent-sessions) 902★ (macOS, free); [monet](https://github.com/zenolab124/monet) 282★; [Mantra](https://mantra.gonewx.com) (core free, optional E2E sync); [SpecStory](https://docs.specstory.com/docs/faqs) (free; cloud reportedly $25/mo per [aisotools](https://aisotools.com/pricing/specstory), unverified) | **Contested; cross-machine sync is less served** |
| **E. Clean copy out of agent TUIs** | CC [#18170](https://github.com/anthropics/claude-code/issues/18170) 300; opencode [#4283](https://github.com/anomalyco/opencode/issues/4283) 133 + [#2755](https://github.com/anomalyco/opencode/issues/2755) 80; Codex [#48122](https://github.com/openai/codex/issues/48122) 47 + [#48125](https://github.com/openai/codex/issues/48125) 27 + [#47996](https://github.com/openai/codex/issues/47996) 21 | CC: labeled only, 9 months; others closed | 5. A clipboard filter scoped to terminal apps: strip padding and indent, rejoin hard wraps, repair URLs | No dedicated tool found (repo search returned 0). Partial: `/copy`, Ghostty `copy_to_clipboard:plain`, [AH-Merii copy-code plugin](https://github.com/AH-Merii/claude-plugins) | **Open, but small** (cheap utility; vendor fix could kill it) |
| **F. Attention routing and approvals across agents** (+ a "companion") | Codex [#3962](https://github.com/openai/codex/issues/3962) 201; Cursor 98 ([108718](https://forum.cursor.com/t/add-sound-when-a-confirmation-is-needed/108718)) + 37 + 23 + 21 + 16 + 13 votes; Ghostty [#10603](https://github.com/ghostty-org/ghostty/discussions/10603) 15; CC Buddy [#45596](https://github.com/anthropics/claude-code/issues/45596) 1,191 | Partial native hooks/sounds | 5 | [Vibe Island](https://vibeisland.app/) **$19.99 one-time** (30 agents, approvals from the notch); [Notchware](https://toolradar.com/tools/notchware) $3.99; [peon-ping](https://github.com/PeonPing/peon-ping) 5,077★; [vibe-notch](https://github.com/farouqaldori/vibe-notch) 2,524★; [Claude-Code-Remote](https://github.com/JessyTsui/Claude-Code-Remote) 1,288★; [Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) 1,077★; [code-notify](https://github.com/mylee04/code-notify) 288★; [CCNotify](https://github.com/dazuiba/CCNotify) 216★; [Buddi](https://github.com/talkvalue/Buddi) 93★ | **Saturated** (shows people pay ~$20) |
| **G. Multi-account / profile switching** | CC [#18435](https://github.com/anthropics/claude-code/issues/18435) 902, [#27302](https://github.com/anthropics/claude-code/issues/27302) 414, [#36151](https://github.com/anthropics/claude-code/issues/36151) 755 (mobile); Codex [#4432](https://github.com/openai/codex/issues/4432) 130, [#20500](https://github.com/openai/codex/issues/20500) 116; Cursor [58411](https://forum.cursor.com/t/seamless-account-switching-in-cursor/58411) 178 + [GitHub accounts](https://forum.cursor.com/t/feature-request-add-the-ability-to-switch-between-multiple-github-accounts-work-personal-within-cursor-ide-without-logging-out-and-back-in/65329) 34 votes; Cline [#869](https://github.com/cline/cline/discussions/869) 62 | Mobile shipped (commenter); Desktop flag (commenter); Cursor "low priority" | 4 | [claude-swap](https://github.com/realiti4/claude-swap) 3,458★; [aisw](https://github.com/burakdede/aisw) 129★; [modeldeck](https://github.com/timharris707/modeldeck) 116★; [claude-code-profiles](https://github.com/quinnjr/claude-code-profiles) 96★; [cux](https://github.com/inulute/cux) 84★; [mobius](https://github.com/chussum/mobius) 74★; [claude-account-switcher](https://github.com/Symbioose/claude-account-switcher) 70★; [ai-switcher](https://github.com/hoangpm96/ai-switcher) 57★; [clausona](https://github.com/larcane97/clausona) 53★; [Lanes](https://github.com/synthetixis/lanes) 12★ | **Saturated + platform risk** (and ToS risk if used to rotate limits) |
| **H. One source of truth for agent config** (AGENTS.md, rules, skills, MCP) across tools and machines | CC [#31005](https://github.com/anthropics/claude-code/issues/31005) 411, [#20697](https://github.com/anthropics/claude-code/issues/20697) 161, [#34235](https://github.com/anthropics/claude-code/issues/34235) 113, [#28729](https://github.com/anthropics/claude-code/issues/28729) 99, [#14920](https://github.com/anthropics/claude-code/issues/14920) 95; Codex [#12115](https://github.com/openai/codex/issues/12115) 121; Cursor [settings sync](https://forum.cursor.com/t/sync-of-keybindings-and-settings/31) 95, global rules 22, Claude skills 22, global AGENTS.md 14 votes; Cline [#6162](https://github.com/cline/cline/discussions/6162) 79 + [#2418](https://github.com/cline/cline/discussions/2418) 68; Zed [#5010](https://github.com/zed-industries/zed/issues/5010) 179 + [#34154](https://github.com/zed-industries/zed/issues/34154) 63 | CC partial fix v2.1.277 | 4 | [ruler](https://github.com/intellectronica/ruler) 2,945★; [ai-rules-sync](https://github.com/PanisHandsome/ai-rules-sync) 101★; Mantra (MCP gateway + skills hub) | **Contested; vendors converging on AGENTS.md** |
| **I. Usage/limit visibility + auto-resume at reset** | CC [#13354](https://github.com/anthropics/claude-code/issues/13354) 209, [#13585](https://github.com/anthropics/claude-code/issues/13585) 128, [#35744](https://github.com/anthropics/claude-code/issues/35744) 103, [#516](https://github.com/anthropics/claude-code/issues/516) 130 (bot-closed), plus limit bugs [#16157](https://github.com/anthropics/claude-code/issues/16157) 695 / [#38335](https://github.com/anthropics/claude-code/issues/38335) 476; Codex [#21073](https://github.com/openai/codex/issues/21073) 76, [#17827](https://github.com/openai/codex/issues/17827) 203; Cursor [rate meter](https://forum.cursor.com/t/request-to-add-a-rate-limit-meter-for-pro-plan/106556) 95 votes; opencode [#6152](https://github.com/anomalyco/opencode/issues/6152) 140, [#768](https://github.com/anomalyco/opencode/issues/768) 70 | Partly native (statusline `rate_limits`, Desktop resume, Mod API) | 4 | [CodexBar](https://github.com/steipete/CodexBar) 22,515★; [ccusage](https://github.com/ccusage/ccusage) 19,008★; [token-monitor](https://github.com/Javis603/token-monitor) 3,096★; [ClaudeBar](https://github.com/tddworks/ClaudeBar) 1,537★; [TokenEater](https://github.com/AThevon/TokenEater) 516★; [Usage4Claude](https://github.com/f-is-h/Usage4Claude) 410★; auto-resume: cc-session-recover, claude-limit-relay (Windows), cux | **Saturated (free)** |
| **J. Local/BYO model routing + fallback** | Warp [#4339](https://github.com/warpdotdev/warp/issues/4339) 1,233; opencode [#6231](https://github.com/anomalyco/opencode/issues/6231) 244 + [#7602](https://github.com/anomalyco/opencode/issues/7602) 120; Cline [#387](https://github.com/cline/cline/discussions/387) 212 + [#386](https://github.com/cline/cline/discussions/386) 100; Cursor [Ollama](https://forum.cursor.com/t/add-support-for-ollama-natively/27291) 131 votes; gemini [#2208](https://github.com/google-gemini/gemini-cli/issues/2208) 58, [#1679](https://github.com/google-gemini/gemini-cli/issues/1679) 54, [#5938](https://github.com/google-gemini/gemini-cli/issues/5938) 37 | Warp custom endpoints (cloud-proxied); opencode v2 partial | 3 (Warp and Cursor proxy requests through their cloud) | [claude-code-router](https://github.com/musistudio/claude-code-router) 37,685★; LiteLLM; opencode discovery plugins | **Saturated (free)** |

**High demand, but already filled or not fillable from outside**
- **LSP for agents** (Codex [#8745](https://github.com/openai/codex/issues/8745) 503): filled free by [Serena](https://github.com/oraios/serena) (30,276★), [mcp-language-server](https://github.com/isaacphi/mcp-language-server) (1,609★), and [cclsp](https://github.com/ktnyt/cclsp) (675★).
- **Mobile/remote control** (opencode [#10288](https://github.com/anomalyco/opencode/issues/10288) 97, Zed [disc 49313](https://github.com/zed-industries/zed/discussions/49313) 80, Cursor Android 44 votes): [Happy](https://github.com/slopus/happy) (24,152★), [vibetunnel](https://github.com/amantus-ai/vibetunnel) (4,688★), and official Claude Code Remote Control.
- **Parallel agents/worktrees:** [claude-squad](https://github.com/smtg-ai/claude-squad) (8,607★) and Conductor (free; Pro $50/mo per [tooldirectory.ai](https://tooldirectory.ai/tools/conductor), unverified).
- **Voice input** (Codex [#3000](https://github.com/openai/codex/issues/3000) 241, opencode [#4695](https://github.com/anomalyco/opencode/issues/4695) 176): Claude Code `/voice`; Wispr Flow (~$15/mo), Superwhisper ($8.49/mo; lifetime reported $249.99), VoiceInk (~$29 one-time), per [spokenly](https://spokenly.app/blog/wispr-flow-pricing), [toolquestor](https://toolquestor.com/vs/wispr-flow-vs-superwhisper) and [tryvoiceink](https://tryvoiceink.com/best-superwhisper-alternatives).
- **AI review bots for GitLab/Bitbucket/Azure DevOps** (Cursor 219 + 165 + 111 + 105 votes; CC [#12346](https://github.com/anthropics/claude-code/issues/12346) 143; Codex [#10665](https://github.com/openai/codex/issues/10665) 88): filled by CodeRabbit ($24/dev/mo annual, all four forges, per [aicodereview.cc](https://aicodereview.cc/blog/coderabbit-pricing)) and PR-Agent.
- **ACP for Claude Code** (CC [#6686](https://github.com/anthropics/claude-code/issues/6686) 437): filled by Zed's adapter.
- **Broadcast input to panes** (Ghostty [3227](https://github.com/ghostty-org/ghostty/discussions/3227) 410): tmux, iTerm2, and the kitty broadcast kitten. A Ghostty PR is in progress.
- **Not outside-fillable:** Claude Projects ↔ Code (421; no API), Cursor Jupyter (307), Cursor's 25 tool-call limit (297), student verification (614), model additions, INR pricing (500), XDG (441/134/101; `CLAUDE_CONFIG_DIR` workaround).

---

## 4. Ranking: top 10 gaps for a small paid product
Rule: demand × outside fit, discounted when free tools already saturate the space or the vendor is visibly shipping it.

1. **A. Agent-agnostic undo / time travel.** ≈726 👍 across Codex and Zed, plus documented holes in Claude Code's `/rewind`. Fit 5. No paid product, and the best OSS has 116★.
2. **B. Mac-native agent sandbox + secret isolation**, aimed at OrbStack/Apple-silicon buyers. OrbStack 233 + 96, opencode 79 + 61, CC web 178, Cursor 68 votes, Zed 22. Fit 4. Dedicated sandbox OSS tops out at 434★ (sandvault); the broader [open-cowork](https://github.com/OpenCoworkAI/open-cowork) desktop app (2,211★) also advertises sandbox isolation.
3. **C. Agent diff review with a feedback loop.** ≈640 👍, plus Zed 605 adjacent. Fit 5. Free incumbents are strong (hunk, plannotator, diffity), so it needs a wedge such as multi-agent support, per-hunk accept that writes back, or turn-by-turn review.
4. **D. Cross-agent session history + encrypted cross-machine sync.** ≈660 👍 plus ~220 Cursor votes. Fit 4. Free viewers exist; the sync and Desktop/CLI bridge is the open part.
5. **E. Clean copy from agent TUIs.** ≈600 👍 combined, and CC has left it 9 months. Fit 5. Small-ticket, but nobody has built it.
6. **F. Attention routing/approvals (+ companion).** ≈200 👍 + ~210 votes, plus Buddy's 1,191. Fit 5. Saturated, but Vibe Island proves a $19.99 price point.
7. **G. Multi-account switching.** The largest raw demand: ≈1,560 👍 (+178 votes). Saturated by free tools and likely to ship natively.
8. **H. Config portability.** ≈1,240 👍 + ~150 Cursor votes + ~150 Cline upvotes. Contested (ruler), and vendors are converging.
9. **I. Usage/limits + auto-resume.** Large demand, but CodexBar (22.5k★) and ccusage (19k★) are free.
10. **J. Local/BYO model routing.** Warp's 1,233 and more, but claude-code-router (37.7k★) is free, and Warp/Cursor route through their own clouds.
