# First product: running notes

Session started 2026-10-15. Branch `first-product`. A fresh session should read this file top to bottom, then `research/` for raw findings.

## Target

**$10,000 from strangers by 31 December 2026. First paying stranger by 25 October 2026.**

Why this number: $10k is about 150 licenses at $69, or about 1,000 paid user-months at $10. That is ambitious for a new product launched to a small audience in an 11-week window, and reachable only if a demand test shows real pull in the first week. Revisit the target once the first test ends.

## Scoreboard

| Date | Strangers who paid | Revenue | Refundable preorders | Signups (real emails, reached through complaints) | Note |
|---|---|---|---|---|---|
| 2026-10-15 | 0 | $0 | 0 | 0 | Research done; pitch sent (Sizewise developer launch, runner-up design pass); Show HN and r/MacApps drafts written |
| 2026-10-15, later | 0 | $0 | 0 | 0 | Outreach list re-checked: most threads already solved; 8 replies and an r/MacOS modmail drafted (launch/outreach-replies.md); nothing posted |

## What needs Ethan (smallest asks first)

1. His X handle, or 5 to 10 real posts, so drafts sound like him. Searched GitHub, ethan-wickstrom.com (down to our fetchers), LinkedIn, Exa; no handle found.
2. Sizewise numbers so far: licenses sold, revenue, downloads, and which channels were tried. This calibrates the target and tells us whether his X audience buys Mac utilities.
3. One sentence on why he built Sizewise, in his words, for the Show HN and r/MacApps posts (no invented backstory).
4. A yes to post the Show HN and r/MacApps drafts this week (first post by 2026-10-20). Is HN user `ethan-wickstrom` yours (created 2025-10-25, karma 1, nothing posted)? Which Reddit account will you post from?
5. Today: post the reply to u/BrownCowStunning_ (launch/outreach-replies.md, section 2) if you want it to help; the thread is a day old and the poster is still replying.
6. By 2026-10-17: send the r/MacOS modmail (section 1) asking to post the /macos page once, then the r/codex replies to u/Calrose_rice and u/andysurtees.

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

- **getsizewise.app/macos** (checked 2026-10-15 by rendering it): an interactive map of every file macOS 27.0.1 puts on a Mac and what changed since 26.5.1 ("macOS 27.0.1 is 4.37 GB bigger"; a new 7.3 GB Rosetta cryptex; 3.09 GB of Intel copies plus 4.14 GB of Rosetta translations against 2.49 GB native). No HN or Reddit post found. It is the strongest first post Ethan has: a finding, not an ad. Also on the site: /try (in-browser demo with a sample home folder), sourced guides for Xcode, Docker, developer caches, System Data, purgeable space, Apple Intelligence storage; Cloudflare Web Analytics; no llms.txt. Sizewise 1.1+ can let Claude or another assistant read saved scans (Settings > Let AI assistants read scan results).

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

