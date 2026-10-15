# First product: running notes

Session started 2026-10-15. Branch `first-product`. A fresh session should read this file top to bottom, then `research/` for raw findings.

## Target

**$10,000 from strangers by 31 December 2026. First paying stranger by 25 October 2026.**

Why this number: $10k is about 150 licenses at $69, or about 1,000 paid user-months at $10. That is ambitious for a new product launched to a small audience in an 11-week window, and reachable only if a demand test shows real pull in the first week. Revisit the target once the first test ends.

## Scoreboard

| Date | Strangers who paid | Revenue | Refundable preorders | Signups (real emails, reached through complaints) | Note |
|---|---|---|---|---|---|
| 2026-10-15 | 0 | $0 | 0 | 0 | Research started |

## What needs Ethan (smallest asks first)

1. His X handle, or 5 to 10 real posts, so drafts sound like him. Searched GitHub, ethan-wickstrom.com (down to our fetchers), LinkedIn, Exa; no handle found.
2. Sizewise numbers so far: licenses sold, revenue, downloads, and which channels were tried. This calibrates the target and tells us whether his X audience buys Mac utilities.

## Facts we know (with source and whether checked)

About Ethan
- GitHub `ethan-wickstrom`: 31 repos, 554 stars, St. Louis, company "Social Fabric, LLC", site ethan-wickstrom.com (checked via WebFetch 2026-10-15).
- Site says "Founder of Tallied, Inc. Building Tally, collection management software for private art collectors" (checked via Exa crawl 2026-10-15). LinkedIn lists prior roles: co-founder/CTO at Swipr, owner/engineer at Fabric (secondhand, Exa crawl).
- Public repos read: `robofactor` (DSPy refactoring CLI with deterministic behavior checks), `tns` (Bun + Effect v4 monorepo of single-file CLIs; "a scaffolded-but-unindexed tool is unrepresentable"), `macpymessenger` (iMessage from Python), `magpie` (DSPy/GEPA preference-learning chat agent), `symphony` (OCaml 5/Eio implementation of the Symphony agent-dispatch spec, Linear + Codex app-server). README voice: terse, exact, single source of truth, illegal states unrepresentable.
- **Ethan already sells a Mac app: Sizewise** (https://getsizewise.app, checked 2026-10-15). Disk usage treemap. Free to scan; $12.99 once adds Move to Trash, Show Changes, Compare with Saved Scan; 5 Macs; every 1.x update; 14-day refunds; sold through Polar as Tallied, Inc. ("POLAR* TALLIED-INC"); Sparkle appcast at updates.getsizewise.app; Homebrew cask `ethan-wickstrom/tap/sizewise`; bundle id `me.wickstrom.Sizewise`; App Intents (Spotlight/Siri "Scan Folder", Shortcuts "Get Folder Size"); APFS-aware "what deleting frees". 1.4.0 shipped 2026-10-12 and moved from a timed trial to free scanning plus paid actions.
  - Consequence: the sales pipeline (Developer ID signing, notarization, Sparkle, Polar checkout and license keys, refund policy, Homebrew tap, landing page) already exists and is proven to work end to end. A new Mac app can reuse it on day one.
  - No Show HN and no Reddit post for Sizewise found (HN Algolia and PullPush searched 2026-10-15). Guess: it has not had a public launch push yet, which suggests distribution, not building, is Ethan's binding constraint.
  - The site copy is a clean sample of Ethan's product voice: short declaratives, second person, concrete numbers ("17.5 million items, mapped in about a minute and a half"), every claim checkable, no adjectives doing the selling.

Access from this container
- Works: HN Algolia API, iTunes review RSS, PullPush (Reddit archive), WebFetch (server side, reaches github.com), Exa search/fetch, WebSearch.
- Blocked: reddit.com direct (403), github.com and api.github.com via curl (403, session bound to its repo), nitter (JS challenge), ethan-wickstrom.com via curl (connection fails).

Market facts (checked 2026-10-15)
- "Coding agent records a polished demo video" is saturated: shot-scraper video (Simon Willison, 2026-06-30), aidemo, demowright, NextDemo, Screenify, vosso voila, demo-dev, ScreenCI, walkr, demo-machine, Screen Browser, two AutoDemos, ultrademo, Paralect skill. Most are free.
- "See what my coding agent sends to the model" is saturated with free tools: ccglass, claude-tap, claude-inspector, LoopLens, Claudoscope (free Mac menu bar app), claude-spyglass, llm-interceptor, cc-wire-analyzer, llm-proxyman, cost-xray. Proxyman also ships an MCP server.

Selling mechanics (checked 2026-10-15)
- Polar lists "Pre-orders & Paid waitlist" as a restricted business that needs closer review (https://docs.polar.sh/merchant-of-record/acceptable-use). Running a preorder test through the Tallied, Inc. Polar account that sells Sizewise could trigger a review of that account. Safer test design: sell a working early version (software that exists, with a license and the same 14-day no-questions refund Sizewise uses). That is ordinary software sales on Polar, and money for a working product is stronger proof than a deposit.

Ethan's product voice (from getsizewise.app home, press, terms and release notes; X voice still unknown)
- Opens with the reader's situation as a plain question, then the answer in two short sentences: "Disk full, and no idea why? Open any folder as a map. The bigger the file, the bigger its rectangle."
- Second person, present tense, short declaratives. No exclamation marks, no emoji, no superlatives.
- Concrete, checkable numbers: "A startup disk with 17.5 million items. Mapped in about a minute and a half."
- Names the exact UI ("Move to Trash", "Show Changes") and says what happens step by step.
- States limits and user control up front: "You confirm every move, and files go only to the Trash." "Skip it, and Sizewise maps everything else and lists the folders it skipped."
- Money is spelled out: price, tax, number of Macs, which updates, refund window, what the card statement says.

Current-pains research, X and blogs (full write-up: research/web_x.md, about 190 links)
- Model context, Oct 2026: Claude Opus 5.5 (released 2026-09-22), Fable 5.1, Sonnet 5.5; OpenAI GPT-6 Astra, GPT-6.1 Sol, GPT-6 Luna. JetBrains survey (May–Jul 2026): at work 39% use Claude Code, 21% Copilot, 16% Codex, 12% Cursor (secondhand via roobrief).
- Ranked by money signal: (1) usage limits and plan juggling, money goes to the labs, fixes are free (CodexBar, ccusage, ~10 switchers); (2) "looks AI-generated", people pay: AIDesigner went from under $1k to $9.5k MRR in 30 days (Apr–May 2026) at $25/mo, MCP into Claude Code/Cursor, built in public on X/Threads/Reddit, churn is its named risk (checked: https://www.mrrstory.com/stories/from-1k-to-95k-mrr-in-30-days-the-solo-ai-tool-fixing-ugly-vibe-coded-apps); 21st.dev (YC W26), Superdesign, Aura charge $6–80/mo; studios sell vibe-coded redesigns for $1.5k–8k; (3) many parallel agents, money goes to cloud workspaces ($20–50/mo) and hardware, Orca is free with ~92k stars; (4) review bottleneck (Ethan dislikes the category); (5) agents say "done" but nothing ran, a $99 ship/don't-ship audit exists; (6) distribution: products sold to vibe coders earn a median $213 per 30 days on TrustMRR; (7) context loss, claude-mem has ~100k stars and native Projects (2026-09-17) absorbs it; (8) secrets: fidelius, a $24 one-time Mac Keychain app sold on Polar, launched ~Oct 2026.
- Verdicts: "looks AI-generated" is current, loud, and paid for (taste that plugs into the agent loop: MCP, skill, linter; static kits are dying). The project graveyard is current but confessional; 8+ free triage tools; money sits next to it in launch help and "finish my app" services.
- Mac developers reward native one-time purchases and punish credit schemes: Raycast's non-native v2 and AI credits drove Sindre Sorhus and others to free Tinycast (2026-09-15).
- Shelf life: every agent-workflow pain drew 10+ free tools within weeks, and Anthropic/OpenAI absorb pains within months (push notifications Apr 28, /usage, agent view, AGENTS.md support Sep, Projects Sep 17). Repo Prompt went free in May.

## Working conclusion so far

Any agent-adjacent developer tool that a coding agent can build in a weekend already exists several times over as free open source (two categories checked in under an hour, 25+ tools). The first product therefore needs an advantage outside code: a channel Ethan owns, taste and polish people pay for over free tools (the TablePlus pattern), curated or growing data, or a buyer who cannot build it themselves. Treat "nobody has built this" as unlikely for any idea, and check before believing it.

## Hypotheses (confidence, 0 to 100)

| # | Hypothesis | Confidence | Evidence for | Evidence against |
|---|---|---|---|---|
| H0 | Default buyer (solo dev with agents, already earning) is the best first buyer | 50 | Pays for tools today | Can build most tools themselves; floods every niche with free OSS |
| H1 | Pro devs who buy native Mac tools on a company card are a better first buyer | 40 | Pay $89 to $99 for polish (Proxyman, TablePlus) | Saturated categories; slow to switch |
| H2 | A product for Ethan's DSPy/GEPA audience has a distribution edge competitors lack | 35 | Retweets from researchers reach AI engineers with company cards | Small market; researchers pay little |

## Ideas tried

| Idea | Status | Why |
|---|---|---|
| Agent-recorded polished demo videos ("Screen Studio for agents") | Dead | 15+ tools shipped in 2026, most free |
| Local inspector for LLM traffic from coding agents ("Proxyman for AI") | Dead | 10+ free tools; Proxyman covers it with MCP |
| Menu bar manager for dev servers and ports left by agents | Dead | 12+ entrants: WhatThePort (free, links servers to agent sessions), Strays, Portman (Ian Nuttall), Portfox + Localfox, Portsmith (paid), p0rt ($19.99 once), Port Monitor (paid), PortsKiller, PortMarshal, AI Garage, ports CLI, Vercel portless |
| Project graveyard dashboard + dev artifact cleanup (node_modules, target, DerivedData, worktrees) | Dead | Hangar (meethangar.com) does projects, servers, regenerable cleanup, unpushed-work protection, archive. Also Mole, npkill, kondo, DevCleaner |
| Agent activity monitor / firewall ("Little Snitch for agents") | Dead | 11+ entrants: Greywall, Rollcage (snapshots + one-click undo of a session + .env protection), IAXT (audit menu bar app), agentsnitch, llm-snitch, CC-Monitor, grith, Belay, Nimuvo, agentic-sentry, Cisco DefenseClaw (OSS) |
| General disk-space app | Crowded | Ethan's own Sizewise competes with DaisyDisk, GrandPerspective, Disk Inventory X, DiskFox (Show HN 2026-10-07, 4 points, hostile comments about paid disk apps: https://news.ycombinator.com/item?id=49998987) |

## Rejected by Ethan before this session (do not re-pitch without a new reason)

DST for Effect/Durable Objects; merge receipts; Stripe revenue vs token spend; agent-integration badge; design direction as agent rules. Pending with no decision: payments reconciliation explainer; EU CRA triage for maintainers; design lint for shipped UI; positioning engine; away-run review/cost screen; Stripe paid-but-no-access check; design checks for agent UI; interface stress testing; AI builder launch platform; live React trees for agents; forgotten projects holding live keys; macOS visual review browser. Parallel-agent desktop managers: crowded, few pay.
