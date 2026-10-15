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

GitHub feature-request research (full write-up: research/github_issues.md)
- Top asks with outside-product fit: agent-agnostic undo (~726 👍, now served by Rollcage); Mac-native agent sandbox with secrets out of reach (OrbStack #2295, 233 👍, no reply in 9 months); review of agent diffs with comments back to the agent (free tools hunk 9.6k★, plannotator 9.4k★); session history synced across machines (Claude Code #28791 150 👍, Codex #25319 109 👍; free viewers exist, sync is the unserved part); clean copy out of agent terminal UIs (Claude Code #18170, 300 👍, untouched 9 months); alerts (saturated, Vibe Island $19.99); multi-account (saturated); config sync (ruler 2.9k★); usage meters (CodexBar 22.5k★, ccusage 19k★); model routing (claude-code-router 37.7k★).
- Claude Code "Mods" went live 2026-10-01 (hooks with UI panes and a session usage API), which makes free in-agent add-ons even easier to build.

Platform, pricing and channel facts (full write-up: research/market.md; flags there say checked or secondhand)
- Polar: 5% + 50¢, plus 1.5% on non-US cards; license-key validate/activate endpoints need no auth and are safe in a desktop app; first payout waits up to 14 days for review (checked). Gumroad: 10% + 50¢ with native pre-orders. Lemon Squeezy is migrating users to Stripe Managed Payments (CEO post 2026-01-28). Stripe Managed Payments (Stripe as MoR, GA 2026-04-22) adds 3.5% and has no license keys. Paddle Billing has no license keys.
- Mac App Store: Small Business Program 15%; US link-outs allowed since 2026-06-08; Apple's 2026-08-13 filing proposes 5% for small-business link-outs, not ruled on. Private Cloud Compute model (32K context, free, daily limits) needs App Store distribution; direct-download apps appear ineligible.
- Foundation Models on macOS 27: read context at runtime with `SystemLanguageModel.contextSize`; Apple's docs say 4K, one session sample prints 8192; text + image input, tool calling, `@Generable`. `fm` CLI ships preinstalled (respond, chat, schema, count-tokens, `serve` as an OpenAI-compatible server, quota-usage; needs `sudo fm license` once). Python SDK `apple-fm-sdk`.
- Xcode 27 agents (plan mode, plugins with skills/MCP/ACP, `xcrun mcpbridge`) hit Swift tooling; Repo Prompt went free/OSS on 2026-06-13 after its founder joined OpenAI. Apple `container` 1.0 hits OrbStack/Docker Desktop; Spotlight clipboard/actions and menu bar customization hit Paste/Maccy, Raycast/Alfred, Bartender/Ice.
- Revenue calibration (TrustMRR, verified via payment provider, read 2026-10-15): self-listed Mac utilities mostly earn $100–$5k a month; new 2026 Mac apps usually show lifetime revenue under $10k. Top Mac row: Voicy (dictation) $17.8k last 30 days. SlapMac (novelty, $9.99 once) $57k in 7 months. ExtraDock $38.8k in 11 months. Headroom (menu bar app wrapping the open-source headroom-ai CLI; compresses Claude Code/Codex tool output for "up to 2x usage on the plan you already pay for"; $3–40/mo tiers anchored to the user's AI plan) $11.1k all-time since Mar 2026, $3.1k last 30 days, MRR $1.8k, 205 subscriptions, ~6.5k users, founder has 720 X followers. Build Mac App (boilerplate for licensing/notarization/updates/payments) $161 in its first month.
  - Lesson from Headroom: a buyer who already has a free alternative still pays when the product pays for itself in a unit they already spend (plan usage), shows the savings live, and needs no setup.
- Launch channels: Show HN posts doubled from 2025 H1 to 2026 H1 (12.4k to 26.0k) while the share reaching 100 points fell from 3.5% to 1.7% (computed from HN Algolia). r/MacApps self-promo for a non-App-Store app needs a real identity and a site with Terms and Privacy, one post per 30 days, in a Problem/Comparison/Pricing format (read on a mirror). ChatGPT referred ~10% of Vercel's new signups (secondhand).

Hacker News research (full write-up: research/hn.md; 228 Algolia queries, 54 threads read, author counts are lower bounds)
- By money signal: (1) keeping secrets away from agents, 49 authors, 30 in Aug–Oct: "I would pay more for that broker layer than for another 2x cheaper sandbox" (https://news.ycombinator.com/item?id=50071898); approval fatigue pushes people to plaintext: "tired of clicking approve on my watch 15 times for every test run" (https://news.ycombinator.com/item?id=50024528); crowded with free tools (OneCLI, varlock, secretspec, fnox, Keyhole, Infisical Agent Vault...). (2) Parallel worktrees isolate code but not the running app (ports, .env, DBs, compose, disk), 69 authors, the most frequent pain, no money signal: "absolutly eveyrone I know vibe-coded this thing". (3) Rescuing Lovable/Bolt apps, money goes to freelancers. (4) Surprise bills and hard caps, 22 authors, 20 in October after Simon Willison's post. (5) Supervising agents away from the desk: Pocketty, a $99 iPhone app, had zero purchases in its trial.
- Buying behavior: these buyers would rather build than buy. A paid tool has to be hard to vibe-code (trust, security, deep OS integration) or clearly better finished. Favoured price model: one-time license with a year of updates (TablePlus model); "$90/yr/user is somthing I'd never grab".

Paid-tool landscape (full write-up: research/landscape.md, ~280 links, [V] = verified on TrustMRR)
- Design for agent-built UIs: AI Designer $78.7k all-time, MRR $9.0k [V]; Skillry (paid agent skill library: $9.99/mo, $79/yr, $169 lifetime) MRR $2.47k two months after launch [V]; shadcnblocks 5,420 Pro customers at $149–399 once (self-reported); free design skills have enormous pull: ui-ux-pro-max 136k★, taste-skill 96.8k★, impeccable 81.3k★, anthropics/skills 181k★. Tailwind Plus closed to new buyers on 2026-09-09 when Tailwind Labs joined Shopify.
- Launch assets: Screen Studio ~25k monthly users at $108/yr; one-time clones Screen Charm $54k and ScreenSage $50k all-time [V]; App Store screenshot tools $3–7.5k [V]; App Store submissions up 84% year on year.
- Avoid: usage meters (CodexBar free, 22.5k★; SessionWatcher revenue down 41.5% in 30 days), session managers (Orca 92.8k★ free), MCP managers (MCP Router ended 2026-09-18), notifications, terminals, context builders, sandboxes, visual pointing tools (PinVari, $39.99, made $58 [V]).

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
| Undo / time travel for coding agents (APFS clones, Bash edits, untracked files) | Dead | Demand is real (Codex #9203 482 👍 "bring back /undo", #11626 228 👍; Claude Code /rewind skips Bash edits per its docs), but Rollcage (rollcage.app, checked 2026-10-15) already ships it as a polished native Mac app: APFS clone at agent start and every 15 min, one-click session undo that keeps later edits, mass-delete alarm, secrets guard via hooks, alerts, plan limits; $29 launch then $39 once, 3 Macs, 7-day trial, no refunds. Plus 20+ small free tools (pi-rewind 116★, codex-rewind 54★, revertly, uhoh, ckpt, sheep...) |
| Secrets broker for agents (Keychain vault, placeholder keys swapped at a local proxy, Touch ID grants) | Dead | HN demand is real (49 authors; "I would pay more for that broker layer"), but 12+ tools already do placeholder substitution at a local proxy: veil, Tokenhush, credential-proxy (Swift Mac app), agentauth, Phantom Secrets, proxy-shadow-keys, varlock proxy, Pathway (trypathway.ai), hoophq/cloak, mirage-proxy, keys-on-the-wire, Docker Sandboxes; plus fidelius ($24 Mac app) and Rollcage's guard |
| Agent activity monitor / firewall ("Little Snitch for agents") | Dead | 11+ entrants: Greywall, Rollcage (snapshots + one-click undo of a session + .env protection), IAXT (audit menu bar app), agentsnitch, llm-snitch, CC-Monitor, grith, Belay, Nimuvo, agentic-sentry, Cisco DefenseClaw (OSS) |
| General disk-space app | Crowded | Ethan's own Sizewise competes with DaisyDisk, GrandPerspective, Disk Inventory X, DiskFox (Show HN 2026-10-07, 4 points, hostile comments about paid disk apps: https://news.ycombinator.com/item?id=49998987) |

## Rejected by Ethan before this session (do not re-pitch without a new reason)

DST for Effect/Durable Objects; merge receipts; Stripe revenue vs token spend; agent-integration badge; design direction as agent rules. Pending with no decision: payments reconciliation explainer; EU CRA triage for maintainers; design lint for shipped UI; positioning engine; away-run review/cost screen; Stripe paid-but-no-access check; design checks for agent UI; interface stress testing; AI builder launch platform; live React trees for agents; forgotten projects holding live keys; macOS visual review browser. Parallel-agent desktop managers: crowded, few pay.