Reddit research (full write-up: research/reddit.md; ~390k post titles and bodies via the Arctic Shift archive API, fresh to 2026-10-15; PullPush now refuses agents with HTTP 429)
- Money signals by strength: usage limits (~2,140 authors, money goes to the vendors); AI-built apps not production-ready (~1,040 authors, money goes to human services and audits); finding first users (~2,430, crowded); dictation (~570, crowded); **Mac storage eaten by developer and agent files (129 posts Aug–Oct): DaisyDisk (~$10, "worth every cent") and DiskFox ($9.99) sell, Mole (free) is the most recommended** (https://www.reddit.com/r/MacOS/comments/1x3hej6/ , https://www.reddit.com/r/macapps/comments/1wz36bh/).
- Design for agent-built UI: lots of demand, but no Aug–Oct comment from anyone who paid for a tool; people use free skills (Impeccable, unslop, Taste Skill), Claude Design, Figma MCP, or another model subscription. Counter-evidence to the runner-up, weighed against AI Designer's verified $9.0k MRR.
- Agents deleting data: the most viral pain ("deleted 48k files", score 4,842) has the weakest buyers.
- Mac buyers prefer one-time purchases and accept a lifetime price of about one to two years of subscription. Proxyman, TablePlus and Fork are named as tools developers happily pay for.

Outreach re-check (2026-10-15, threads re-read through Arctic Shift, HN Algolia and WebFetch; details in launch/outreach-replies.md)
- Most of the 39 people on research/outreach.md had an answer within hours of posting. u/cecoondog bought DaisyDisk ($9.99) four and a half hours after posting, on commenters' advice, and wrote "Best $10 purchase I've ever made"; Mole and OnyX were "too techie" (https://www.reddit.com/r/MacOS/comments/1x3hej6/). Others were fixed by Mole, by deleting Time Machine snapshots, by a restart, or by a macOS update.
- Developers ask their agent instead of buying: "I just asked Claude where all my disk space went and it gave me a really useful breakdown" (https://news.ycombinator.com/item?id=50064993); in r/codex's "Codex disk usage" thread the most upvoted comment asks "Can Codex prune this back?", answered "It can. It's pretty good at it too" (https://www.reddit.com/r/codex/comments/1x1ytxw/). All five HN leads were answered with free commands.
- Promotion rules (Arctic Shift rules endpoint): r/mac bans self-promotion and removed a disk-app maker's answer on u/funky_surprise's thread after a user called it AI-written promotion of "garbage software"; r/macbookpro and r/macbookair ban promotion; r/MacOS requires a modmail before promoting anything you made. Other makers already reply in these threads (neodisk.app, SpaceWise, FinderTools, Diskaroo, Mole's author).
- An Apple Community user tip (neuroanatomist, 2026-10-03) says macOS 27 no longer reports purgeable space and counts it in System Data, which explains much of the reported System Data growth (https://discussions.apple.com/docs/DOC-250012471). Sizewise's purgeable-space guide describes the macOS 26 behavior; worth a macOS 27 note, and worth checking what Not in this map shows on 27 (unchecked).
- HN user `ethan-wickstrom` exists: created 2025-10-25, karma 1, nothing posted. Matches the GitHub handle; unconfirmed that it's Ethan's.
- Arctic Shift serves subreddit rules at /api/subreddits/rules?subreddits=NAME. reddit.com stays blocked for WebFetch and Exa.

## Working conclusion (2026-10-15, after six research tracks and 21 category checks)

1. No open lane exists for a new developer utility. Every category checked (21, listed under "Ideas tried") already had 10 or more tools, mostly free, most built within weeks of the pain appearing. Anthropic and OpenAI absorb what remains within months. The default buyer (solo dev with agents) builds instead of buying: "absolutly eveyrone I know vibe-coded this thing" (https://news.ycombinator.com/item?id=47975381). That buyer is also the competitor.
2. Money still reaches small makers in crowded categories when the product is polished, shows measurable value, and reaches buyers: Rollcage ($29 to $39 once), Headroom ($1.8k MRR on top of a free CLI), AI Designer ($9.0k MRR), Skillry ($2.5k MRR), Screen Studio clones ($50k+ all-time).
3. Distribution is the binding constraint, for indie Mac developers generally and for Ethan specifically: Sizewise is finished, priced, and sold through Polar, and has had no public launch on HN or Reddit (checked 2026-10-15).
4. Therefore the decision rule is speed to a paying stranger, and the product that wins it is the one already built.

## Decision

Strongest direction: **launch Sizewise to Mac developers whose disks keep filling up** (Xcode, Docker, package caches, agent worktrees, model weights), with Show Changes ("where did the space go since last week?") as the reason to pay. Fastest possible path to a paying stranger: the product is live, free to scan, $12.99 once, with Terms, Privacy, refunds and developer guides already written.

Runner-up (ready if the test fails, or if Ethan wants a new product first): **a design pass for agent-built web apps.** One command captures every route of a running app, renders a few complete design directions on the user's own screens, applies the chosen one through the user's coding agent as tokens and component changes, then checks every route for drift. Money in the category is verified (AI Designer $9.0k MRR, Skillry $2.5k MRR, studios at $1.5k to $8k). Crowded (Mowgli, Remarked, Fragments, Foundry, Kagome, Tell, free skills with 80k to 136k stars); its moat is Ethan's taste, which needs his time.

## Test 1: Sizewise developer launch

- Pass: **10 paid licenses from strangers within 7 days of the first public post.** Strangers means not friends, not existing followers who know Ethan personally. Source of truth: Polar orders (Ethan reports the count).
- Deadline: first post by 2026-10-20; read the result 7 days after the first post.
- Kill or pivot rule: under 3 paid licenses in 7 days means the channel or the category is wrong for a quick win; run the runner-up. Between 3 and 9 means keep Sizewise as a slow SEO business and run the runner-up anyway.
- Assets, all drafts, none posted or published (2026-10-15): Show HN for /macos (launch/hn-macos-page.md) and for Sizewise (launch/show-hn.md); r/MacApps post in Problem/Comparison/Pricing format (launch/r-macapps.md; Tier 2 rules: real identity, LinkedIn, contact details, site with Privacy and Terms; no em dashes; one post per 30 days); sourced guide "What coding agents and dev tools leave on your Mac" for getsizewise.app/agent-disk (launch/agent-disk/, rendered locally); the developer-week demo page (launch/dev-week/); llms.txt (launch/llms.txt); outreach list (research/outreach.md) and the replies still worth posting, plus an r/MacOS modmail (launch/outreach-replies.md); X outlines only (launch/x-outlines.md), waiting on Ethan's posts to learn his voice.
- Every claim in every draft must be true of Sizewise 1.4 as shipped. No invented backstory: Ethan fills in why he built it.

## Test 2 (runner-up, ready to run): design pass for agent-built web apps

- Buyer: a solo developer who sells a SaaS or landing page built with coding agents and says it "looks AI-generated".
- Offer to test: a working early version sold through Polar as software (not a preorder; Polar restricts preorders), $49 once per project with a 14-day refund, or a $15/month plan. Pick one before launch: one-time first, because Mac and indie buyers prefer it (Reddit research) and it avoids AI Designer's churn problem.
- Demo the test needs: before/after of three real open-source agent-built apps, every route, rendered in Chromium here, plus one 30-second clip of the pick-a-direction step.
- Pass: 10 paid early-access licenses from strangers within 7 days of launch. Signals that don't count: likes, stars, waitlist emails.
- Known risks to check first: Reddit shows demand but nobody saying they paid for a tool; free skills (Impeccable, Taste Skill, ui-ux-pro-max) and Claude Design set a free floor; Ethan's taste is the moat and needs his time.

## Hypotheses (confidence, 0 to 100)

| # | Hypothesis | Confidence (2026-10-15, after research) | Evidence for | Evidence against |
|---|---|---|---|---|
| H0 | Default buyer (solo dev with agents, already earning) is the best first buyer for a utility | 25 (was 50) | Pays for plans and a few tools (Headroom, Rollcage, AI Designer) | Builds instead of buys; 21 of 21 categories already saturated; "I'd pay" statements aim at the model vendors |
| H1 | Pro devs who buy native Mac tools on a company card are a better buyer | 40 | Proxyman, TablePlus, Fork named as happily paid for | Mature categories; slow to switch |
| H2 | A product for the DSPy/GEPA audience has a distribution edge | 25 (was 35) | That audience amplifies research results | GEPA skill optimizers and FM eval tools already exist, Apple ships Evaluations |
| H3 | Distribution, not product, is Ethan's binding constraint | 75 | Sizewise and /macos are polished and unlaunched; indie Mac devs say the same in 2026 interviews | Sizewise sales so far unknown |
| H4 | Sizewise's first launch to developers yields 10 paid licenses from strangers within 7 days | 25 (was 35; outreach re-check) | Storage pain is frequent and already sells at about $10 (DaisyDisk, DiskFox); free scan lowers friction; /macos is a strong HN post | Mole (70k★, free) is the default recommendation; HN hostile to paid disk apps; $12.99 ceiling; developers now ask Claude or Codex to find and clear space; every HN lead was answered with free commands |
| H5 | A new developer utility can't win on code alone in Oct 2026 | 85 | 10+ tools per pain within weeks; vendors absorb pains within months | Polished paid entrants still sell in crowded categories |
| H6 | Mac users who aren't developers pay about $10, within hours, for the disk app other people recommend when their disk fills | 70 | u/cecoondog bought DaisyDisk 4.5 hours after posting and another commenter downloaded it; Mole and OnyX "too techie" for them | One thread; many threads end with no purchase (snapshots, restart, update, Mole) |
| H7 | Sizewise can reach those buyers inside the 7-day test | 20 | /macos fits r/MacOS, where System Data posts cluster, if moderators allow it; Sizewise has a System Data guide for search | Promotion banned in r/mac, r/macbookpro, r/macbookair; r/MacOS needs moderator approval; threads resolve within hours, usually by a recommendation of DaisyDisk or Mole |

## Ideas tried

| Idea | Status | Why |
|---|---|---|
| Agent-recorded polished demo videos ("Screen Studio for agents") | Dead | 15+ tools shipped in 2026, most free |
| Local inspector for LLM traffic from coding agents ("Proxyman for AI") | Dead | 10+ free tools; Proxyman covers it with MCP |
| Menu bar manager for dev servers and ports left by agents | Dead | 12+ entrants: WhatThePort (free, links servers to agent sessions), Strays, Portman (Ian Nuttall), Portfox + Localfox, Portsmith (paid), p0rt ($19.99 once), Port Monitor (paid), PortsKiller, PortMarshal, AI Garage, ports CLI, Vercel portless |
| Project graveyard dashboard + dev artifact cleanup (node_modules, target, DerivedData, worktrees) | Dead | Hangar (meethangar.com) does projects, servers, regenerable cleanup, unpushed-work protection, archive. Also Mole, npkill, kondo, DevCleaner |
| Undo / time travel for coding agents (APFS clones, Bash edits, untracked files) | Dead | Demand is real (Codex #9203 482 👍 "bring back /undo", #11626 228 👍; Claude Code /rewind skips Bash edits per its docs), but Rollcage (rollcage.app, checked 2026-10-15) already ships it as a polished native Mac app: APFS clone at agent start and every 15 min, one-click session undo that keeps later edits, mass-delete alarm, secrets guard via hooks, alerts, plan limits; $29 launch then $39 once, 3 Macs, 7-day trial, no refunds. Plus 20+ small free tools (pi-rewind 116★, codex-rewind 54★, revertly, uhoh, ckpt, sheep...) |
| Secrets broker for agents (Keychain vault, placeholder keys swapped at a local proxy, Touch ID grants) | Dead | HN demand is real (49 authors; "I would pay more for that broker layer"), but 12+ tools already do placeholder substitution at a local proxy: veil, Tokenhush, credential-proxy (Swift Mac app), agentauth, Phantom Secrets, proxy-shadow-keys, varlock proxy, Pathway (trypathway.ai), hoophq/cloak, mirage-proxy, keys-on-the-wire, Docker Sandboxes; plus fidelius ($24 Mac app) and Rollcage's guard |
| Design references and personal taste libraries wired to agents (MCP) | Dead | Mobbin MCP (paid plans), uistash (Mac app: saved references rebuilt as coded "Styles" served over local MCP, uses your own agent CLIs), PocketUI (personal library + MCP), curated.design MCP (sections + design.md per site), Screenrove MCP (has `check_my_ui`), swaggin, designLib-mcp, design-scope-mcp, lookbook, screenshots-design-inspiration MCP |
| Hard budget caps / kill switch across cloud and AI APIs | Dead | Spiked after Simon Willison's 2026-10-04 post (652 points), but Kill Switch (OSS + managed, 15 providers, plus an agent guard), reGuard, subKey, Recovea, Spendmux, noburn, Tessera, Caveman Cloud, Hadrian, budget-guard, LiteLLM budgets already exist |
| App Store screenshots and previews driven by an agent | Dead | Matte (MCP), Stoot (native, agent-driven), Screenpane (MCP), Screenshot Bro (MCP), Screenshot Studio (MCP), Shipshots, Stora, storescreens CLI, goldie, app-store-screenshots skill, app-preview-craft skill |
| GEPA/DSPy optimization of agent skills and CLAUDE.md from session logs | Dead | gskill (official GEPA), cc-skill-optimizer, two skill-evolution plugins, cabrero, retrospective-skill, skill-optimizer, SuperQode |
| Parallel design variants of your running app in worktrees | Dead | styles-iterator, variant-ui (MCP), okiro, iterate skill, parallel-build skill, Parallel Code, Daintree, VibeTree |
| Redesign an existing vibe-coded app end to end | Crowded | Mowgli (redesign canvas + agent sync), Remarked (productized: 3 screens in 7 days), Kagome, Foundry, Fragments (Mac app, design-system drift checks), Alloy, GlowUp UI, Tell (OSS, 14 genericness detectors), studios at $1.5k–8k |
| Per-worktree databases, ports and env via APFS clones | Dead | Pomelo (native Mac app: per-branch services, DBs, ports, URLs, MCP), pgbranch, wtdb, agent-slots, cow, simgit, coworktree, claude-cow-worktree, exp, Clonopy, Sandbase (pre-launch) |
| Evals and prompt optimization for Apple Foundation Models | Dead | Apple shipped the Evaluations framework in the 27 releases (WWDC26 session 335); plus prompt-better (DSPy bridge), fmtools, FoundationModelsBench, FoundationModelsKit |
| Dev-artifact disk cleanup as a new app | Dead | Mole (70k★ free CLI + paid native app, includes `mo purge` for build artifacts), Hangar, Rollcage's storage cleaner, npkill, kondo |
| Agent activity monitor / firewall ("Little Snitch for agents") | Dead | 11+ entrants: Greywall, Rollcage (snapshots + one-click undo of a session + .env protection), IAXT (audit menu bar app), agentsnitch, llm-snitch, CC-Monitor, grith, Belay, Nimuvo, agentic-sentry, Cisco DefenseClaw (OSS) |
| General disk-space app | Crowded | Ethan's own Sizewise competes with DaisyDisk, GrandPerspective, Disk Inventory X, DiskFox (Show HN 2026-10-07, 4 points, hostile comments about paid disk apps: https://news.ycombinator.com/item?id=49998987) |

## Rejected by Ethan before this session (do not re-pitch without a new reason)

DST for Effect/Durable Objects; merge receipts; Stripe revenue vs token spend; agent-integration badge; design direction as agent rules. Pending with no decision: payments reconciliation explainer; EU CRA triage for maintainers; design lint for shipped UI; positioning engine; away-run review/cost screen; Stripe paid-but-no-access check; design checks for agent UI; interface stress testing; AI builder launch platform; live React trees for agents; forgotten projects holding live keys; macOS visual review browser. Parallel-agent desktop managers: crowded, few pay.
