# Hacker News pain research: solo developers who build with coding agents

Window: 2026-04-15 to 2026-10-15, with Aug to Oct 2026 weighted most. Source: Hacker News comments and stories through the Algolia API. Compiled 2026-10-15.

## TL;DR: ranked clusters

"Authors" is the number of distinct HN users in my curated evidence list for that cluster. It is a lower bound: I did not read every hit. "Aug–Oct" is how many of those items are dated Aug to Oct 2026. Full linked lists are in the appendix.

| # | Pain cluster | Authors | Aug–Oct | Money signal | Verdict |
|---|---|---|---|---|---|
| 1 | **B. Keeping secrets away from coding agents** (credential brokering, approval fatigue) | 49 | 30 of 50 | Explicit and recent: "I would pay more for that broker layer than for another 2x cheaper sandbox" ([ekorondy, Oct 13](https://news.ycombinator.com/item?id=50071898)). People already pay 1Password ([_august](https://news.ycombinator.com/item?id=49317843)) and Infisical ([vekker](https://news.ycombinator.com/item?id=49174788)). | Real pain with a money signal. Crowded with free OSS. |
| 2 | **A. Parallel worktrees isolate the code but not the running app** (ports, .env, DBs, compose, caches, disk, dev-server lifecycle) | 69 | 21 of 70 | No "I'd pay" quotes. Very heavy DIY: a 15K-line in-house Rust tool used "100 times a day" ([aroman](https://news.ycombinator.com/item?id=48853408)). Adjacent paid tools are praised (OrbStack, [rswail](https://news.ycombinator.com/item?id=48472575)). A $50/month port tool was mocked ([snowe2010](https://news.ycombinator.com/item?id=49064942)). | Most frequent pain. Willingness to pay is unproven. |
| 3 | **C. Rescuing AI-built apps** (Supabase RLS, auth, Stripe webhooks, deploys) | 18 | 7 of 18 | Money already changes hands: freelancers sell fixed-price fixes and audits ([Andler](https://news.ycombinator.com/item?id=50050342), [kieranlenton54](https://news.ycombinator.com/item?id=48388928)). | Real pain with money, but the buyer is the not-yet-earning builder, and it overlaps ideas already considered. |
| 4 | **E. Surprise bills and the demand for hard budget caps** | 22 | 20 of 22 | "I would pay for Cloudflare Workers Paid ($5) in a heartbeat", blocked only by unlimited-bill risk ([woodylondon](https://news.ycombinator.com/item?id=47795924)). People cap with virtual cards. | Real pain, spiking in Oct 2026. Overlaps "cost screens". |
| 5 | **D. Supervising agents away from the desk** (needs-input alerts, approving from a phone, persistent sessions, keep-awake) | 36 | 22 of 38 | **Negative.** A $99 iPhone app for this had zero purchases during its trial window ([maker, Oct 9](https://news.ycombinator.com/item?id=50016283)). Free OSS and first-party remote control exist. | Real pain, weak money. |
| 6 | **F. Usage-limit anxiety and juggling accounts** | 23 | 11 of 23 | Weak. Free trackers exist, and using multiple accounts to dodge limits breaks the terms of service ([adastra22](https://news.ycombinator.com/item?id=49416557)). | Interesting. Overlaps cost screens. |
| 7 | **G. Every session starts from zero** (searchable transcripts, memory across sessions) | 22 | 12 of 22 | Weak. Mostly builders giving away free tools. | Interesting. |
| 8 | **H. Keeping CLAUDE.md, AGENTS.md, skills, MCP and hooks in sync across harnesses and machines** | 27 | 20 of 27 | Weak. Partly solved once Claude Code began reading AGENTS.md ([Sept 18](https://news.ycombinator.com/item?id=49760187)). | Interesting. |

Interesting complaints with little sign of money (section 4): I. screenshots into terminal agents, J. verifying agent output, K. Claude Code copy/paste papercuts, L. sandboxing and approval fatigue (36+ projects), M. Mac signing and notarization, N. freelancer invoicing churn, O. "Claudespeak".

## 1. Method

- **Queries:** 228 Algolia queries, all filtered to `created_at_i > 1776211200` with typo tolerance off. They are listed in the query log at the end. They included every phrase from the brief: "I'd pay for", "I would pay for", "would happily pay", "shut up and take my money", "is there a mac app", "is there a tool", "is there an app", "does anyone know a tool", "looking for a tool", "I wrote a script", "I built a script", "I hacked together", "my workaround", "wish there was", "I wish Claude Code", "I wish Codex", plus `"Claude Code" annoying`, `"coding agents" pain`, worktrees, `"parallel agents"`, `agent secrets`, `agent .env`, `"dev server" ports`, `"usage limits"`, `"context window" CLAUDE.md`, `MCP config`, `"vibe coded" looks`, `"side projects" abandoned`/graveyard, `"AI slop" design`/UI, and Show HN Mac app stories. Follow-up queries came from the threads I opened (ports, `.localhost`, zombie dev servers, image paste over SSH, hard caps, Lovable/Supabase, Harvest, OrbStack, TablePlus and others).
- **Deep reads:** 54 full threads fetched through `/api/v1/items/`, for example "Ask HN: What are tools you have made for yourself since the advent of AI?" (779 comments), "I Got Sick of Remembering Port Numbers", Pocketty, Agent37, Agent Vault, OneCLI, "Where .env Went Wrong", "We're going to need default hard budget caps…", "Distributing Mac software…", "$500/month side projects", "Show your micro-SaaS", and the Harvest price hike.
- **Corpus:** 23,713 distinct in-window comments and stories, cached raw under `research/hn_raw/`. A cluster's evidence is a hand-curated list of comment IDs, and counts are distinct authors in that list.
- **Caveats:** HN skews toward people who build their own tools, which itself turned out to be a finding. Some exact phrases returned zero hits (`"is there a mac app"`, `"does anyone know a tool"`), so the variant phrasings carried the load. Anything marked **(guess)** is my inference and was not stated on HN.

---

## 2. Real pain with a money signal

### #1. B. Keeping secrets away from coding agents (49 authors, 30 of 50 items in Aug–Oct)

**In plain words:** agents need API keys to run builds, tests and deploys. Developers do not want those keys in `.env` files, in the model's context, in transcripts or in logs. The "secure" setups, such as 1Password approval prompts, are so interruptive during long agent runs that people fall back to plaintext.

Quotes:
- "I would pay more for that broker layer than for another 2x cheaper sandbox." ([ekorondy, 2026-10-13](https://news.ycombinator.com/item?id=50071898))
- "sandbox protects the host. it does not protect your tokens. scoped, short lived credentials per task. that i would pay more for." ([talkarimli, 2026-10-12](https://news.ycombinator.com/item?id=50063391))
- “I refuse to admit to the number of times where I've told the agent "Please write the 1Password creds to .env and use .env instead because I'm tired of clicking approve on my watch 15 times for every test run."” ([ShakataGaNai, 2026-10-09](https://news.ycombinator.com/item?id=50024528))
- "especially frustrating when I leave an agent running for a long time and it gets stuck on my build scripts because it's waiting for my approval." ([alex0ptr, 2026-10-09](https://news.ycombinator.com/item?id=50020505))
- "every week I encounter something that doesn't work or work well. I've reached the point where I want to consider using something, that someone smarter than me came up with." ([pietz, 2026-07-01](https://news.ycombinator.com/item?id=48745111))
- “had an API key leak because an agent decided to "helpfully" paste it into a log output. Didn't notice until the bill came.” ([HyperAI, 2026-08-31](https://news.ycombinator.com/item?id=49508497))

**Workarounds people use today:**
- Hand-written API proxies that add the secret on the way out ([onion2k](https://news.ycombinator.com/item?id=48744549), [simonw](https://news.ycombinator.com/item?id=49786809)).
- A hook that redacts secrets from transcripts ([spellboots](https://news.ycombinator.com/item?id=49914606)).
- `sops exec-env` ([thehamkercat](https://news.ycombinator.com/item?id=49757541)).
- An extension that blocks `.env` reads inside a Lima VM ([magimas](https://news.ycombinator.com/item?id=48919564)).
- Caching daemons such as "once" and fnox ([Once thread](https://news.ycombinator.com/item?id=50018239)).
- Capping the damage instead: "disable auto-reloading. Now if it blows up, I'm down $5" ([andai](https://news.ycombinator.com/item?id=49952333)).

**What people pay for or use:**
- 1Password Environments together with `op` ([_august](https://news.ycombinator.com/item?id=49317843)). One user refuses because "If 1Password hadn't jumped the subscription model shark, I'd be all over that" ([jpitz](https://news.ycombinator.com/item?id=49172297)).
- Infisical: [vekker](https://news.ycombinator.com/item?id=49174788), and its Agent Vault proxy ([Show HN](https://news.ycombinator.com/item?id=47865822)).
- Docker Sandboxes, chosen for "secret injection with placeholders" despite an annoying login ([rusch](https://news.ycombinator.com/item?id=49240545), [Humphrey](https://news.ycombinator.com/item?id=49251284)).

**Incumbents and crowding:** the space is crowded:
- OneCLI ([Show HN](https://news.ycombinator.com/item?id=49023427)), varlock ([theozero](https://news.ycombinator.com/item?id=49025087)), secretspec ([domenkozar](https://news.ycombinator.com/item?id=49125350)), fnox ([kstrauser](https://news.ycombinator.com/item?id=49125562)), Keyhole ([maferland](https://news.ycombinator.com/item?id=48809077)), secret-shuttle ([pdumicz](https://news.ycombinator.com/item?id=48749273)), vne ([pro-vi](https://news.ycombinator.com/item?id=50066458)), llmvlt ([moronim](https://news.ycombinator.com/item?id=48462925)), Stashbase ([radim_h](https://news.ycombinator.com/item?id=50100776)).
- AWS Strands Box ([vscarpenter](https://news.ycombinator.com/item?id=50072925)).
- One commenter: "everyone got the same idea again and there’s a bunch of implementations people are desperate to promote" ([adithyassekhar](https://news.ycombinator.com/item?id=49025146)).

**Mac-specific gap:** the macOS sandbox used by Agent Safehouse cannot filter network access by domain. “MacOS sandboxing does not allow that type of blocking. Only broad categories like "local" vs "remote"” ([e1g, the Safehouse author](https://news.ycombinator.com/item?id=48764305); [atombender](https://news.ycombinator.com/item?id=48737694)).

**Product angle (guess):** a Mac-native broker for local agents. It would:
- Store keys in the Keychain or Secure Enclave.
- Grant access per agent session with Touch ID, scoped to a repo or command and auto-expiring. This is approve once, not 15 times per test run.
- Inject values into the process without writing them to disk.
- Proxy egress per host.
- Redact secrets from Claude Code and Codex transcripts, and keep an audit log.

The pitch is "1Password-grade without the subscription and without the approval storm". The risks are trust (a small vendor holding secrets), many free CLIs, and 1Password shipping the same feature.

### #2. A. Parallel worktrees isolate the code, not the running app (69 authors, 21 of 70 items in Aug–Oct)

**In plain words:** running several agents on one repo through git worktrees works for files. But every worktree also needs its own ports, `.env`, database, docker compose project, `node_modules` or build cache, and a reachable URL. Agents also leave dev servers running or start duplicates. The disk and RAM cost multiplies with each worktree.

Quotes:
- "If git worktrees solve the problem of code isolation, bud solves the problem of isolating everything else. It's about 15K lines of rust, and I use it 100 times a day or so." ([aroman, 2026-07-09](https://news.ycombinator.com/item?id=48853408))
- "Files stayed separate; ports, databases, cache keys, queues, and Compose resources did not." ([grepsedawk, 2026-07-28](https://news.ycombinator.com/item?id=49086018))
- "still leaves you reinstalling node_modules per tree and fighting over a dev server port. That's the actual cost, and none of these tools touch it. So I gave up on parallelizing inside one repo." ([zjy71055, 2026-06-01](https://news.ycombinator.com/item?id=48355104))
- "with worktrees I am not really able to easily copy secrets, etc to run my app, ports conflict, I end up with a bunch of separate dbs and services" ([Atotalnoob, 2026-04-23](https://news.ycombinator.com/item?id=47871666))
- "AI agents suck at the process lifecycle management: leaving processes alive, starting the same daemon multiple times… The interesting part to me isn't the port numbers, it's the automatic service start/stop" ([CGamesPlay, 2026-05-01](https://news.ycombinator.com/item?id=47971271))
- "my Mac is using insane amount of RAM and SSD space (bcs of all the worktrees)" ([cahaya, 2026-08-26](https://news.ycombinator.com/item?id=49446476)). See also "200+ GB codex-rs target folder. Forget about doing worktrees." ([yearolinuxdsktp, 2026-10-01](https://news.ycombinator.com/item?id=49927304)).

**Workarounds people use today:**
- Shell scripts that pick free ports, write them into `.env` and release them on teardown ([laurels-marts](https://news.ycombinator.com/item?id=48246985)).
- A Claude hook that copies `node_modules` and `.env` and sets a compose project name per worktree ([francislavoie](https://news.ycombinator.com/item?id=49111504)).
- A Postgres database per worktree ([christophilus](https://news.ycombinator.com/item?id=49786309)).
- Docker containers for each session ([jacobgold, Clor](https://news.ycombinator.com/item?id=49703810)).
- runnem, which "helps the AI get at the logs of the running processes" ([dsmurrell](https://news.ycombinator.com/item?id=48457988)).

**Incumbents:**
- Conductor and Superset setup and teardown scripts. One user still hit "port conflicts with docker projects" ([shmoogy](https://news.ycombinator.com/item?id=47874122); [saddlepaddle](https://news.ycombinator.com/item?id=48238725)).
- Vercel's portless ([vlucas](https://news.ycombinator.com/item?id=47975002), [chrisvenum](https://news.ycombinator.com/item?id=48244872)), localias ([swiftcoder](https://news.ycombinator.com/item?id=47972030)), outport ([pyreal](https://news.ycombinator.com/item?id=47971151)), termic ([SimionBaws](https://news.ycombinator.com/item?id=49430363)), autowt ([irskep](https://news.ycombinator.com/item?id=49414315)), and OrbStack ([gempir](https://news.ycombinator.com/item?id=48472352) notes its file-watcher limits).
- On ports specifically: "absolutly eveyrone I know vibe-coded this thing" ([OriPekelman](https://news.ycombinator.com/item?id=47975381)).

**Willingness to pay:** I found no explicit "I'd pay" statement. There are two counter-signals:
- PortZero charges $50/month for cloud tunnels and drew ridicule: "Wild to vibe code something in a week then charge $50/month" ([snowe2010](https://news.ycombinator.com/item?id=49064942)).
- One scripter says scripts were "trivial", so "i havent tried any of the GUI apps yet" ([laurels-marts](https://news.ycombinator.com/item?id=48246985)).

Adjacent evidence that Mac developers pay for dev-environment polish: OrbStack is "worth it for the time saved" ([rswail](https://news.ycombinator.com/item?id=48472575)). Others find "$96/yr" hard to justify ([mpeg](https://news.ycombinator.com/item?id=48471003)).

**Product angle (guess):** a per-worktree environment manager that sits under any agent app rather than competing with them. It would provide:
- A stable `name.localhost` URL with TLS for each worktree.
- `.env` templating.
- A database cloned per worktree.
- Compose namespacing.
- Shared build caches and cleanup of disk space.
- A process supervisor that kills zombie servers and exposes logs to the agent.

### #3. C. Rescuing AI-built apps (18 authors, 7 of 18 items in Aug–Oct). This is evidence on ideas already considered.

**In plain words:** people who built with Lovable, Bolt, v0, Replit or Cursor get users, then hit open Supabase tables, auth gaps, Stripe webhooks that fail or double-fire, and failed deploys. Today they pay humans to fix it.

Quotes:
- "I fix AI-built apps on Supabase and Stripe: RLS and auth gaps, webhooks that fail or double-fire… First audit is free and scoped" ([Andler, 2026-10-12](https://news.ycombinator.com/item?id=50050342))
- "I finish and fix apps that were started in Lovable, Bolt, Cursor or Claude Code" (fixed price, paid in milestones) ([FlowLabDev, 2026-10-01](https://news.ycombinator.com/item?id=49926217))
- "one friend wasn't sure whether his RLS policies were actually working correctly. Another didn't really know which Supabase tables were accessible publicly." ([tornadorice, 2026-08-27](https://news.ycombinator.com/item?id=49468226))
- "their database was completely open with no RLS" ([kay_o, 2026-04-19](https://news.ycombinator.com/item?id=47828077))
- "I have more work than ever fixing the security issues on vibe coded apps" ([jazz3k, 2026-07-03](https://news.ycombinator.com/item?id=48780877))

**Money:**
- Several freelancers advertise exactly this service ([kieranlenton54](https://news.ycombinator.com/item?id=48388928), [jensrusi](https://news.ycombinator.com/item?id=48748389), [Orangecat2026](https://news.ycombinator.com/item?id=49156706)).
- A consultant sees "a real need for it" ([ethagnawl](https://news.ycombinator.com/item?id=48436232)).
- Lovable's own backend lock-in makes fixes harder ([allthetime](https://news.ycombinator.com/item?id=49288290)).

**Caveat:** the buyer is the secondary segment, people who have not yet earned. The topics overlap the "Stripe paid-but-no-access checks" and security-triage ideas already considered. This is strong new evidence for those ideas, not a new idea.

### #4. E. Surprise bills and hard budget caps (22 authors, 20 of 22 items in Aug–Oct)

**In plain words:** a leaked key, a runaway agent or serverless costs can produce an unbounded bill. Solo developers avoid platforms that have no hard cap.

Quotes:
- "I would pay for Cloudflare Workers Paid ($5) in a heartbeat… once you're on the paid plan, you're exposed to unlimited risk… As a solo dev, it's a risk I simply cannot take" ([woodylondon, 2026-04-16](https://news.ycombinator.com/item?id=47795924))
- "A key got hacked and a Chinese-language bot used $300 in tokens in an hour… the spending limit is meaningless without a hidden checkbox called “enforce spending limit,” which is (or at least was for me) off by default." ([iambateman, 2026-10-04](https://news.ycombinator.com/item?id=49950313))
- "I've had an AI coding agent enter a doom loop for hours multiple times now." ([vincentmathis, 2026-10-04](https://news.ycombinator.com/item?id=49951446))
- "If a company can’t give me hard limits on the cost I have to pay, I will not do business with them." ([mybrowsercache, 2026-10-04](https://news.ycombinator.com/item?id=49953454))
- Customers are "solving it for themselves with virtual cards" ([gausswho](https://news.ycombinator.com/item?id=49949353))

The spike is driven by Simon Willison's "We're going to need default hard budget caps on pretty much everything" ([652 points, Oct 4](https://news.ycombinator.com/item?id=49949235)).

**Incumbents:**
- Provider-side caps exist but are patchy. One was "Literally only works for four random services" ([modeless](https://news.ycombinator.com/item?id=49949316)), and Cloudflare has none ([hmokiguess](https://news.ycombinator.com/item?id=49955488)).
- Fixed-price hosts, for example [tungnt620](https://news.ycombinator.com/item?id=49626462).

This overlaps the "cost screens for agent runs" idea already considered. The new angle is a cross-provider kill switch for keys and spend.

---

## 3. Real pain with weak or negative money signals

### #5. D. Supervising agents away from the desk (36 authors, 22 of 38 items in Aug–Oct)

**In plain words:** knowing which agent is blocked, approving prompts from a phone, keeping sessions alive across sign-outs and reboots, and keeping the Mac awake.

Quotes:
- "Of the trials started so far, how many have bought at $99?" ([amber71de](https://news.ycombinator.com/item?id=50015771)). The maker replied: "Zero, as far as I can tell… Developers are a stubborn/interesting target group -- I bet there will be more built-it-myself variants than purchases." ([lukeed, 2026-10-09](https://news.ycombinator.com/item?id=50016283))
- "What exactly should I pay 99 for?" ([worldisaduck](https://news.ycombinator.com/item?id=50013229))
- Free alternatives were recommended in the same thread: Heeler ([joshstrange](https://news.ycombinator.com/item?id=50022438)) and herdr-web-ui ([antoniomika](https://news.ycombinator.com/item?id=50014638)).
- "it periodically signs me out, breaking the session… you are not allowed to run remote control for those sessions" ([mynegation, 2026-10-06](https://news.ycombinator.com/item?id=49985469))
- "missed permission prompts, no idea which agent was waiting on me" ([ericksnetwork](https://news.ycombinator.com/item?id=47901927)). A Mac menu-bar switcher for agents waiting on you launched Oct 13 ([Muster](https://news.ycombinator.com/item?id=50074942)).
- Keep-awake helpers are a recurring side need: a lid-closed applet sold on Gumroad ([d0ublespeak](https://news.ycombinator.com/item?id=48452717)) and "my screen would turn off, instantly interrupting whatever was running" ([Adam-Hincu](https://news.ycombinator.com/item?id=49129872)).

**Incumbents:** first-party Remote Control and the mobile apps ("finally quite usable", [theptip](https://news.ycombinator.com/item?id=49619628)), `claude agents` ([adocomplete](https://news.ycombinator.com/item?id=49159045)), herdr, Paseo, Orca and a dozen more ([KronisLV's list](https://news.ycombinator.com/item?id=49945423)). The one pay-signal in this cluster is for the free, open-source multiplexer herdr: "I love this tool so much I’d pay for it" ([tyleo](https://news.ycombinator.com/item?id=49202022)).

**Verdict:** the clearest negative price test in the dataset.

### #6. F. Usage-limit anxiety and juggling accounts (23 authors, 11 of 23 in Aug–Oct)

- "449 subagents cut off by limits… 438 redone" ([autorunfun, 2026-09-24](https://news.ycombinator.com/item?id=49831380))
- "It's a daily occurrence for me to use 2-3 accounts for the same conversation." ([ftchd](https://news.ycombinator.com/item?id=49689506))
- "I really wish there was a canonical platform endpoint to programmatically check Codex usage amount and the quota reset times" ([minimaxir](https://news.ycombinator.com/item?id=48963777))
- Claude Code "will abruptly break the work and leave it there unfinished as soon as it runs out of tokens" ([algoth1](https://news.ycombinator.com/item?id=48857956))
- Trackers are free and plentiful: ccusage, cc-probeline ([labzink](https://news.ycombinator.com/item?id=49272665)), usagi ([duggan](https://news.ycombinator.com/item?id=48458412)).
- Using multiple accounts to dodge limits is against the terms of service ([adastra22](https://news.ycombinator.com/item?id=49416557)).

### #7. G. Every session starts from zero (22 authors, 12 of 22 in Aug–Oct)

- "Every new session starts from zero. And the AI keeps suggesting ideas I already said no to months ago." ([kiokuapp](https://news.ycombinator.com/item?id=48966917))
- "the answer usually already existed somewhere in my old sessions… (~3.3 GB)" ([vshulcz](https://news.ycombinator.com/item?id=48923305))
- "/resume… you can only filter by first message or custom name" ([cavino](https://news.ycombinator.com/item?id=48012400))
- Supply heavily exceeds visible demand: ctx ([luca-ctx](https://news.ycombinator.com/item?id=49389642)), deja, Claude-Find, CogniKernel ([KanishkNoir](https://news.ycombinator.com/item?id=49851311)), jevmem ([avinashjetwani](https://news.ycombinator.com/item?id=49846413)), Lapse ([hariprasd](https://news.ycombinator.com/item?id=49600470)) and tenjin ([AliAbdoli](https://news.ycombinator.com/item?id=49689157)) are all free. A skeptic sees AI 'memory' "as a pain point for people in their experience using LLMs" and says "It wastes context" ([swordsith](https://news.ycombinator.com/item?id=49584198)).

### #8. H. Keeping CLAUDE.md, AGENTS.md, skills, MCP and hooks in sync (27 authors, 20 of 27 in Aug–Oct)

- "One agent standard that causes me pain: AGENTS.md / CLAUDE.md. I have multiple machines… and runtimes" ([schipperai](https://news.ycombinator.com/item?id=49587840))
- "The pain point you're underselling is hooks. They're the least portable piece by far" ([JulienZammit](https://news.ycombinator.com/item?id=47861545))
- "Switched to pi to avoid having to keep skills/MCP configs in sync across agents" ([by2kaapi](https://news.ycombinator.com/item?id=49930109))
- The "Ask HN: How do you manage skills files?" thread drew 299 comments ([thread](https://news.ycombinator.com/item?id=49589914)). The usual answer is symlinks, chezmoi ([jameshiew](https://news.ycombinator.com/item?id=49592102)), sx ([nhod](https://news.ycombinator.com/item?id=49599972)), aix ([yokuze](https://news.ycombinator.com/item?id=49601053)) or capshelf ([mstr32](https://news.ycombinator.com/item?id=49594219)), all free.
- Claude Code reading AGENTS.md ([Sept 18](https://news.ycombinator.com/item?id=49760187)) removed the biggest papercut.

---

## 4. Interesting complaints with little sign of money

- **I. Getting screenshots into terminal agents, especially over SSH** (16 authors).
  - "screenshot → save → scp → paste path" ([arihantsethia](https://news.ycombinator.com/item?id=47977572))
  - "paste into a claude session running over SSH, it pastes the path to the file, not the data" ([kstenerud](https://news.ycombinator.com/item?id=48305089))
  - "describing where a broken UI is and taking screenshots for AI agents really sucks" ([Loerei](https://news.ycombinator.com/item?id=48834908))
  - At least six small free tools exist: SnippAI ([brothaakhee](https://news.ycombinator.com/item?id=48936308)), Hotshot ([andan02](https://news.ycombinator.com/item?id=48588204)), clipport, screenshotter ([mgranados](https://news.ycombinator.com/item?id=48461235)) and others.
- **J. Verifying agent output** (15 authors).
  - "Verification has been the painful one" ([jhgaylor](https://news.ycombinator.com/item?id=49125075))
  - Watching CI in an agent loop "burns tons of tokens", fixed with a deterministic CLI poller ([klardotsh](https://news.ycombinator.com/item?id=49883966))
  - A test "was green for weeks" while the feature was deleted ([alekstret](https://news.ycombinator.com/item?id=49309410))
  - This overlaps the review and visual-review ideas already considered.
- **K. Claude Code terminal papercuts** (10 authors).
  - "Cut and paste is broken in Claude Code… leading spaces and extraneous newlines" ([bryanlarsen](https://news.ycombinator.com/item?id=48733653))
  - "Soft line breaks are copied to clipboard as hard line breaks" ([jansan](https://news.ycombinator.com/item?id=48185782))
  - Partly fixed upstream with `/tui default` ([bickov](https://news.ycombinator.com/item?id=48744475)).
- **L. Sandboxing and approval fatigue** (21 authors, very crowded).
  - One builder lists "36 other similar projects" ([petesergeant](https://news.ycombinator.com/item?id=49109201)).
  - Approval fatigue: "you start clicking Approve on autopilot" ([laurencoral](https://news.ycombinator.com/item?id=48830666)).
- **M. Shipping Mac software** (13 authors, all from one May thread, [Distributing Mac software…](https://news.ycombinator.com/item?id=48075366)).
  - "Between quarantine, code signing, and notarizing (which requires $99 a year), it's just not worth it." ([ryandrake](https://news.ycombinator.com/item?id=48077524))
  - The maker of a small paid menu-bar app: "The hardest part was not the code, it was figuring out which app store rules I had accidentally stepped on" ([ashwani1242](https://news.ycombinator.com/item?id=48184244)).
- **N. Freelancer invoicing churn** (13 authors).
  - Harvest raised prices after its acquisition ([thread](https://news.ycombinator.com/item?id=49374920)). "They doubled my bill… I declined and am now using Clockify" ([mherrmann](https://news.ycombinator.com/item?id=49376085)).
  - Several devs built their own instead ([ddyy](https://news.ycombinator.com/item?id=48920389), [springtimesun](https://news.ycombinator.com/item?id=49141854)).
  - "none of my customers will let me bill them $1500 more… because I'm using AI" ([pmontra](https://news.ycombinator.com/item?id=48389272)).
- **O. "Claudespeak"** (15 authors).
  - "I would happily pay more for a claude model that performs the same but speaks normal English… Every ticket, every PR feedback, every comment in the codebase is poisoned" ([invalidusernam3](https://news.ycombinator.com/item?id=49817128))
  - This is a model-level pain. Free skills and plugins such as Terse already exist ([Show HN](https://news.ycombinator.com/item?id=49995809)).

## 5. Pricing and buying-behavior signals

These bear on the $30–$100 one-time model.

- **A one-time license with a year of updates is the preferred model.**
  - "TablePlus is a good example. I buy their product and in exchange I get a year of updates." ([neilalexander](https://news.ycombinator.com/item?id=48847017))
  - A Tower replacement is planned as "a one time purchase with support guaranteed for a year" ([Jeremy1026](https://news.ycombinator.com/item?id=49690475)).
  - "I could see it maybe as a one-time purchase, but $90/yr/user is somthing I'd never grab." ([jjcm](https://news.ycombinator.com/item?id=49700565))
  - A Mac voice tool for agents is priced at "$29.99 licence for 2 Macs" ([danielfromtas](https://news.ycombinator.com/item?id=48991728)).
- **The main competitor is DIY.**
  - "Could we please stop putting price tags on 15-commit repos?" ([SeriousM](https://news.ycombinator.com/item?id=48452721))
  - "Its hard to get people to pay anything.. but i did make about $1000 from v1" (a CLI for watching Codex) ([radio879](https://news.ycombinator.com/item?id=49605626))
  - A developer is building a TablePlus replacement because "the latest releases of TablePlus have gone down in terms of user interface quality" ([ykshev](https://news.ycombinator.com/item?id=48453999)).
- **Moats beyond code.** "given the ease at which software can be ideated and maintained, i would rather focus on having a more dataset-intensive moat" ([sim04ful](https://news.ycombinator.com/item?id=49418858)). Sellers also hide what earns money: "it would be product suicide to openly call out a money making product" ([unified101](https://news.ycombinator.com/item?id=49417836)).

## 6. New evidence on ideas the client already considered

Only the strong items are listed here.

- **Parallel-agent desktop managers.** This confirms "crowded, few pay":
  - One comment lists 10+ products ([KronisLV](https://news.ycombinator.com/item?id=49945423)).
  - The first party shipped `claude agents` ([adocomplete](https://news.ycombinator.com/item?id=49159045)).
  - Pocketty had zero sales at $99 ([lukeed](https://news.ycombinator.com/item?id=50016283)).
  - The unsolved layer underneath is cluster A.
- **Cost screens for agent runs:** clusters E and F are both active. E spiked in October.
- **Stripe paid-but-no-access checks:** freelancers sell fixes for "webhooks that fail or double-fire" ([Andler](https://news.ycombinator.com/item?id=50050342)).
- **Forgotten projects holding live keys:** cluster B is the live-session version, including a leaked key that was not noticed "until the bill came" ([HyperAI](https://news.ycombinator.com/item?id=49508497)).
- **React trees exposed to agents:**
  - "Hover over your UI element to get its exact location in code" ([Loerei](https://news.ycombinator.com/item?id=48834908)).
  - Orca's built-in browser lets you "select an object(s), write a comment and send it back to the agent" ([vulture916](https://news.ycombinator.com/item?id=49235682)).
- **Design lint:** a paid service turns Lovable apps that "look and behave like the AI default" into on-brand products ([jensrusi](https://news.ycombinator.com/item?id=48748389)).

## 7. Three most surprising findings

1. **Developers would rather build it than buy it, even at $99, and the sellers say so.** Pocketty had zero buyers during its trial window ([link](https://news.ycombinator.com/item?id=50016283)). Several categories show the same pattern:
   - On local port tools: "absolutly eveyrone I know vibe-coded this thing" ([link](https://news.ycombinator.com/item?id=47975381)).
   - On secret brokers: "everyone got the same idea again" ([link](https://news.ycombinator.com/item?id=49025146)).
   - On sandboxes: "36 other similar projects" ([link](https://news.ycombinator.com/item?id=49109201)).

   A paid tool has to be hard to vibe-code (trust, security, OS integration) or clearly better finished.
2. **Security friction pushes people to less security.** A user who keeps "no secrets on disk" tells the agent to dump 1Password credentials into `.env` to avoid approving "15 times for every test run" ([link](https://news.ycombinator.com/item?id=50024528)). The macOS sandbox cannot do the per-domain egress control that would make this safe ([link](https://news.ycombinator.com/item?id=48764305)). **(guess)** This is a native-Mac gap that a $30–$60 utility could fill.
3. **The parallel-agent bottleneck has moved from orchestration UI to the environment.** One dev maintains 15K lines of Rust just to isolate "everything else" ([link](https://news.ycombinator.com/item?id=48853408)). Another gave up parallelizing within a repo ([link](https://news.ycombinator.com/item?id=48355104)). Worktrees eat 200 GB build folders ([link](https://news.ycombinator.com/item?id=49927304)). Meanwhile, the money that does change hands goes to human freelancers who fix AI-built apps ([link](https://news.ycombinator.com/item?id=50050342)), not to tools.

---

## Appendix: full evidence lists (every item linked)

Each line: date · author · HN link · thread title · first ~170 characters of the comment (verbatim, lightly escaped). Counts are of distinct authors in this curated list, not of all HN mentions.

### A. Parallel worktrees isolate code but not the running app (ports, .env, DBs, compose, caches, disk, dev-server lifecycle) — 70 items, 69 distinct authors, 21 dated Aug–Oct 2026

- 2026-10-06 · jadar · [item 49977535](https://news.ycombinator.com/item?id=49977535) · _JetBrains reports revenue growth, net financial loss for 202_ — “I still haven’t found an IDE that I feel really helps me develop with AI better than the command line. I have built bespoke tools that work the way I want. But a really g…”
- 2026-10-06 · xlii · [item 49974791](https://news.ycombinator.com/item?id=49974791) · _Why Common Lisp is now the best programming language_ — “And there is a super power to it. / It's possible to write the whole system only by defining the types. / The "glue" can be sloppy but as long as it keeps on the edges th…”
- 2026-10-05 · sgammon · [item 49960065](https://news.ycombinator.com/item?id=49960065) · _Turn off Apple Intelligence on macOS 27 and get its disk spa_ — “Wow. 12gb?! Huge. That’s almost a third of an added worktree’s rust target dir!…”
- 2026-10-01 · yearolinuxdsktp · [item 49927304](https://news.ycombinator.com/item?id=49927304) · _How to speed up the Rust compiler in September 2026_ — “It’s insane. 45 minutes to build debug from scratch. Linking is super slow even in debug and that’s without LTO. / Incremental compilation is not cleaned up. Older deps p…”
- 2026-10-01 · Aurornis · [item 49924065](https://news.ycombinator.com/item?id=49924065) · _How to speed up the Rust compiler in September 2026_ — “You should have set up https://github.com/mozilla/sccache at minimum. Setting up compiler caching is routine for people coming from older compiled language backgrounds bu…”
- 2026-09-30 · piyh · [item 49915434](https://news.ycombinator.com/item?id=49915434) · _Gemini 4 Argon_ — “They only released auto mode in the last 2 weeks. Before that it was bypass permissions or manually approve every single tool call. Antigravity is permanently 6 months be…”
- 2026-09-27 · nexo-v1 · [item 49865990](https://news.ycombinator.com/item?id=49865990) · _Floci: Locally emulating any cloud service_ — “I was never happy with how heavy LocalStack was, so I'm going to try this for my next green field cloud app. / I think having such emulator being lightweight and quick to…”
- 2026-09-22 · joshstrange · [item 49800839](https://news.ycombinator.com/item?id=49800839) · _JetBrains Air: A System of Products for Agentic Software Dev_ — “Yes, it’s because I’m writing less code by hand. I mostly use IDEA now to navigate/review the code or do my own debugging/tracing. My time in the IDE has fallen drastical…”
- 2026-09-21 · christophilus · [item 49786309](https://news.ycombinator.com/item?id=49786309) · _AX – Google’s Open Agentic Orchestrator_ — “The way I do it is each worktree gets its own .env, with dev credentials to whatever it needs access to, and my coworkers have theirs set up to have an isolated Postgres…”
- 2026-09-14 · jacobgold · [item 49703810](https://news.ycombinator.com/item?id=49703810) · _GPT-5.6 Luna vs. GPT-6 Astra: Is a $1.20 Model Good Enough f_ — “Since you asked, the answer is that I built and use an agent multiplexer called Clor https://clor.com / I have a $200/mo Claude subscription and a $200/mo Codex subscript…”
- 2026-09-11 · polishdude20 · [item 49665489](https://news.ycombinator.com/item?id=49665489) · _Working with Git Worktrees in Magit_ — “Aren't worktrees multiple copies? I usually have multiple worktrees and each one has different ports the various apps and servers talk to so I can easily visit each workt…”
- 2026-09-11 · cdmckay · [item 49664035](https://news.ycombinator.com/item?id=49664035) · _Working with Git Worktrees in Magit_ — “The problem I have with worktrees is that if I want to test the changes I need to juggle the worktrees. / It works better for me if I have multiple copies of the repo wit…”
- 2026-09-11 · miggol · [item 49655792](https://news.ycombinator.com/item?id=49655792) · _Working with Git Worktrees in Magit_ — “A slight limitation of worktrees is that you can only have a branch checked out once in all of your worktrees. I guess that's just how git works. / But when I want to che…”
- 2026-09-11 · black_knight · [item 49654938](https://news.ycombinator.com/item?id=49654938) · _Working with Git Worktrees in Magit_ — “I think my layout is similar to yours. What do your scripts do? / My branches end up in a tree structure (no shit!), and I rebase and merge up stream as changes land. I g…”
- 2026-08-31 · colechristensen · [item 49509253](https://news.ycombinator.com/item?id=49509253) · _uv: Deduplicate all files in the wheel cache_ — “The things which use my disk are things like package caches in several languages, build artifacts in both release and debug, multiplied by worktrees, things like iOS devi…”
- 2026-08-26 · cahaya · [item 49446476](https://news.ycombinator.com/item?id=49446476) · _Apple introduces M6 and M5 Ultra_ — “Until recently my M1 Max 32GB 2021 was great until memory became the bottleneck. My M1 Pro 8GB lasted me less than a year bcs with Docker dev stuff made it sluggish. 32GB…”
- 2026-08-25 · booty · [item 49438090](https://news.ycombinator.com/item?id=49438090) · _New Mac mini, featuring M6 and M5 Pro_ — “I work on a big web monolith on an M5 Pro 48GB. / I'm usually running about ~4 instances of it locally in separate Git worktrees, which (in our setup) means I'm also runn…”
- 2026-08-25 · SimionBaws · [item 49430363](https://news.ycombinator.com/item?id=49430363) · _Parallel development without the headaches using Git worktre_ — “Easy: each worktree starts services on new ports. https://termic.dev goves you ENV variables for this, oir you definee your own custom named variables, and termic assigns…”
- 2026-08-24 · irskep · [item 49414315](https://news.ycombinator.com/item?id=49414315) · _Parallel development without the headaches using Git worktre_ — “I use git worktrees daily. I'm surprised by how hard it can be to explain them to people who have never used them. Lately I've settled on "like clones, but sharing a .git…”
- 2026-08-11 · jbo76 · [item 49258046](https://news.ycombinator.com/item?id=49258046) · _Coordinate coding agents and Git worktrees around features_ — “md² gives you more control and allows for better multi-tasking when working with agents. / These are some of the problems I ran into and am trying to solve: / - a new wor…”
- 2026-08-09 · krupkinmaxim · [item 49235472](https://news.ycombinator.com/item?id=49235472) · _OpenChamber: An Agentic Development Environment_ — “The split I've settled on: git worktrees for parallelism, containers only when I actually need isolation from the host. / Worktrees are cheap because they share the objec…”
- 2026-07-30 · madarco · [item 49114250](https://news.ycombinator.com/item?id=49114250) · _Git worktrees are not an isolation boundary for coding agent_ — “nono is great but you'll still won't be able to run multiple dev servers, dbs or test in the browser... / the better alternative is using sandboxes, for TRUE isolation. /…”
- 2026-07-30 · francislavoie · [item 49111504](https://news.ycombinator.com/item?id=49111504) · _Git worktrees are not an isolation boundary for coding agent_ — “I set up a custom hook in Claude which runs my own worktree creation/cleanup script, which takes care of copying my node\_modules into the worktree, my .env (plus doing so…”
- 2026-07-30 · user43928 · [item 49111444](https://news.ycombinator.com/item?id=49111444) · _Git worktrees are not an isolation boundary for coding agent_ — “Same here, over hundreds of worktrees in months of work. / The only problem I ran into was when Codex or Claude Code were configured to create the worktrees nested into t…”
- 2026-07-30 · nullderef · [item 49110949](https://news.ycombinator.com/item?id=49110949) · _Git worktrees are not an isolation boundary for coding agent_ — “I haven’t hit these issues when using worktrees. But what’s a pain is having to compile from scratch every time, and not carrying over gitignored files.…”
- 2026-07-30 · bryanlarsen · [item 49110131](https://news.ycombinator.com/item?id=49110131) · _Superlogical_ — “Hmmm, it's a fairly stock emacs setup. Most of the weird/specific stuff is outside of emacs: setting up a sandbox, managing worktrees, managing disk space because each wo…”
- 2026-07-30 · ymir_e · [item 49109559](https://news.ycombinator.com/item?id=49109559) · _Agent-Manager: A Tmux TUI for Running Claude Code, Codex and_ — “I've tested out just about every tool like this, and ended up coding my own, it is really minimal though. / The primary reason people reach for these tools are two to thr…”
- 2026-07-30 · kasktra · [item 49107548](https://news.ycombinator.com/item?id=49107548) · _Show HN: I built myself the simplest worktree management too_ — “I recently went back to using my terminal more instead of using tools like Conductor, Paseo, Codex App. This led me to start managing my own worktrees, which is annoying…”
- 2026-07-28 · grepsedawk · [item 49086018](https://news.ycombinator.com/item?id=49086018) · _Setup Script Should Support Git Worktrees_ — “Author here. Parallel worktrees showed me where Git’s isolation ends. Files stayed separate; ports, databases, cache keys, queues, and Compose resources did not. We now s…”
- 2026-07-27 · Uptrenda · [item 49065206](https://news.ycombinator.com/item?id=49065206) · _Show HN: Port Zero – How I learned to stop worrying and love_ — “I get the problem well. I have built a networking runtime and a Python networking library that extensively used servers as part of testing. If you bind to a specific port…”
- 2026-07-27 · octopoc · [item 49063648](https://news.ycombinator.com/item?id=49063648) · _Show HN: Port Zero – How I learned to stop worrying and love_ — “Hi HN, / Recently I wasted several hours wrangling my dev environment only to find out that the browser frontend was talking to the wrong version of the backend. This got…”
- 2026-07-10 · tonyarkles · [item 48866765](https://news.ycombinator.com/item?id=48866765) · _After 7 years in production, Scarf has reluctantly moved awa_ — “Speaking as someone who has tried Haskell but hasn’t ever really gotten into it, but spends all day with a C++ codebase that also has long cold-compile times… I think the…”
- 2026-07-09 · aroman · [item 48853408](https://news.ycombinator.com/item?id=48853408) · _GPT-5.6_ — “No. I used to use Cursor, but now my workflow is that I use an inhouse CLI tool I wrote called "bud" that wraps/seeds the harnesses per-worktree, and boots a full copy of…”
- 2026-07-09 · xyzsparetimexyz · [item 48843951](https://news.ycombinator.com/item?id=48843951) · _Rewriting Bun in Rust_ — “› I asked Claude to loop the workflow on all 1,448 .zig files, and about 2 minutes in, one Claude ran git stash before committing. Another ran git stash pop. And then git…”
- 2026-07-07 · nomel · [item 48825002](https://news.ycombinator.com/item?id=48825002) · _Herdr: One terminal to rule them all_ — “The problem I have with worktrees is when I need to switch branches to merge or something. If a work tree for any branch involved exists, git prevents me from switching t…”
- 2026-07-07 · dools · [item 48823715](https://news.ycombinator.com/item?id=48823715) · _Herdr: One terminal to rule them all_ — “I use this bash script that creates tmux windows and panes in a worktree and then undoes the process: / https://gist.github.com/iaindooley/cc8a61a1ff0fe23526c850906... /…”
- 2026-07-07 · AgentME · [item 48823552](https://news.ycombinator.com/item?id=48823552) · _Astro 7.0_ — “The AI Enhancements section was interesting. I've been wondering about the best practices for agents interacting with long-running dev servers, and Astro 7's approach (ru…”
- 2026-07-07 · dagss · [item 48823265](https://news.ycombinator.com/item?id=48823265) · _Herdr: One terminal to rule them all_ — “Is there git worktree support? / With the long waits for agents to do stuff I really don't see how one can get anything done without multitasking with multiple worktrees…”
- 2026-07-03 · parpfish · [item 48780980](https://news.ycombinator.com/item?id=48780980) · _Ask HN: Is anyone experimenting with different ways of using_ — “i hate that there are so many worktrees now that its a real pain to find the actual file and modify it by hand. / there are so many stupid little changes (e.g., rewording…”
- 2026-07-03 · just-tom · [item 48772037](https://news.ycombinator.com/item?id=48772037) · _Ask HN: Is anyone experimenting with different ways of using_ — “I'm building "workboxes" to work on my startup. It helps me develop features insanely fast. A workbox is a simple worktree-in-a-sandbox per feature. I have a simple front…”
- 2026-06-24 · yaskou · [item 48655552](https://news.ycombinator.com/item?id=48655552) · _.gitignore Isn't the only way to ignore files in Git_ — “How do you manage the lifecycle of the worktrees in practice? Is it mostly manual git worktree add/remove, or do you use aliases/scripts/some other tools?…”
- 2026-06-18 · ngai_aku · [item 48587214](https://news.ycombinator.com/item?id=48587214) · _Emacs 31 is around the corner: The changes I'm daily driving_ — “agent-shell is awesome, but Anthropic banning subscription usage via ACP is a killer. I've liked claude-code-ide.el when I've used it, but its lack of concurrent sessions…”
- 2026-06-16 · davidhaggstrom · [item 48560861](https://news.ycombinator.com/item?id=48560861) · _Ask HN: What's your multi-agent orchestration setup, and suc_ — “I just have worktrees set up with a script that pulls in my venv and git hooks so each one runs isolated. Sometimes I miss having a good way for agents to share some info…”
- 2026-06-12 · port11 · [item 48500650](https://news.ycombinator.com/item?id=48500650) · _Show HN: Homebrew 6.0.0_ — “Mise’s refusal to make global packages globally available is off-putting. I keep using it for specific Node versions and the integration with fnox. / The big drawback: ha…”
- 2026-06-10 · gempir · [item 48472352](https://news.ycombinator.com/item?id=48472352) · _macOS Container Machines_ — “I just wish bind mounts would be more performant/native. I get that this is probably impossible, and probably also sucks on Linux, haven't tried. / But like having contai…”
- 2026-06-09 · kwar13 · [item 48461808](https://news.ycombinator.com/item?id=48461808) · _Ask HN: What are tools you have made for yourself since the_ — “nothing groundbreaking but this little tool cleans up build artifacts automatically so my hd frees up every once in a while. / https://github.com/kavehtehrani/devprune…”
- 2026-06-09 · dsmurrell · [item 48457988](https://news.ycombinator.com/item?id=48457988) · _Ask HN: What are tools you have made for yourself since the_ — “https://runnem.com - something I use to easily get projects running again when I get back to them. It also helps the AI get at the logs of the running processes.…”
- 2026-06-09 · udave · [item 48457715](https://news.ycombinator.com/item?id=48457715) · _Ask HN: What are tools you have made for yourself since the_ — “Ive made my own agentic IDE centered around worktrees and containerization. it allows me to run multiple development environments on my machine with each development serv…”
- 2026-06-04 · cadamsdotcom · [item 48405988](https://news.ycombinator.com/item?id=48405988) · _Show HN: Boxes.dev: ditch localhost; run Claude Code and Cod_ — “Hello gents, some quick feedback. / I think when you say “ditch localhost” you’re telling me to ditch my fast, instant-response laptop which I own and can peg the CPU of…”
- 2026-06-04 · 2001zhaozhao · [item 48402714](https://news.ycombinator.com/item?id=48402714) · _Show HN: Boxes.dev: ditch localhost; run Claude Code and Cod_ — “Really cool tool! / I am building a self-hosted tool (OpenClaw-like) to solve the same problem (running agents 24/7 and access from monile), which I think is the main alt…”
- 2026-06-01 · zjy71055 · [item 48355104](https://news.ycombinator.com/item?id=48355104) · _Rift: Better Alternative to Git Worktrees_ — “git worktree (or any COW snapshot like this) still leaves you reinstalling node\_modules per tree and fighting over a dev server port. That's the actual cost, and none of…”
- 2026-05-23 · BrandiATMuhkuh · [item 48247259](https://news.ycombinator.com/item?id=48247259) · _Launch HN: Superset (YC P26) – IDE for the agents era_ — “I've been using Superset as my daily driver for about 2 months and I'm loving it. / i have created a simple setup script that reserves a couple of ports per workspace/wor…”
- 2026-05-23 · laurels-marts · [item 48246985](https://news.ycombinator.com/item?id=48246985) · _Open source Kanban desktop app that runs parallel agents on_ — “i have shell scripts that create/tear down worktrees. the shell script finds unique unused ports across all existing worktrees and assigns in local .env upon worktree cre…”
- 2026-05-23 · chrisvenum · [item 48244872](https://news.ycombinator.com/item?id=48244872) · _Open source Kanban desktop app that runs parallel agents on_ — “I have this issue at work, I asked CC to create a very simple bun CLI tool that can be hard to create, destroy and list worktrees. The CLI seeds the .env file with a url,…”
- 2026-05-23 · nullbio · [item 48244816](https://news.ycombinator.com/item?id=48244816) · _Launch HN: Superset (YC P26) – IDE for the agents era_ — “One thing I don't understand with all of these, is how they're handling different worktree infrastructure spin-up? / For example, if I have a webapp, I want each of the w…”
- 2026-05-22 · jerrygenser · [item 48238352](https://news.ycombinator.com/item?id=48238352) · _Launch HN: Superset (YC P26) – IDE for the agents era_ — “This uses separate git worktrees. If we have a local dev setup involving multiple docker services, is there a recommended solution for managing those envs? I didn't see.…”
- 2026-05-18 · chi_features · [item 48185797](https://news.ycombinator.com/item?id=48185797) · _No more JetBrains products for me_ — “I wasn't going to pipe up because I wasn't sure that a Hackernews thread is a good substitute for an issue tracker... but it's related to new AI-driven workflows so I hop…”
- 2026-05-12 · nokturn · [item 48102604](https://news.ycombinator.com/item?id=48102604) · _What do you NOT like about Cursor / VSCode / Claude Code des_ — “worktrees are a must if you want to run parallel tasks in the same codebase... Either that or sandboxes :) / That example i gave above with the worktrees happened to me r…”
- 2026-05-07 · elysianfields · [item 48049367](https://news.ycombinator.com/item?id=48049367) · _Agent-harness-kit scaffolding for multi-agent workflows (MCP_ — “This looks really cool. Did you think about including automatic worktree creation + sandboxing? / I've built sth similar (more focus on the project setup and being able t…”
- 2026-05-05 · Finbarr · [item 48025040](https://news.ycombinator.com/item?id=48025040) · _Treat your coding agents like developers_ — “Author here. Three months ago I posted a Show HN for yolobox (1) - a sandbox for running AI coding agents without them being able to nuke your home directory. / Since the…”
- 2026-05-01 · OriPekelman · [item 47975381](https://news.ycombinator.com/item?id=47975381) · _I Got Sick of Remembering Port Numbers_ — “This is really amusing. Because absolutly eveyrone I know vibe-coded this thing. I think the first one was https://github.com/ralt/dns-to-port possibly mine is second (bu…”
- 2026-05-01 · hotfixguru · [item 47971483](https://news.ycombinator.com/item?id=47971483) · _I Got Sick of Remembering Port Numbers_ — “Vercel’s portless is a great alternative, but unfortunately it doesn’t work well with oauth flows. I’ve built portmap(0) to solve that. Also comes with skills which makes…”
- 2026-05-01 · CGamesPlay · [item 47971271](https://news.ycombinator.com/item?id=47971271) · _I Got Sick of Remembering Port Numbers_ — “I've built this twice before. The main problem that I hit is that the AI agents suck at the process lifecycle management: leaving processes alive, starting the same daemo…”
- 2026-05-01 · pyreal · [item 47971151](https://news.ycombinator.com/item?id=47971151) · _I Got Sick of Remembering Port Numbers_ — “I created something similar to help me spin up complex apps in multiple worktrees with full port orchestration: https://outport.dev/…”
- 2026-04-29 · maherbeg · [item 47950073](https://news.ycombinator.com/item?id=47950073) · _Zed 1.0_ — “It works well but there are a lot of missing features skill auto complete custom agents sub agents background process management…”
- 2026-04-28 · graiz · [item 47939246](https://news.ycombinator.com/item?id=47939246) · _I Got Sick of Remembering Port Numbers_ — “…”
- 2026-04-27 · cityofdelusion · [item 47928016](https://news.ycombinator.com/item?id=47928016) · _GitHub Copilot is moving to usage-based billing_ — “Huh, I find my copilot plugin to be so incredibly glitchy. My agents are always reporting that their shells are mangled that commands are truncated and all kinds of nonse…”
- 2026-04-23 · laurels-marts · [item 47878883](https://news.ycombinator.com/item?id=47878883) · _Parallel agents in Zed_ — “Unless I misunderstand something but why not just roll a couple of helper shell scripts that create a new git worktree for you, copy over a local .env file (or any other…”
- 2026-04-23 · shmoogy · [item 47874122](https://news.ycombinator.com/item?id=47874122) · _Parallel agents in Zed_ — “Conductor has a feature that lets you define a script to copy .env and other things as needed from main repo into new worktrees on creation. / I don't use it much anymore…”
- 2026-04-23 · Atotalnoob · [item 47871666](https://news.ycombinator.com/item?id=47871666) · _Parallel agents in Zed_ — “I’m interested in these types of tools, but the biggest issue I am currently having in my workflow is manually verifying everything is working. Tests and stuff are nice,…”

### B. Keeping secrets and API keys away from coding agents (credential brokering, approval fatigue) — 50 items, 49 distinct authors, 30 dated Aug–Oct 2026

- 2026-10-15 · radim_h · [item 50100776](https://news.ycombinator.com/item?id=50100776) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “We’re building Stashbase.dev around this. The agent makes API calls through a proxy that holds the upstream credentials, with access restricted by host, method and path.…”
- 2026-10-13 · sscaryterry · [item 50074525](https://news.ycombinator.com/item?id=50074525) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “› You still need an egress allowlist the guest cannot rewrite, credentials that never enter the guest, and a hard call budget per task. I would pay more for that broker l…”
- 2026-10-13 · arbor-group · [item 50071998](https://news.ycombinator.com/item?id=50071998) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “The broker point is the part I keep coming back to as well. Short-lived credentials help, but an agent can do a lot in five minutes if the scope is still broad, so the in…”
- 2026-10-13 · ekorondy · [item 50071898](https://news.ycombinator.com/item?id=50071898) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “The host isolation everyone is comparing on price is not the hard problem. / gVisor vs a full VM is a real tradeoff. Most agent failures that actually hurt are not sandbo…”
- 2026-10-13 · pro-vi · [item 50066458](https://news.ycombinator.com/item?id=50066458) · _Vne – .env Util for Agents_ — “So vne is a small cli that helps agents to operate with .env files which were the only thing left I really open a code editor for. It is not a sandbox. And it is optimize…”
- 2026-10-13 · cagster · [item 50064826](https://news.ycombinator.com/item?id=50064826) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “Short-lived tokens only limit how long a credential works, but better than nothing. i.e. They don't stop an unwanted action while it's still valid. / A practical pattern…”
- 2026-10-12 · talkarimli · [item 50063391](https://news.ycombinator.com/item?id=50063391) · _Launch HN: Agent37 (YC F26) – Low-cost agent sandboxes for r_ — “congrats on the launch. / i think the sandbox part is getting commoditized, like others said. the harder part is what the agent can touch inside it. / you connect google,…”
- 2026-10-09 · ShakataGaNai · [item 50024528](https://news.ycombinator.com/item?id=50024528) · _Once: Cache CLI commands_ — “OMG. 'op read' with agents. Holy shit. / I first clicked this with just a mild curiosity. But as soon as I saw the 1password example. Lightning. / I try to do everything…”
- 2026-10-09 · alex0ptr · [item 50020505](https://news.ycombinator.com/item?id=50020505) · _Once: Cache CLI commands_ — “Yes, exactly. This is especially frustrating when I leave an agent running for a long time and it gets stuck on my build scripts because it's waiting for my approval. / I…”
- 2026-09-30 · spellboots · [item 49914606](https://news.ycombinator.com/item?id=49914606) · _You said no MCP_ — “There are many ways to do this without using mcp, for example one of the many proxy servers that inject the token into requests. I use a custom solution that redacts all…”
- 2026-09-30 · mijoharas · [item 49909465](https://news.ycombinator.com/item?id=49909465) · _Pi.dev: You Said No MCP_ — “I find it pretty handy. I run any bash tools in a restricted sandbox, and so that it cannot hit the network (usually). I don't want any credentials to be available to the…”
- 2026-09-21 · simonw · [item 49786809](https://news.ycombinator.com/item?id=49786809) · _MCP was always a bad idea?_ — “If a full coding agent can access a CLI tool. that agent can almost certainly access the API keys being used by that tool. They can go as far as decompiling binaries, or…”
- 2026-09-19 · radio879 · [item 49770821](https://news.ycombinator.com/item?id=49770821) · _Inside ZCode: Silently uploading your Git history to the clo_ — “I was wondering if I should try to create my own pseudo filesystem with FUSE for easy copy-on-write/snapshots, a native feel, and automated secrets filtering/swapping. I…”
- 2026-09-18 · thehamkercat · [item 49757541](https://news.ycombinator.com/item?id=49757541) · _Inside ZCode: Silently uploading your Git history to the clo_ — “i use sops / Encrypt: sops encrypt --input-type dotenv --output-type dotenv .env › secrets.enc.env / then rm .env / You can then run your script/dev with: sops exec-env s…”
- 2026-09-12 · stickynotememo · [item 49668727](https://news.ycombinator.com/item?id=49668727) · _Ask HN: What do you do about API keys?_ — “Having them in plaintext always seemed like a bad idea. Forget agents accidentally reading .env; any random package you get from the AUR can trivially read all your keys.…”
- 2026-08-31 · HyperAI · [item 49508497](https://news.ycombinator.com/item?id=49508497) · _OpenClaw 2.0, Accidentally_ — “Convenience always wins until it doesn't. I learned this the hard way — had an API key leak because an agent decided to "helpfully" paste it into a log output. Didn't not…”
- 2026-08-29 · coder-pm · [item 49490126](https://news.ycombinator.com/item?id=49490126) · _Data Exfiltration from Amazon Kiro via Prompt Injection_ — “The root cause is simple, the agent could read a live key! It should never have it. It’s a combination of few issues at once: repo read, write access to the settings file…”
- 2026-08-29 · valenterry · [item 49487108](https://news.ycombinator.com/item?id=49487108) · _Show HN: Sesame - a local-first, open-source password manage_ — “I wish there was a password manager with a different focus. / In the way where there would be a server (selfhosted) that has the passwords and is well protected. Then, on…”
- 2026-08-28 · zbentley · [item 49482470](https://news.ycombinator.com/item?id=49482470) · _The Twelve-Factor App (2025)_ — “Firmly agree. A lot of sibling comments are talking about environment mutation (which does have issues); I want to talk about environment read access. / The environment i…”
- 2026-08-28 · skybrian · [item 49482235](https://news.ycombinator.com/item?id=49482235) · _The Twelve-Factor App (2025)_ — “Now that we use coding agents, you don't want to store secrets anywhere in the same VM, because that makes them vulnerable to exfiltration. The best way is to access exte…”
- 2026-08-16 · _august · [item 49317843](https://news.ycombinator.com/item?id=49317843) · _Show HN: Laptop is the last place your secrets are still in_ — “I've moved my secrets to 1Password Environments (https://www.1password.dev/environments), which works really well for everyday use. / It works with 1password cli (https:/…”
- 2026-08-10 · Humphrey · [item 49251284](https://news.ycombinator.com/item?id=49251284) · _Docker Sandboxes – Disposable, isolated sandboxes for AI age_ — “My feedback on sbx: / Concept is great - works quite well - I often have multiple short lived sandboxes running at once. / Docs (1) on overriding auth are incorrect. Sbx…”
- 2026-08-10 · llimllib · [item 49242449](https://news.ycombinator.com/item?id=49242449) · _Docker Sandboxes – Disposable, isolated sandboxes for AI age_ — “right, but say you give the agent access to github and it can push as you, or make a gist; now it can easily exfiltrate your secret. / And that's just an easy case - real…”
- 2026-08-10 · rusch · [item 49240545](https://news.ycombinator.com/item?id=49240545) · _Docker Sandboxes – Disposable, isolated sandboxes for AI age_ — “The login is annoying but, lacking an open source alternative, this has been my daily driver for a while now because it works great out of the box with two key features:…”
- 2026-08-07 · sparsesignal · [item 49214825](https://news.ycombinator.com/item?id=49214825) · _Responding to the next frontier of critical cyber capabiliti_ — “› I stress about my agent sandboxes all the time / Same here, so I ended up moving the whole dev environment (editors, agents, containers) inside a hardened QEMU/KVM VM t…”
- 2026-08-04 · vekker · [item 49174788](https://news.ycombinator.com/item?id=49174788) · _Where .env Went Wrong_ — “Hm, the main headache I have with .env files is simply that I lose them (switching between machines etc...), or the trouble of sharing secrets with team mates, etc... The…”
- 2026-08-04 · ramses0 · [item 49172519](https://news.ycombinator.com/item?id=49172519) · _Where .env Went Wrong_ — “I wish there was better support for something like 'SECRET\_CMD="..."' (ie: "run this command to get/refresh secrets"), but that's just baking arbitrary command execution…”
- 2026-08-04 · jpitz · [item 49172297](https://news.ycombinator.com/item?id=49172297) · _Where .env Went Wrong_ — “If 1Password hadn't jumped the subscription model shark, I'd be all over that. Any chance you'd entertain supporting bitwarden?…”
- 2026-08-04 · stilwe · [item 49171870](https://news.ycombinator.com/item?id=49171870) · _Where .env Went Wrong_ — “Hey cool, a relevant place to mention my project: https://dotprot.dev/ / Type "dotprot" to copy your .env file into 1Password using the 1P CLI, it verifies it's there, th…”
- 2026-08-04 · fastandfearless · [item 49170604](https://news.ycombinator.com/item?id=49170604) · _Show HN: Isolade, a local-first coding agent workbench with_ — “I can only say the same: "Most people run their coding agents directly on the host system." And the problem between the host system and the microVM approach is the same,…”
- 2026-07-27 · connorelkin · [item 49075465](https://news.ycombinator.com/item?id=49075465) · _Ihatedevops.com – because DevOps separates vibe coder from e_ — “DevOps used to be the most annoying part of software dev. Now it's a lot easier, but the difference between a vibe coder and a software engineer remains. / For people rip…”
- 2026-07-23 · adithyassekhar · [item 49025146](https://news.ycombinator.com/item?id=49025146) · _Show HN: OneCLI – OSS credential gateway that keeps secrets_ — “Holy mother of whatever this is, everyone got the same idea again and there’s a bunch of implementations people are desperate to promote in the comments. / You’re just tr…”
- 2026-07-23 · theozero · [item 49025087](https://news.ycombinator.com/item?id=49025087) · _Show HN: OneCLI – OSS credential gateway that keeps secrets_ — “Looks great. The "credential broker" pattern (inject placeholders, replace in proxy) is something we just added to https://varlock.dev (totally free and open source). / R…”
- 2026-07-23 · Jonathanfishner · [item 49023427](https://news.ycombinator.com/item?id=49023427) · _Show HN: OneCLI – OSS credential gateway that keeps secrets_ — “hey HN, Jonathan and Guy here, creators of OneCLI (https://onecli.sh/). OneCLI is an open source vault for AI Agents. / Traditional vaults are used to store your secrets…”
- 2026-07-22 · satoyoshidev · [item 49008483](https://news.ycombinator.com/item?id=49008483) · _Show HN: CodeAlmanac – Karpathy-style codebase wiki from you_ — “Transcripts tend to have secrets pasted into them during debugging, api keys, .env values and so on. Is there anything that keeps the sync agent from writing those into a…”
- 2026-07-22 · tesnorindian · [item 49003418](https://news.ycombinator.com/item?id=49003418) · _OpenAI and Hugging Face address security incident during mod_ — “The other day I was trying to prevent my pi.dev coding harness to expose my API keys in the env variable to the remotely hosted LLM. This is a chicken and egg problem. Wi…”
- 2026-07-21 · jboss10 · [item 48997440](https://news.ycombinator.com/item?id=48997440) · _Annoying and alarming things about OpenCode_ — “I use this setup as well. I've written an alias for bwrap which only gives the agent access to the current directory and read only access to the docs. / It has read-only…”
- 2026-07-15 · magimas · [item 48919564](https://news.ycombinator.com/item?id=48919564) · _I tricked Claude into leaking your deepest, darkest secrets_ — “but this seems quite overkill no? / I currently run pi agent in Lima on a Mac with only the code project folder mounted and an extension that prevents pi agent from readi…”
- 2026-07-06 · maferland · [item 48809077](https://news.ycombinator.com/item?id=48809077) · _Show HN: Keyhole – Share secrets with your AI agents_ — “I didn't build Keyhole to solve secret management, there are tools like Doppler for that. It lets the agent handle a secret without having it in context. It can put it wh…”
- 2026-07-01 · pdumicz · [item 48749273](https://news.ycombinator.com/item?id=48749273) · _Show HN: I built a way for coding agents to use secrets with_ — “I built secret-shuttle - a tool for coding agents to USE secrets without seeing them. / It's a local daemon + CLI + skills.md. / The agent only ever works with refs like…”
- 2026-07-01 · pietz · [item 48745111](https://news.ycombinator.com/item?id=48745111) · _Ask HN: How do you provide your AI agents with access to cre_ — “is this something you built yourself or do you use a tool that was specifically created for this? I took my own few steps of building something similar, but every week I…”
- 2026-07-01 · onion2k · [item 48744549](https://news.ycombinator.com/item?id=48744549) · _Ask HN: How do you provide your AI agents with access to cre_ — “I don't. I write a lightweight API proxy, usually as a CLI app, that takes requests from the agent, adds secrets and makes the request, and then passes the response trans…”
- 2026-06-30 · atombender · [item 48737694](https://news.ycombinator.com/item?id=48737694) · _Ask HN: Secure wrapper for coding agents?_ — “Seconding this. I've been running Safehouse for months and love that it can wrap any process (it's just a wrapper around the native macOS sandbox API, after all). The onl…”
- 2026-06-28 · skybrian · [item 48709041](https://news.ycombinator.com/item?id=48709041) · _A way to exclude sensitive files issue still open for OpenAI_ — “To avoid the risk of exfiltration, we need to stop using .env for security. API keys needed when working in a repo should be handled by a proxy like ssh-agent, and we nee…”
- 2026-06-12 · nunez · [item 48500030](https://news.ycombinator.com/item?id=48500030) · _Claude Fable is relentlessly proactive_ — “Claude typically recommends .env files for storing secrets. You use one to store a refresh token for the Gmail API or IMAP connection details. Your agent uses an MCP serv…”
- 2026-06-09 · moronim · [item 48462925](https://news.ycombinator.com/item?id=48462925) · _Ask HN: What are tools you have made for yourself since the_ — “I made a CLI tool that securely stores and injects your AI API keys into scripts, so you never have to worry about .env leaks. Have a look at https://llmvlt.dev…”
- 2026-06-09 · kukkeliskuu · [item 48456905](https://news.ycombinator.com/item?id=48456905) · _Ask HN: What are tools you have made for yourself since the_ — “Many, recently: / - I coded myself a portfolio manager to manage all the projects that I have / - secrets management tool to avoid accidental leaks of tokens by AIs / - t…”
- 2026-04-24 · wfinigan · [item 47890495](https://news.ycombinator.com/item?id=47890495) · _Show HN: Agent Vault – Open-source credential proxy and vaul_ — “Love this. Our team has been frustrated that nothing like this exists. You run into this problem as soon as you start thinking seriously about capable cloud agents, but t…”
- 2026-04-24 · 10keane · [item 47886582](https://news.ycombinator.com/item?id=47886582) · _Show HN: Agent Vault – Open-source credential proxy and vaul_ — “been thinking about this exact problem for a while. my own setup uses OS keyring with a ‹secret:name› token substitution pattern — the agent requests a credential by name…”
- 2026-04-22 · dangtony98 · [item 47865822](https://news.ycombinator.com/item?id=47865822) · _Show HN: Agent Vault – Open-source credential proxy and vaul_ — “Hey HN! Today we're launching Agent Vault - an open source HTTP credential proxy and vault for AI agents. Repo is at https://github.com/Infisical/agent-vault, and there's…”

### C. Rescuing AI-built apps (Supabase RLS, auth, Stripe webhooks, deploy) - paid to freelancers — 18 items, 18 distinct authors, 7 dated Aug–Oct 2026

- 2026-10-12 · Andler · [item 50050342](https://news.ycombinator.com/item?id=50050342) · _Ask HN: Who wants to be hired? (October 2026)_ — “Location: Burgas, Bulgaria / Remote: Yes / Willing to relocate: Yes / Technologies: Supabase, PostgreSQL row-level security, Stripe webhooks, TypeScript/Deno edge functio…”
- 2026-10-10 · altmanaltman · [item 50028432](https://news.ycombinator.com/item?id=50028432) · _Should I Hire a Dev or Can I Vibecode This?_ — “Meant for non-technical users who are building their own things (a lot these days) to understand if their current big idea is safe to vibecode and if its worth it to hire…”
- 2026-10-01 · FlowLabDev · [item 49926217](https://news.ycombinator.com/item?id=49926217) · _Ask HN: Who wants to be hired? (October 2026)_ — “Location: Remote / Remote: Yes / Willing to relocate: No / Technologies: React, TypeScript, Next.js, Supabase, PostgreSQL, Node.js, Python, n8n, Make, Zapier, WordPress,…”
- 2026-08-27 · tornadorice · [item 49468226](https://news.ycombinator.com/item?id=49468226) · _(dead)_ — “Hey guys, / Recently I started noticing the same problem with a lot of my friends who are building apps with tools like Lovable and Supabase. They build something quickly…”
- 2026-08-21 · waterTanuki · [item 49382893](https://news.ycombinator.com/item?id=49382893) · _The Citizen Developer_ — “New person in sales joined my company a few months ago and on the very first introduction they handed me a vibe coded app and asked me to review it for them and put it in…”
- 2026-08-13 · allthetime · [item 49288290](https://news.ycombinator.com/item?id=49288290) · _Lovable raises $400M Series C_ — “I recently consulted for a vibe-founder who built yet-another ai voice chat and what shocked me about lovable was the lock-in. The supabase backend is completely inaccess…”
- 2026-08-03 · Orangecat2026 · [item 49156706](https://news.ycombinator.com/item?id=49156706) · _Ask HN: Who wants to be hired? (August 2026)_ — “Location: Remote (UTC+0) Remote: Yes (only) Willing to relocate: No Technologies: TypeScript, Next.js 15 (App Router), React, Supabase/PostgreSQL + RLS, Stripe (webhooks,…”
- 2026-07-11 · jwpapi · [item 48873320](https://news.ycombinator.com/item?id=48873320) · _Write code like a human will maintain it_ — “I generally like refactoring too, like cleaning up at home, but if you open up a codebase that has been vibecoded and it seems like it’s a never-ending chain of bad pract…”
- 2026-07-03 · jazz3k · [item 48780877](https://news.ycombinator.com/item?id=48780877) · _Ask HN: Is anyone experimenting with different ways of using_ — “I'm in offensive security and use it to write exploit code for various projects I'm working on. / Too many people are using LLMs to shortcut knowledge completely. I have…”
- 2026-07-01 · jensrusi · [item 48748389](https://news.ycombinator.com/item?id=48748389) · _Ask HN: Who wants to be hired? (July 2026)_ — “Munich, Germany | Remote (CET, overlaps US mornings) | Freelance / contract only, not seeking employment / 20+ years across product, UX and frontend, now doing user-facin…”
- 2026-06-07 · ethagnawl · [item 48436232](https://news.ycombinator.com/item?id=48436232) · _LLMs are eroding my software engineering career and I don't_ — “› It's horrible to be a software dev right now, you've to deal with AI and lunatics. / Yes, yes, 1000x yes. / As a bit of an aside, I have been toying with the idea of ad…”
- 2026-06-07 · slyzmud · [item 48434278](https://news.ycombinator.com/item?id=48434278) · _I design with Claude more than Figma now_ — “I've working on a small side project with a non technical friend for a couple months. It's really small but we are selling it to some clients. / The other day my friend d…”
- 2026-06-06 · tobyhinloopen · [item 48421713](https://news.ycombinator.com/item?id=48421713) · _Ask HN: What was your "oh shit" moment with GenAI?_ — “A non-technical employee of a client vibe-coded an app and I was asked to review and deploy it. / It was okay, not bad at all. No serious issues. / At the same time, me f…”
- 2026-06-03 · kieranlenton54 · [item 48388928](https://news.ycombinator.com/item?id=48388928) · _Ask HN: Who wants to be hired? (June 2026)_ — “Location: United Kingdom Remote: Yes (GMT) Willing to relocate: No Technologies: JavaScript/React, Supabase, Firebase, Stripe, Netlify / Available for freelance/contract…”
- 2026-05-25 · CharlieDigital · [item 48271054](https://news.ycombinator.com/item?id=48271054) · _Building Pi with Pi_ — “A story to share: friend vibe coded absolute slop with Replit starting late 2024 (!!). Absolute trash code. Hacked multiple times because his login code exposed the full…”
- 2026-05-22 · fathermarz · [item 48242805](https://news.ycombinator.com/item?id=48242805) · _AI has a multiplying effect on existing technical skills_ — “100% could not agree more. Was hired to fix a vibe coded app for a company that one of their people whipped up over five months. Tens of thousands of lines of code in a s…”
- 2026-05-17 · moron4hire · [item 48170241](https://news.ycombinator.com/item?id=48170241) · _I don't think AI will make your processes go faster_ — “Same, exact experience here. / This one non-technical PM guy at work used Codex to develop a project I was expecting would fall on my plate. He asked me to do a code revi…”
- 2026-04-19 · kay_o · [item 47828077](https://news.ycombinator.com/item?id=47828077) · _Vercel April 2026 security incident_ — “› start building the same generated code with the same vulnerability / This situation is pretty funny to me. Some of my friends who arent technical tried vibe coding and…”

### D. Supervising agents away from the desk (needs-input alerts, phone approval, persistent sessions, keep-awake) — 38 items, 36 distinct authors, 22 dated Aug–Oct 2026

- 2026-10-14 · afruitpie · [item 50095797](https://news.ycombinator.com/item?id=50095797) · _OpenCode 2.0_ — “Native apps connecting to the OpenCode server is a great way to run sessions on remote hosts! / I wish Claude Code would adopt the same model. The desktop app deploys a s…”
- 2026-10-13 · josefchen · [item 50074942](https://news.ycombinator.com/item?id=50074942) · _Show HN: Muster, a Mac Menu Bar Switcher for Claude Code, Co_ — “Hey HN - I use quite a few coding agents (Claude Code, Codex, Cursor, ...) and often several of them concurrently, so it can be hard to keep track of which agent is waiti…”
- 2026-10-12 · flurly · [item 50063147](https://news.ycombinator.com/item?id=50063147) · _Show HN: Runway.sh – one place to access all your machines,_ — “the networking is very similar to tailscale, but the main use case is being able to spin up coding agents across your machines from a website. for example, i love being a…”
- 2026-10-10 · toppa33 · [item 50028853](https://news.ycombinator.com/item?id=50028853) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Don’t miss the nap trap days but glad you found a useful way to be productive. I ran into a similar issue and built something free & open source. Not on the App Store yet…”
- 2026-10-09 · joshstrange · [item 50022438](https://news.ycombinator.com/item?id=50022438) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “If you are in the Herdr ecosystem and the iOS ecosystem I highly recommend Heeler: https://github.com/ZingerLittleBee/Heeler…”
- 2026-10-09 · lukeed · [item 50016283](https://news.ycombinator.com/item?id=50016283) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Zero, as far as I can tell. Maybe there will be a few by the end of the 14d window. Developers are a stubborn/interesting target group -- I bet there will be more built-i…”
- 2026-10-09 · amber71de · [item 50015771](https://news.ycombinator.com/item?id=50015771) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Of the trials started so far, how many have bought at $99?…”
- 2026-10-09 · antoniomika · [item 50014638](https://news.ycombinator.com/item?id=50014638) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Was looking for something like this but stumbled upon herdr-web-ui (0) first. They seem to do the same thing, but herdr-web-ui is completely free and self hosted and sets…”
- 2026-10-09 · sailfast · [item 50014471](https://news.ycombinator.com/item?id=50014471) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Nice! I did something like this running tailscale to my laptop with a TUI and it worked well for awhile. And then I realized I didn't want to be notified when my agents w…”
- 2026-10-08 · worldisaduck · [item 50013229](https://news.ycombinator.com/item?id=50013229) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “right after connecting to my workstation it says: “herdr is not installed on this host” while it clearly is. Running it in shell directly works, but it’s impossible to sc…”
- 2026-10-08 · lukeed · [item 50009634](https://news.ycombinator.com/item?id=50009634) · _Show HN: Pocketty – iPhone SSH terminal that pings you when_ — “Hello~! pocketty is an SSH terminal for iPhone and iPad, made for herdr. herdr keeps your agent panes alive on your computer and knows the state of each one: working, nee…”
- 2026-10-06 · mynegation · [item 49985469](https://news.ycombinator.com/item?id=49985469) · _Berthd_ — “On the claude side, it periodically signs me out, breaking the session. Yes, I can ssh and reconnect but why? You can use a long-lived token but you are not allowed to ru…”
- 2026-10-03 · imbobbytables · [item 49946818](https://news.ycombinator.com/item?id=49946818) · _Show HN: Valet – Self-Hosted Cloud Agents with Computers_ — “Hi HN, I built Valet because Cursor Cloud Agents and Amp Orbs are the coolest things I've ever seen, but they cost money. And Codex Remote/Claude Remote Control isn't goo…”
- 2026-09-14 · yashness · [item 49692659](https://news.ycombinator.com/item?id=49692659) · _Ask HN: What are you working on? (September 2026)_ — “Push notifications for AI agents, but better. It eliminates baby sitting terminals & let's you go out & approve key decisions while you're also notified of the proof of w…”
- 2026-09-10 · kyxsc · [item 49650979](https://news.ycombinator.com/item?id=49650979) · _OpenAI Agents API_ — “Yep I run 'claude remote-control' as daemons (systemd/launchctl) on whatever paths/repos I wanna be able to create a session from on-to-go. / Works really well and is a g…”
- 2026-09-09 · theptip · [item 49619628](https://news.ycombinator.com/item?id=49619628) · _Connecting the machines_ — “Codex and Claude mobile apps are finally quite usable in the last month or two, it’s been a long time that the experience has been janky. / You finally don’t need to do t…”
- 2026-09-01 · jonchurch_ · [item 49516652](https://news.ycombinator.com/item?id=49516652) · _Apple caught off guard by AI demand for Mac Mini and Mac Stu_ — “caffeinate -is -t 7200 claude --remote-control / then Control + Command + Q ftw / (keep system from sleeping if plugged in, keep system from going idle even if not plugge…”
- 2026-08-31 · spacedcowboy · [item 49509801](https://news.ycombinator.com/item?id=49509801) · _Apple caught off guard by AI demand for Mac Mini and Mac Stu_ — “I was getting semi-useful results from a 128GB M4 Max. That was a few months ago, and the models have improved (quite a bit) since then, but now I'm happy to send my $20/…”
- 2026-08-17 · monkpit · [item 49335823](https://news.ycombinator.com/item?id=49335823) · _Show HN: Saggar, a Mac terminal that keeps sessions and your_ — “Ok! This is a killer feature / a must for me. I can use Claude code’s remote control, but I can’t do that across my multiple accounts. So having the ability to manage any…”
- 2026-08-10 · resonious · [item 49239244](https://news.ycombinator.com/item?id=49239244) · _OpenChamber: An Agentic Development Environment_ — “Not surprised at all but there seems to be tons of these kinds of tools and I'm having a hard time picking one. Is there a nice list somewhere? I guess I can ask chatgpt.…”
- 2026-08-03 · thepoet · [item 49159465](https://news.ycombinator.com/item?id=49159465) · _Devtools must be open source_ — “A bit idealistic for the crowd here but has some good points. / The other day I wanted to build personal apps for my Kobo device. It has a single ~800Mhz core and 512 MB…”
- 2026-08-01 · Adam-Hincu · [item 49129872](https://news.ycombinator.com/item?id=49129872) · _I made a free web app that prevents your screen from turning_ — “I always have background tasks running, whether it’s Cursor, Codex or Claude Code programming in the background, a download, an upload, or something else. The problem was…”
- 2026-07-29 · sebderhy · [item 49097326](https://news.ycombinator.com/item?id=49097326) · _ShellTeam – web app to steer coding agents on your VPS_ — “Hey HN. Like many others, I'm running my coding agents almost exclusively on my VPS. But I got tired of the terminal as the interface: I tried Termius on my phone but it…”
- 2026-07-11 · cwbuilds · [item 48871462](https://news.ycombinator.com/item?id=48871462) · _Show HN: Abralo – Free, easy way to run several Claude Code_ — “Yeah, I have used that and it's pretty good. For me, keeping up with multiple Claude Code agents got pretty annoying (hard to see which need your attention etc) so I felt…”
- 2026-07-09 · treefry · [item 48840499](https://news.ycombinator.com/item?id=48840499) · _I think I have LLM burnout_ — “From my experience, there are mainly 3 burnout reasons. 1. Multi-tasking is the top one. I usually have to frequently switch between 3 to 5 agent windows which are on dif…”
- 2026-07-08 · xbryanx · [item 48833031](https://news.ycombinator.com/item?id=48833031) · _Herdr: One terminal to rule them all_ — “I wish Claude's remote control sessions were longer running. If I forget about a conversation it's been cognitively difficult for me to track down which tmux tab = the co…”
- 2026-07-03 · m_ke · [item 48779953](https://news.ycombinator.com/item?id=48779953) · _Ask HN: Is anyone experimenting with different ways of using_ — “I mostly use claude code on mobile and desktop with remote sessions and do most of my coding on the go now. / I have been tempted to distill something like GLM 5.2 into a…”
- 2026-06-29 · kerlenton · [item 48718754](https://news.ycombinator.com/item?id=48718754) · _Herdr: Agent multiplexer that lives in your terminal_ — “Multiplexing the agents is clearly the first obvious pain point, but the other one I keep encountering after this is visibility: with multiple agents running, it becomes…”
- 2026-06-25 · zaptheimpaler · [item 48679265](https://news.ycombinator.com/item?id=48679265) · _OAuth for all_ — “Yeah I was doing some similar stuff. I think I tried copying the auth file for codex or claude and even that didn't work - the tokens were somehow tied to some machine id…”
- 2026-06-18 · joshstrange · [item 48591502](https://news.ycombinator.com/item?id=48591502) · _Migrate from OpenClaw_ — “I've tried Nanoclaw and Openclaw and I found them both to be steaming piles of crap. Both of them broke in record time (less than about 1 week). And yes, I tried OpenClaw…”
- 2026-06-09 · alexghr · [item 48460034](https://news.ycombinator.com/item?id=48460034) · _Ask HN: What are tools you have made for yourself since the_ — “I've built a stacked-PR tool for myself, it's just a simple wrapper around git commands. State stored locally in .git/config - https://github.com/alexghr/graphene / Lots…”
- 2026-06-09 · fluder_tw · [item 48458326](https://news.ycombinator.com/item?id=48458326) · _Ask HN: What are tools you have made for yourself since the_ — “I made mobile friendly agentic driven IDE (as a PWA), where I can start "agent" processes on my different laptops (company, personal) or on the dedicated server and manag…”
- 2026-06-09 · zacfire · [item 48456620](https://news.ycombinator.com/item?id=48456620) · _Ask HN: What are tools you have made for yourself since the_ — “Here are a few small tools I built: / Tubenote, a free YouTube video summarization extension. Mangata, a walking app that makes it easy to take notes and photos while wal…”
- 2026-06-09 · switchbak · [item 48454295](https://news.ycombinator.com/item?id=48454295) · _Ask HN: What are tools you have made for yourself since the_ — “I wired up a stream deck to perform long-running tasks. Very much tailored to the kind of HCI that I prefer, so I can be interrupt driven versus checking on status all th…”
- 2026-06-08 · d0ublespeak · [item 48452717](https://news.ycombinator.com/item?id=48452717) · _Ask HN: What are tools you have made for yourself since the_ — “Heaps, most recent is just a little applet that stops my Mac from going to sleep with the lid closed: https://transitivedev.gumroad.com/l/doppio-app / Bunch of security t…”
- 2026-05-06 · adampac · [item 48035909](https://news.ycombinator.com/item?id=48035909) · _A desktop made for one_ — “Would love to learn more about your setup as I put something fairly similar for myself and looking for ways to improve it even further. / My goal is to have agents work i…”
- 2026-05-04 · furyofantares · [item 48004115](https://news.ycombinator.com/item?id=48004115) · _A desktop made for one_ — “I've got a wrapper around tmux for an audience of one. I can operate claude code, codex, opencode, or just a shell, from any of my devices to any of my devices (via tails…”
- 2026-04-25 · ericksnetwork · [item 47901927](https://news.ycombinator.com/item?id=47901927) · _Show HN: MultiTable – I built a dashboard so I could vibe-co_ — “Author here. I built MultiTable because I kept losing context running Claude Code, Codex, and a bunch of dev servers in parallel — six tmux panes, missed permission promp…”

### E. Surprise bills and the demand for hard budget caps — 22 items, 22 distinct authors, 20 dated Aug–Oct 2026

- 2026-10-08 · kvakvs · [item 50011018](https://news.ycombinator.com/item?id=50011018) · _Serverless Horrors $10,811.41_ — “Use fixed price hosting resources, those cannot bite you and if they're too small you can always expand by buying more virtual hosts, or even program your own simple scal…”
- 2026-10-06 · stuaxo · [item 49976377](https://news.ycombinator.com/item?id=49976377) · _We're going to need default hard budget caps on pretty much_ — “Yeah I want the hard budget limit, I absolutely don't want a suprise mega bill and as such stay away from cloud services especially AWS because it's hard to reason about…”
- 2026-10-04 · seviu · [item 49956065](https://news.ycombinator.com/item?id=49956065) · _We're going to need default hard budget caps on pretty much_ — “As somebody developing hobby apps, there are things i just can’t use. Take an example cloudflare workers. I recently worked on a poc for an app. I ended up hosting it at…”
- 2026-10-04 · mybrowsercache · [item 49953454](https://news.ycombinator.com/item?id=49953454) · _We're going to need default hard budget caps on pretty much_ — “My mobile phone contract reduces my speed a lot when the hard limit it reached. I still get some connectivity. What Never happens is that I have to pay extra. If a compan…”
- 2026-10-04 · KronisLV · [item 49952651](https://news.ycombinator.com/item?id=49952651) · _We're going to need default hard budget caps on pretty much_ — “› Generally speaking, it's much better to use alerts instead of hard limit. / Probably for companies and opportunistic individuals with a high risk tolerance. As for me,…”
- 2026-10-04 · andai · [item 49952333](https://news.ycombinator.com/item?id=49952333) · _We're going to need default hard budget caps on pretty much_ — “I call this "blast radius". Earlier this year during the Claw hype I was reading about all kinds of elaborate schemes to prevent the agent from getting API keys. / I real…”
- 2026-10-04 · gozucito · [item 49952146](https://news.ycombinator.com/item?id=49952146) · _We're going to need default hard budget caps on pretty much_ — “Why don't I have the ability to delete my payment details from Codex or Claude? That way I cannot be billed more until my subscription is over. / Turns out it's impossibl…”
- 2026-10-04 · SubiculumCode · [item 49951676](https://news.ycombinator.com/item?id=49951676) · _We're going to need default hard budget caps on pretty much_ — “More than just hard budget caps, we need agents to be aware of those hard budget caps, and plan accordingly. Too much agent behavior is driven by the immediate proximal g…”
- 2026-10-04 · vincentmathis · [item 49951446](https://news.ycombinator.com/item?id=49951446) · _We're going to need default hard budget caps on pretty much_ — “It should definitely be default for all payed APIs. I think every AI provider have this by default. / I've had an AI coding agent enter a doom loop for hours multiple tim…”
- 2026-10-04 · ButlerianJihad · [item 49951247](https://news.ycombinator.com/item?id=49951247) · _We're going to need default hard budget caps on pretty much_ — “As a hobbyist, I pulled completely out of AWS when I realized the billing issues could never be resolved. Even/especially with tight monitoring and hard caps. / Even as a…”
- 2026-10-04 · iambateman · [item 49950313](https://news.ycombinator.com/item?id=49950313) · _We're going to need default hard budget caps on pretty much_ — “I learned this the hard way with OpenAI last week. A key got hacked and a Chinese-language bot used $300 in tokens in an hour. / I had a spending limit on for $30, so why…”
- 2026-10-04 · tkgally · [item 49949759](https://news.ycombinator.com/item?id=49949759) · _We're going to need default hard budget caps on pretty much_ — “› In an ideal world, our agents could help with this. / Not exactly the sort of case Simon has in mind, but I tell Claude to keep to hard daily limits on its OpenRouter s…”
- 2026-10-04 · neom · [item 49949631](https://news.ycombinator.com/item?id=49949631) · _We're going to need default hard budget caps on pretty much_ — “I had an api key set to read only that somehow ran up a $400 bill, I contacted openai about it and never heard back. Not quite the same thing, but still, I find this very…”
- 2026-10-04 · dwattttt · [item 49949361](https://news.ycombinator.com/item?id=49949361) · _We're going to need default hard budget caps on pretty much_ — “This guy only ended up with a ~$6k bill from his agent, not too shabby: https://news.ycombinator.com/item?id=48500012…”
- 2026-10-04 · gausswho · [item 49949353](https://news.ycombinator.com/item?id=49949353) · _We're going to need default hard budget caps on pretty much_ — “I wonder if BigCorp adding spending caps is due to them getting sick of customers solving it for themselves with virtual cards.…”
- 2026-10-04 · lacunary · [item 49949337](https://news.ycombinator.com/item?id=49949337) · _We're going to need default hard budget caps on pretty much_ — “surprise $10k bill is getting off easy…”
- 2026-10-04 · modeless · [item 49949316](https://news.ycombinator.com/item?id=49949316) · _We're going to need default hard budget caps on pretty much_ — “Wait, Google Cloud finally added hard caps on spending per service? I've been wanting that for so many years! They sure took their sweet time. / https://cloud.google.com/…”
- 2026-10-04 · elffjs · [item 49949235](https://news.ycombinator.com/item?id=49949235) · _We're going to need default hard budget caps on pretty much_ — “…”
- 2026-09-09 · tungnt620 · [item 49626462](https://news.ycombinator.com/item?id=49626462) · _Show HN: Deploy unlimited small/medium-size apps with fixed_ — “Hi HN, I built this because I have multiple side projects (thank to AI) and Supabase bill me per projects, I am dont like Vercel as it can give me some surpise bill. / Th…”
- 2026-08-31 · HyperAI · [item 49508497](https://news.ycombinator.com/item?id=49508497) · _OpenClaw 2.0, Accidentally_ — “Convenience always wins until it doesn't. I learned this the hard way — had an API key leak because an agent decided to "helpfully" paste it into a log output. Didn't not…”
- 2026-07-20 · endlessroad1991 · [item 48974911](https://news.ycombinator.com/item?id=48974911) · _An LLM API gateway with budget-limited tokens for your LLM A_ — “(Originally intended as a Show HN post, but my account is not eligible for posting Show HN post yet, so posting as normal content instead.) / Motivation: I have read quit…”
- 2026-04-16 · woodylondon · [item 47795924](https://news.ycombinator.com/item?id=47795924) · _Cloudflare Email Service_ — “I would pay for Cloudflare Workers Paid ($5) in a heartbeat and currently use the free version of cloudflare for all my DNS / Hosting etc. Where it does not meet my needs…”

### F. Usage-limit anxiety and multi-account juggling — 23 items, 23 distinct authors, 11 dated Aug–Oct 2026

- 2026-10-01 · landoncrabtree2 · [item 49926106](https://news.ycombinator.com/item?id=49926106) · _Etymon – Get rid of all your Claude.md, AGENTS.md, cursor/ru_ — “I use a bunch of different harnesses depending on model need, usage limits, harness-specific capabilities, and other factors. I often switch between ClaudeCode for heavy…”
- 2026-09-24 · autorunfun · [item 49831380](https://news.ycombinator.com/item?id=49831380) · _Show HN: Resume Claude Code subagents killed by a usage limi_ — “Author here. This started as a personal annoyance: when my Claude Max window closes mid-task, every subagent that was running dies, and after the reset the orchestrator r…”
- 2026-09-22 · jdprgm · [item 49807535](https://news.ycombinator.com/item?id=49807535) · _GPT-6 Sol and Luna_ — “I wish there was more transparency on the plus plans usage limits showing actual token usage and prices per model that eats away at remaining usage. / Does anyone know ho…”
- 2026-09-22 · apitman · [item 49806451](https://news.ycombinator.com/item?id=49806451) · _GPT-6 Sol and Luna_ — “Since I spent my morning fixing a bug in my OpenAI API proxy that completely broke prompt caching and caused my usage limits to burn like kindling, really happy to see so…”
- 2026-09-22 · rednb · [item 49796526](https://news.ycombinator.com/item?id=49796526) · _MiMo v2.6_ — “› OpenAI reduced prices and Anthropic increased weekly usage limits. / As a Max x20 and Pro x20 subscriber, can tell you that it doesn't matter since they continually mov…”
- 2026-09-13 · ftchd · [item 49689506](https://news.ycombinator.com/item?id=49689506) · _Show HN: Switcheroo – manage logins for 10 CLIs like Vercel,_ — “Hi HN! / As many of you, I have multiple subscriptions to Claude and Codex. It's a daily occurrence for me to use 2-3 accounts for the same conversation. The point for me…”
- 2026-09-01 · hydropax · [item 49516365](https://news.ycombinator.com/item?id=49516365) · _Ask HN: What are your biggest problems and fixes with multis_ — “With grok bot, I've just been giving it a time to stop working; otherwise, it's likely to burn through my entire week's usage in an afternoon. / If I want to run multiple…”
- 2026-08-24 · adastra22 · [item 49416557](https://news.ycombinator.com/item?id=49416557) · _Anthropic's best AI model struggles to attract users as chea_ — “Separate accounts for work and personal projects is ok. Using multiple accounts to bypass usage limits for the same project is explicitly against ToS. / One of Anthropic’…”
- 2026-08-17 · monkpit · [item 49335823](https://news.ycombinator.com/item?id=49335823) · _Show HN: Saggar, a Mac terminal that keeps sessions and your_ — “Ok! This is a killer feature / a must for me. I can use Claude code’s remote control, but I can’t do that across my multiple accounts. So having the ability to manage any…”
- 2026-08-12 · labzink · [item 49272665](https://news.ycombinator.com/item?id=49272665) · _Show HN: Cc-probeline – Claude Code status line with Fable l_ — “Hi HN. I built cc-probeline — a status line for Claude Code. / I kept hitting usage limits in the middle of a task and couldn't figure out where the tokens were going. /…”
- 2026-08-07 · nodja · [item 49215882](https://news.ycombinator.com/item?id=49215882) · _DeepSeek V4 Flash 0731_ — “I'm the same way, I have a very low/sporadic usage of any subscription I've tried. I now just use openrouter with DS4 pro/flash. It also gets rid of usage anxiety where I…”
- 2026-07-30 · carloslfu · [item 49112804](https://news.ycombinator.com/item?id=49112804) · _Show HN: Claude-account – switch Claude Code accounts withou_ — “appreciate you building this! I have two Claude max accounts. The way I do it is that I have two app launchers (claude desktop). I use the desktop app and a different dat…”
- 2026-07-19 · KronisLV · [item 48969555](https://news.ycombinator.com/item?id=48969555) · _OpenAI reduces Codex Model Context Size from 372k to 272k_ — “On long sessions even with workflows and sub-agents I typically hit around 500-750k tokens in context (say 4-16 hours of work in a session, across multiple 5-hour limits)…”
- 2026-07-19 · minimaxir · [item 48963777](https://news.ycombinator.com/item?id=48963777) · _Codex Resets_ — “I really wish there was a canonical platform endpoint to programmatically check Codex usage amount and the quota reset times so I could just vibecode an app to alert "hey…”
- 2026-07-14 · flipdin · [item 48913417](https://news.ycombinator.com/item?id=48913417) · _Anthropic banned my thirteen 20x accounts, what now?_ — “When I had that many subscriptions, I was being very lazy with it. / I do build a lot of automations though that don’t require AI. By that, I mean using AI to create pyth…”
- 2026-07-10 · algoth1 · [item 48857956](https://news.ycombinator.com/item?id=48857956) · _GPT-5.6_ — “A great thing about codex is that, even if run out of usage, it finishes the task. Claude code will abruptly break the work and leave it there unfinished as soon as it ru…”
- 2026-06-20 · 1Kapish · [item 48609047](https://news.ycombinator.com/item?id=48609047) · _(dead)_ — “I use multiple AI tools for work and also my side projects, and the annoying part was to track my costs and token usage across tools. / Everytime I had to visit each tool…”
- 2026-06-16 · richbradshaw · [item 48556651](https://news.ycombinator.com/item?id=48556651) · _Running local models is good now_ — “I’m keen to understand speed here etc etc. if I bought a Mac studio with 96GB - what can I realistically run, how’s it compare to fable/opus etc and how fast is it? / Cur…”
- 2026-06-09 · duggan · [item 48458412](https://news.ycombinator.com/item?id=48458412) · _Ask HN: What are tools you have made for yourself since the_ — “- FileTranscriber, for getting Whisper transcriptions of media files from the context menu on macOS: https://github.com/duggan/filetranscriber / - usagi, for tracking Cla…”
- 2026-06-09 · kodisha · [item 48458182](https://news.ycombinator.com/item?id=48458182) · _Ask HN: What are tools you have made for yourself since the_ — “I was always experimenting with different agents and models, and I wanted to track how much I use eg codex vs opencode vs hermes, and which models I use. / So I made, kin…”
- 2026-05-06 · druskacik · [item 48039087](https://news.ycombinator.com/item?id=48039087) · _Higher usage limits for Claude and a compute deal with Space_ — “For me personally, I have the basic Claude Code subscription that I use to rewind on some evenings or on weekend, to code a bit for 1-2 hours. I have like 3-5 session wit…”
- 2026-04-24 · stan_kirdey · [item 47893458](https://news.ycombinator.com/item?id=47893458) · _I cancelled Claude: Token issues, declining quality, and poo_ — “I also cancelled my subscription.The $20 Pro plan has become completely unusable for any real work. What is especially frustrating is that Claude Chat and Claude Code now…”
- 2026-04-24 · fluidcruft · [item 47892710](https://news.ycombinator.com/item?id=47892710) · _I Cancelled Claude: Token Issues, Declining Quality, and Poo_ — “It sounds like we have very similar usage/projects. codex had been essentially uncapped (via combination of different x-factors between Plus and Pro and promotions) until…”

### G. Every session starts from zero (searchable transcripts, cross-session memory) — 22 items, 22 distinct authors, 12 dated Aug–Oct 2026

- 2026-10-05 · contentkraft · [item 49963220](https://news.ycombinator.com/item?id=49963220) · _Agents don't need memory, they need documentation_ — “I came to the same conclusion and built something to solve this pain point on top of having scoped access and tasks, it’s called (Takibi Base)(https://takibibase.com/), a…”
- 2026-10-01 · igorbark · [item 49926430](https://news.ycombinator.com/item?id=49926430) · _Pi 1.0_ — “the main thing i use it for that seems like a pain with other coding agents is my sandboxing workflow: i have a custom extension which allows the pi process to run on my…”
- 2026-09-25 · KanishkNoir · [item 49851311](https://news.ycombinator.com/item?id=49851311) · _(dead)_ — “I built CogniKernel to give coding agents persistent project memory, but the difficult part turned out not to be storing memories- it was to make them trustworthy. / Sinc…”
- 2026-09-25 · avinashjetwani · [item 49846413](https://news.ycombinator.com/item?id=49846413) · _Jevmem – automatic project memory for Claude Code, built on_ — “jevmem watches Claude Code, Cursor & Codex chats and keeps a JEVMEM.md in your repo up to date. After each message, Jev (TypeSafe) decides whether anything is worth remem…”
- 2026-09-13 · AliAbdoli · [item 49689157](https://news.ycombinator.com/item?id=49689157) · _Ask HN: What are you working on? (September 2026)_ — “Working on https://tenjin.sh/ . It's a knowledge layer for agents so agents stop duplicating work. / Rides Claude Code/Codex hooks and captures useful information, and in…”
- 2026-09-07 · hariprasd · [item 49600470](https://news.ycombinator.com/item?id=49600470) · _Ask HN: Show your micro-SaaS_ — “I made a notepad, which is also a shared memory layers for all of the agents (claude, gpt). So wherever you talk, you're saving important info without efforts. It gets sa…”
- 2026-09-06 · swordsith · [item 49584198](https://news.ycombinator.com/item?id=49584198) · _OKF Agent Memory – Git-native persistent memory for AI codin_ — “Personally I've always seen AI 'memory' as a pain point for people in their experience using LLMs than a benefit from the agent remembering the last unrelated thing you w…”
- 2026-08-21 · fluidcruft · [item 49391724](https://news.ycombinator.com/item?id=49391724) · _Felony Bench_ — “You can disable claude-code's memories both at a repo level and in user settings. I have this in ~/.claude/settings.json / "autoMemoryEnabled": false, (Claude fixed this…”
- 2026-08-21 · luca-ctx · [item 49389642](https://news.ycombinator.com/item?id=49389642) · _ctx 1.0: 'git blame' but for agent sessions_ — “OP here / ctx has reached major stable version 1.0. It's an open-source local CLI for searching your coding agent history. / 1.0 brings several big changes: / - switched…”
- 2026-08-11 · jbo76 · [item 49258046](https://news.ycombinator.com/item?id=49258046) · _Coordinate coding agents and Git worktrees around features_ — “md² gives you more control and allows for better multi-tasking when working with agents. / These are some of the problems I ran into and am trying to solve: / - a new wor…”
- 2026-08-08 · Alifatisk · [item 49225326](https://news.ycombinator.com/item?id=49225326) · _Message your other Claude Code sessions_ — “I wish there was a clean way to compact the conversation into a prompt with all necessary context for a new fresh conversation.…”
- 2026-08-06 · omartelo · [item 49199714](https://news.ycombinator.com/item?id=49199714) · _Show HN: Wallfacer – A terminal session manager for Claude C_ — “Same thing bit me. What fixed it was keeping the session id next to the checkout instead of letting the directory be the key. Small local db, one row per worktree. Resume…”
- 2026-07-31 · rkuska · [item 49120805](https://news.ycombinator.com/item?id=49120805) · _The session you cannot take with you_ — “I am waiting for prices to get down and in the meanwhile I am gathering as much session data from claude/codex as possible so I can then later use them to fine tune open…”
- 2026-07-22 · satoyoshidev · [item 49008483](https://news.ycombinator.com/item?id=49008483) · _Show HN: CodeAlmanac – Karpathy-style codebase wiki from you_ — “Transcripts tend to have secrets pasted into them during debugging, api keys, .env values and so on. Is there anything that keeps the sync agent from writing those into a…”
- 2026-07-19 · kiokuapp · [item 48966917](https://news.ycombinator.com/item?id=48966917) · _(dead)_ — “Hi HN, / I use Claude Code and Cursor every day. Two things kept annoying me. Every new session starts from zero. And the AI keeps suggesting ideas I already said no to m…”
- 2026-07-15 · vshulcz · [item 48923305](https://news.ycombinator.com/item?id=48923305) · _Open-source memory for coding agents, synced over SSH_ — “Hi HN. I built deja after watching Claude Code and Codex debug the same problems more than once. / The annoying thing was that the answer usually already existed somewher…”
- 2026-06-23 · dasubhajit · [item 48649714](https://news.ycombinator.com/item?id=48649714) · _(dead)_ — “agent orchestration will be painful if you still have to babysit context. / at modulus, we’re spending way too much time solving the context problems for coding agents -…”
- 2026-06-09 · cdnsteve · [item 48455577](https://news.ycombinator.com/item?id=48455577) · _Ask HN: What are tools you have made for yourself since the_ — “1. Built an agent memory tool since all agents and clis are dumb and don't remember anything. Instead of prepping 300 project files and Md files I just say: / Check sugar…”
- 2026-06-08 · andrewstuart2 · [item 48450392](https://news.ycombinator.com/item?id=48450392) · _Ask HN: What are tools you have made for yourself since the_ — “Claudhd / It's a user daemon that runs on my machine and exposes a unix socket, and then a bunch of hooks in claude, zsh, vim, etc, that report directory and commands I'v…”
- 2026-05-26 · haoranchg · [item 48283162](https://news.ycombinator.com/item?id=48283162) · _Show HN: Cross-agent messaging and shared memory over the lo_ — “I run an agent fleet of multiple AI run time, including Claude Code/Codex/Cursor/Gemini. At this stage, I do not trust fully autonomy(although I trust 70%~80% of it). Ins…”
- 2026-05-04 · cavino · [item 48012400](https://news.ycombinator.com/item?id=48012400) · _Claude-Find – Pull Deep Memory from Across Your Claude Code_ — “I've been using Claude Code daily for ~1 year now. It's my default LLM interface, not just for coding, but for all types of work. In a given month, I'd have hundreds of s…”
- 2026-04-15 · eru · [item 47775560](https://news.ycombinator.com/item?id=47775560) · _Claude Code Routines_ — “› Claude Code’s "Memory" feature was the tipping point for me, with the model committing feedbacks and learnings to some local, provider-specific path, that won’t persist…”

### H. Keeping CLAUDE.md / AGENTS.md / skills / MCP / hooks in sync across harnesses and machines — 27 items, 27 distinct authors, 20 dated Aug–Oct 2026

- 2026-10-02 · jkl5xx · [item 49930482](https://news.ycombinator.com/item?id=49930482) · _Pi 1.0_ — “Was also wondering this the other day. Every harness I’ve looked into seems to be monolithic. I would really prefer specialized profiles/configurations instead of loading…”
- 2026-10-02 · by2kaapi · [item 49930109](https://news.ycombinator.com/item?id=49930109) · _Pi 1.0_ — “Switched to pi to avoid having to keep skills/MCP configs in sync across agents like claude and codex to have consistent experience. / But loved the minimalism, extensibi…”
- 2026-10-01 · landoncrabtree2 · [item 49926106](https://news.ycombinator.com/item?id=49926106) · _Etymon – Get rid of all your Claude.md, AGENTS.md, cursor/ru_ — “I use a bunch of different harnesses depending on model need, usage limits, harness-specific capabilities, and other factors. I often switch between ClaudeCode for heavy…”
- 2026-09-23 · Chemaclass · [item 49823921](https://news.ycombinator.com/item?id=49823921) · _One setup, every AI CLI with agnostic-AI_ — “Keep agents, skills, rules, hooks, and MCP servers in one portable source. agnostic-ai writes each tool's native files and checks them for drift.…”
- 2026-09-19 · perganomoly · [item 49765432](https://news.ycombinator.com/item?id=49765432) · _Claude Code now reads AGENTS.md if there is no Claude.md_ — “Because I care about products, their communities, and how company’s treat customers. / I was quite annoyed with Claude earlier this year when I had to maintain duplicate…”
- 2026-09-18 · aroman · [item 49760485](https://news.ycombinator.com/item?id=49760485) · _Claude Code now reads AGENTS.md if there is no Claude.md_ — “Finally, I can delete 'sync-agent-docs.sh', which recursively symlinked AGENTS.md to GEMINI.md and CLAUDE.md...…”
- 2026-09-17 · chrismarlow9 · [item 49735206](https://news.ycombinator.com/item?id=49735206) · _OpenSpec – A lightweight and configurable AI spec framework_ — “Symlink the global MD files to a single file I control that is versioned. Define my own general spec and workflow terminology using markdown files in this universal MD. /…”
- 2026-09-09 · alexsmirnov · [item 49629408](https://news.ycombinator.com/item?id=49629408) · _Ask HN: How do you manage skills files?_ — “I did create special repo that has all skills/agents/scripts and MCP configuration. All agents ( currently 3 in use: claude code, opencode, and pi ) packed in docker cont…”
- 2026-09-09 · chachachainsaw · [item 49621514](https://news.ycombinator.com/item?id=49621514) · _Ask HN: How do you manage skills files?_ — “I’ve been keeping all skills in .agents/skills and symlinking .claude/skills, this way I can use them across both claude code and codex. One of the not so straight forwar…”
- 2026-09-07 · yokuze · [item 49601053](https://news.ycombinator.com/item?id=49601053) · _Ask HN: How do you manage skills files?_ — “I commit my standard set of agent configuration (including Skills) to this repo, similar to how many people have a "dotfiles" repo: https://github.com/yokuze/aix-config /…”
- 2026-09-07 · nhod · [item 49599972](https://news.ycombinator.com/item?id=49599972) · _Ask HN: How do you manage skills files?_ — “I've been using a project called SX https://github.com/sleuth-io/sx to manage them. It has its quirks, but overall I find it to be very useful. / One thing I've had to wr…”
- 2026-09-07 · bredren · [item 49599741](https://news.ycombinator.com/item?id=49599741) · _Ask HN: How do you manage skills files?_ — “I use skills all day, every day. One of my greatest annoyances right now is having to switch between '/' and '$' in moving between CC and codex. At one point I attempted…”
- 2026-09-07 · srijanshukla18 · [item 49596283](https://news.ycombinator.com/item?id=49596283) · _Ask HN: How do you manage skills files?_ — “I've got a skill repository on github, and I got a hermes automation to sync skills repo - this hermes automation is on every device. Any skills I make on the fly - my gl…”
- 2026-09-07 · mstr32 · [item 49594219](https://news.ycombinator.com/item?id=49594219) · _Ask HN: How do you manage skills files?_ — “The main problem I encountered around this is that skills need to be edited across projects and across team members in a controlled way. Git is of course required for thi…”
- 2026-09-07 · ssivark · [item 49593732](https://news.ycombinator.com/item?id=49593732) · _Ask HN: How do you manage skills files?_ — “To the extent that skills are contextual guidance (for this author, this project, etc) and not just (raw) capabilities they are unlikely to be eaten by models. / I mainta…”
- 2026-09-06 · joshuanapoli · [item 49592107](https://news.ycombinator.com/item?id=49592107) · _Ask HN: How do you manage skills files?_ — “We have some company-managed skills, that help coding agents find the relationships between our repos, and our conventions, architecture, and other high-level decisions.…”
- 2026-09-06 · jameshiew · [item 49592102](https://news.ycombinator.com/item?id=49592102) · _Ask HN: How do you manage skills files?_ — “I manage them as part of my dotfiles using chezmoi. A '.agents/skills/' directory + a symlink to there from '.claude/skills/'. / › Do you keep improving them over time? /…”
- 2026-09-06 · schipperai · [item 49587840](https://news.ycombinator.com/item?id=49587840) · _Mdmanager.ai – Manage your Claude.md and AGENTS.md across ma_ — “One agent standard that causes me pain: AGENTS.md / CLAUDE.md. / I have multiple machines (personal laptop, work laptop, server) and runtimes (Claude Code, Codex, Pi) whi…”
- 2026-08-20 · kstenerud · [item 49373088](https://news.ycombinator.com/item?id=49373088) · _Feature Request: Support AGENTS.md_ — “For me it's very handy to have agent-specific instructions. Each harness does it differently and with differing levels of annoyance: / - .cursor/rules / - CLAUDE.md / - .…”
- 2026-08-18 · jesserobbins · [item 49350237](https://news.ycombinator.com/item?id=49350237) · _Manage agent loadouts with drskill – "brew doctor for agents_ — “drskill is "brew doctor for your agent's loadout", a CLI that audits the Skills and MCP servers your agents are loading. In can scan up to 34 issue categories like missin…”
- 2026-07-10 · snthpy · [item 48856304](https://news.ycombinator.com/item?id=48856304) · _GPT-5.6_ — “OT but how are y'all sharing your skills and agents across harnesses? / I have a bunch of Claude Code Plugins and yesterday asked Codex to make them accessible to itself.…”
- 2026-06-30 · scottfits · [item 48737315](https://news.ycombinator.com/item?id=48737315) · _Ask HN: How do you share /skills across your dev team?_ — “this is a pain point -- we also have .skill files duplicated across Claude Desktop and our agent's codebase and keeping them in sync is a pain. / I assume it's just somet…”
- 2026-06-30 · bewal416 · [item 48737209](https://news.ycombinator.com/item?id=48737209) · _Ask HN: How do you share /skills across your dev team?_ — “My team wants to adopt a shared set of skills in our codebase: design rules, reusable component references, copy guidelines, etc. Currently, we've kept .claude/skills in…”
- 2026-06-22 · fortuitous-frog · [item 48632844](https://news.ycombinator.com/item?id=48632844) · _Codex logging bug may write TBs to local SSDs_ — “I used to use a symlink but was concerned that Claude might see the presence of an "AGENTS.md" file (in e.g, a "List Files" tool call output or from a direct 'ls'), be cu…”
- 2026-06-08 · sethd · [item 48453939](https://news.ycombinator.com/item?id=48453939) · _Ask HN: What are tools you have made for yourself since the_ — “- https://github.com/sethdeckard/atria : TUI for managing multiple AI coding agents that doesn't force a particular workflow on you. You can use tmux, the built-in PTY, o…”
- 2026-04-22 · JulienZammit · [item 47861545](https://news.ycombinator.com/item?id=47861545) · _Changes in the system prompt between Claude Opus 4.6 and 4.7_ — “The "agent-neutral codebase" framing is the right abstraction. We ended up building a small generator that takes a single spec file and emits the agent-specific config (C…”
- 2026-04-20 · jrvarela56 · [item 47830722](https://news.ycombinator.com/item?id=47830722) · _Changes in the system prompt between Claude Opus 4.6 and 4.7_ — “The past month made me realize I needed to make my codebase usable by other agents. I was mainly using Claude Code. I audited the codebase and identified the points where…”

### I. Getting screenshots and images into terminal agents (especially over SSH) — 17 items, 16 distinct authors, 2 dated Aug–Oct 2026

- 2026-10-13 · wtallis · [item 50065919](https://news.ycombinator.com/item?id=50065919) · _Codex CLI installs a persistent, self-updating background da_ — “Half of what you're listing as features people should be impressed are stuff that causes as much frustration as it solves. The image pasting behavior is a super-annoying…”
- 2026-08-09 · vulture916 · [item 49235682](https://news.ycombinator.com/item?id=49235682) · _OpenChamber: An Agentic Development Environment_ — “Even though all these "ADE"s are mostly the exact same (Superset, T3, Conductor, Paseo,random Reddit-dude,etc.). I'm liking Orca largely because of the built in browser w…”
- 2026-07-29 · sebderhy · [item 49097326](https://news.ycombinator.com/item?id=49097326) · _ShellTeam – web app to steer coding agents on your VPS_ — “Hey HN. Like many others, I'm running my coding agents almost exclusively on my VPS. But I got tired of the terminal as the interface: I tried Termius on my phone but it…”
- 2026-07-16 · brothaakhee · [item 48936308](https://news.ycombinator.com/item?id=48936308) · _SnippAI – Screenshot, speak, straight into your Claude Code_ — “Hey HN, / So as I'm pair-programming (vibe coding?) with Claude all day, usually with a browser open next to the terminal, every time I spotted a UI bug the routine was t…”
- 2026-07-08 · posterity · [item 48838010](https://news.ycombinator.com/item?id=48838010) · _Ask HN: Make good open-source products, but how to get user?_ — “You might be making the classic builder mistake when pitching if I'm reading your landing page correctly / "Translate What You See To What Your Agent Needs" is not a job…”
- 2026-07-08 · Loerei · [item 48834908](https://news.ycombinator.com/item?id=48834908) · _Show HN: Hover over your UI element to get its exact locatio_ — “I found that describing where a broken UI is and taking screenshots for AI agents really sucks. I’m too lazy to explain an indescribable visual bug or capture a milliseco…”
- 2026-07-08 · xbryanx · [item 48833031](https://news.ycombinator.com/item?id=48833031) · _Herdr: One terminal to rule them all_ — “I wish Claude's remote control sessions were longer running. If I forget about a conversation it's been cognitively difficult for me to track down which tmux tab = the co…”
- 2026-06-18 · andan02 · [item 48588204](https://news.ycombinator.com/item?id=48588204) · _Hotshot – tool to make screenshot –› Claude/copilot/goose fa_ — “hotshot is a tiny macOS menu bar app that captures a screenshot and automatically pastes the file path into whichever terminal session you were last using. Built for AI c…”
- 2026-06-09 · mgranados · [item 48461235](https://news.ycombinator.com/item?id=48461235) · _Ask HN: What are tools you have made for yourself since the_ — “Not really a tool but converted a hobby swift app to a webUI animated showing mexico city and london when there's rain https://tlaloc.cloud/ / The one tool i noticed coul…”
- 2026-06-09 · Adrig · [item 48458253](https://news.ycombinator.com/item?id=48458253) · _Ask HN: What are tools you have made for yourself since the_ — “- A HTML prototyping skill and a simple upload web app to share it privately with my team / - A Chrome extension to make design comments and ASCII wireframes right on the…”
- 2026-06-08 · ozten · [item 48452974](https://news.ycombinator.com/item?id=48452974) · _Ask HN: What are tools you have made for yourself since the_ — “Too many to mention. Daily drivers: replacements for CapCut, Granola. / A remote image viewer to see screenshots in VMs. / A simple agent harness to drive spec to verific…”
- 2026-06-08 · ozaark · [item 48452810](https://news.ycombinator.com/item?id=48452810) · _Ask HN: What are tools you have made for yourself since the_ — “I've been building a tool aimed at better web annotations for teams and AI collaboration at https://viewall.io/ / Having worked with web facing teams there are always vas…”
- 2026-05-28 · kstenerud · [item 48305089](https://news.ycombinator.com/item?id=48305089) · _Why Ctrl+V won't paste images in Claude Code on WSL, with a_ — “I've actually never tried it before. I just ran some tests now on a mac: / If I copy a file in Finder and paste it into a claude session, it shows in the TUI as (Image #1…”
- 2026-05-28 · benjamincburns · [item 48304976](https://news.ycombinator.com/item?id=48304976) · _Why Ctrl+V won't paste images in Claude Code on WSL, with a_ — “But can you paste an image into it? / I have a similar setup, but I access it directly via iTerm2 instead of VS Code's terminal. I've figured out the right terminal setti…”
- 2026-05-22 · Guillaume86 · [item 48242236](https://news.ycombinator.com/item?id=48242236) · _DeepSeek makes the V4 Pro price discount permanent_ — “Yes I'm also using it for coding: I often make the agent use WebSearch in the research phase when deciding on a stack or a library or research best/modern practices to do…”
- 2026-05-01 · arihantsethia · [item 47977572](https://news.ycombinator.com/item?id=47977572) · _Clipport – paste screenshots into SSH sessions from iTerm_ — “clipport is for one narrow loop: agent or script is running over SSH UI state is visible on the Mac screenshot needs to get back into the remote shell Today that is usual…”
- 2026-04-30 · arihantsethia · [item 47964971](https://news.ycombinator.com/item?id=47964971) · _clipboard – paste screenshots into SSH sessions from iTerm_ — “warpboard is for one narrow loop: agent or script is running over SSH UI state is visible on the Mac screenshot needs to get back into the remote shell / Today that is us…”

### J. Verifying agent output (fake tests, CI polling, 'says done but isn't') — 15 items, 15 distinct authors, 9 dated Aug–Oct 2026

- 2026-10-13 · mrwoof · [item 50065174](https://news.ycombinator.com/item?id=50065174) · _Refute, Don't Review_ — “Michael, the post author here. I build Cmd+Ctrl, a unified mobile app for all the AI coding agents. / I typically run a single orchestrator agent across 10–15 parallel wo…”
- 2026-09-28 · klardotsh · [item 49883966](https://news.ycombinator.com/item?id=49883966) · _Sonnet 5.5_ — “The thing with watching CI in an agent loop is that it burns tons of tokens. At work I ended up writing a deterministic, traditional CLI tool to poll GitLab CI pipeline+j…”
- 2026-09-27 · RaysonTech · [item 49863043](https://news.ycombinator.com/item?id=49863043) · _Nom Army: Don't trust coding agents when they say they're do_ — “I’ve been using multiple coding agents across real projects and kept running into a problem that bothered me more than model selection or orchestration: / Coding agents a…”
- 2026-09-08 · andai · [item 49609144](https://news.ycombinator.com/item?id=49609144) · _How well do agents use test/verification techniques?_ — “I asked Sonnet to port a prolog interpreter from Python to JS. I was surprised and delighted that it ended up writing a test suite for it. All tests passed. / Until... I…”
- 2026-08-21 · fabianlindfors · [item 49394427](https://news.ycombinator.com/item?id=49394427) · _Building an (almost) fully self-hosted, sandboxed, agentic s_ — “Agreed, we had agents writing standard integration/unit/e2e tests but turned out to be a ton of work reviewing just that and hard to wrap one’s head around as a developer…”
- 2026-08-15 · alekstret · [item 49309410](https://news.ycombinator.com/item?id=49309410) · _Ask HN: How do you go from writing code to deploying with ag_ — “Most of the time it works as you said, but I implemented one rule that fixed these issues for me: my agent doesn't count a test until it has watched it fail. / The proces…”
- 2026-08-10 · kojeovo · [item 49244384](https://news.ycombinator.com/item?id=49244384) · _Ask HN: How do you go from writing code to deploying with ag_ — “do you read the code and test code? how do you know that the tests are any good? in my experience a lot of the time it will just mock the expected outcome and then it pas…”
- 2026-08-09 · UncleEntity · [item 49227924](https://news.ycombinator.com/item?id=49227924) · _Ask HN: How do you go from writing code to deploying with ag_ — “Yeah, that only works if they follow the plan (they don't), actually write the tests first (they don't) and don't silently defer anything which doesn't have a test writte…”
- 2026-08-08 · sakuraiben · [item 49227024](https://news.ycombinator.com/item?id=49227024) · _Ask HN: How do you go from writing code to deploying with ag_ — “Been doing hardcode agent driven coding for the past year. I feel like I now have to test all my code locally with agents reviewing them and ideally testing them. Unfortu…”
- 2026-07-31 · jhgaylor · [item 49125075](https://news.ycombinator.com/item?id=49125075) · _Agent Sandbox: A Kubernetes CRD and controller for AI agent_ — “My agents need three verbs to help me write code: plan, implement, verify. Planning happens locally with the model and my issue tracker. Implementing happens across a fle…”
- 2026-07-11 · ruslan_qm · [item 48869740](https://news.ycombinator.com/item?id=48869740) · _9lives – Self-healing test runner that refuses to mask real_ — “I built 9lives after realizing that coding agents often break Playwright tests in the most frustrating ways: an agent renames a button, the test turns red, and then eithe…”
- 2026-06-09 · wizenheimer · [item 48454421](https://news.ycombinator.com/item?id=48454421) · _Ask HN: What are tools you have made for yourself since the_ — “I shipped a QA harness for Claude Code. Instead of clicking through flows by hand, it reads your code diffs, identifies the affected UI flows, and tests them in real brow…”
- 2026-06-08 · chatmasta · [item 48450785](https://news.ycombinator.com/item?id=48450785) · _Launch HN: Intuned (YC S22) – Build and run reliable browser_ — “I’d like to see less focus on Playwright and more focus on giving the agent more than just an MCP to browser automation. Make it multi-modal, figure out how to optimize w…”
- 2026-06-04 · priyadarshy · [item 48393055](https://news.ycombinator.com/item?id=48393055) · _Self-hosted dev sandboxes with preview URLs (Docker, Go, no_ — “I think we're all under-indexing on how important it is going to be to be able to play-test an agent's changes before shipping it as a hedge against slop. I don't think p…”
- 2026-04-22 · xdennis · [item 47870263](https://news.ycombinator.com/item?id=47870263) · _Technical, cognitive, and intent debt_ — “I completely agree. This is one of the most annoying things about LLMs. I always see them fixing linter errors by adding ignore comments, typing many things as "Any", dup…”

### K. Claude Code terminal papercuts (copy/paste, line breaks, flicker) — 10 items, 10 distinct authors, 2 dated Aug–Oct 2026

- 2026-08-29 · jolmg · [item 49491191](https://news.ycombinator.com/item?id=49491191) · _GUIs should be fully keyboard-driven_ — “› Funny but I struggle with copying anything in most recent TUIs. Fancy padding or multiplexer borders and multiple lines of text? It breaks. Incomplete text in a spreads…”
- 2026-08-27 · hadlock · [item 49470339](https://news.ycombinator.com/item?id=49470339) · _Show HN: Yet another minimal and lightweight terminal multip_ — “I hadn't seen herdr until just now but I built a similar tool with it's own keyboard bindings https://github.com/hadlock/cscope . Claude Code changed some underlying chan…”
- 2026-07-03 · gozucito · [item 48781102](https://news.ycombinator.com/item?id=48781102) · _Ask HN: Is anyone experimenting with different ways of using_ — “2 to 5 tabs in warp. Kinda want to figure out how to properly use iterm+tmux to have the boris cherny experience. already used both but there were issues with tmux with e…”
- 2026-07-01 · bickov · [item 48744475](https://news.ycombinator.com/item?id=48744475) · _Can't copy-paste in Claude Code? "/tui default" and your bac_ — “Says a lot that "how do I copy text out of it" is a solved-by-secret-command problem. Great agent, the terminal UX is held together with /commands…”
- 2026-06-30 · bryanlarsen · [item 48733653](https://news.ycombinator.com/item?id=48733653) · _You shouldn't copy-paste errors into Claude Code_ — “It's clear that Anthropic itself is following this bad advice. Cut and paste is broken in Claude Code -- anything it prints for you to cut and paste is markdown formatted…”
- 2026-06-16 · anon7000 · [item 48562339](https://news.ycombinator.com/item?id=48562339) · _SpaceX to buy Cursor for $60B_ — “I’m very comfortable with the terminal, but let’s be honest. It’s not very good at certain apps. For example, copy/pasting long bits of code or strings into and out of Cl…”
- 2026-06-16 · baq · [item 48558865](https://news.ycombinator.com/item?id=48558865) · _SpaceX to buy Cursor for $60B_ — “the reason to use cursor nowadays isn't the IDE (though it's helpful perhaps once a week), but how it makes running models from multiple providers trivial out of the box.…”
- 2026-06-05 · ashdksnndck · [item 48407755](https://news.ycombinator.com/item?id=48407755) · _When AI Builds Itself: Our progress toward recursive self-im_ — “CLAUDE\_CODE\_NO\_FLICKER=1 / This is a beta feature where Claude code draws the interface on the terminal’s alternate screen buffer like vim or htop. I believe it’s not the…”
- 2026-05-18 · jansan · [item 48185782](https://news.ycombinator.com/item?id=48185782) · _No More JetBrains Products for Me_ — “I have recently thinking about jumping ship, too, but for usability reasons. The Claude Code terminal is quite a desaster. Soft line breaks are copied to clipboard as har…”
- 2026-05-02 · da_ordi_ · [item 47983849](https://news.ycombinator.com/item?id=47983849) · _OpenWarp_ — “I was looking at warp, wave, and a few others, and this is the exact stuff I will need, thanks for sharing. / So when I SSH to remote servers, I would like to bring my ag…”

### L. Sandboxing and approval fatigue (very crowded) — 21 items, 21 distinct authors, 5 dated Aug–Oct 2026

- 2026-09-08 · edf13 · [item 49610009](https://news.ycombinator.com/item?id=49610009) · _Show HN: Grith – syscall-level supervision for AI agents_ — “Hi, / I'm Dan and I staarted building grith AI earlier this year after getting annoyed with constant permission prompts from Claude Code and Codex. / I had previously bui…”
- 2026-08-10 · espadrine · [item 49241156](https://news.ycombinator.com/item?id=49241156) · _Docker Sandboxes – Disposable, isolated sandboxes for AI age_ — “Models start going to extreme, damaging lengths to achieve ambiguous prompts(0). Having good sandboxes is now a must IMO. / But sbx is a bit annoying to use with OpenCode…”
- 2026-08-09 · schipperai · [item 49234565](https://news.ycombinator.com/item?id=49234565) · _Ask HN: What are you working on? (August 2026)_ — “I’m working on “nah” (1) an agent hook guard that blocks catastrophic agent actions like filesystem destruction, secrets exfiltration, and git disasters. / All the agent…”
- 2026-08-07 · sparsesignal · [item 49214825](https://news.ycombinator.com/item?id=49214825) · _Responding to the next frontier of critical cyber capabiliti_ — “› I stress about my agent sandboxes all the time / Same here, so I ended up moving the whole dev environment (editors, agents, containers) inside a hardened QEMU/KVM VM t…”
- 2026-08-06 · dgunay · [item 49200567](https://news.ycombinator.com/item?id=49200567) · _Humans missed 1 in 3 threats approving AI agent commands acr_ — “For me the problems with agent permission prompts are twofold: / 1) I generally have a lot of things where I am okay with the agent calling a specific tool (maybe in cert…”
- 2026-07-30 · petesergeant · [item 49109201](https://news.ycombinator.com/item?id=49109201) · _Agent-Manager: A Tmux TUI for Running Claude Code, Codex and_ — ““How does this differ from”… / For all of these tools, now, there are many. After I built my own agent sandboxer(0) I went so far as to create a site dedicated to 36 othe…”
- 2026-07-13 · nzoschke · [item 48899958](https://news.ycombinator.com/item?id=48899958) · _Grok CLI uploaded the whole home directory to GCS_ — “The home directory is the scariest thing to me. The agent needs the code to code, but it doesn't need your personal files or secrets. / Personally I'm not worried about s…”
- 2026-07-08 · laurencoral · [item 48830666](https://news.ycombinator.com/item?id=48830666) · _Show HN: IAXT – macOS menu-bar app that records what AI codi_ — “…”
- 2026-07-02 · e1g · [item 48759541](https://news.ycombinator.com/item?id=48759541) · _Ask HN: Secure wrapper for coding agents?_ — “Safehouse author here - glad you found it helpful. It didn't even occur to me to add --offline mode because my mental model is anchored in agents which often require netw…”
- 2026-06-30 · atombender · [item 48737694](https://news.ycombinator.com/item?id=48737694) · _Ask HN: Secure wrapper for coding agents?_ — “Seconding this. I've been running Safehouse for months and love that it can wrap any process (it's just a wrapper around the native macOS sandbox API, after all). The onl…”
- 2026-06-30 · rjzzleep · [item 48732627](https://news.ycombinator.com/item?id=48732627) · _Ask HN: Secure wrapper for coding agents?_ — “I believe someone recently posted sort of a secure harness/wrapper for running coding agents in a secure sandbox. I can't find the project. / Of course I can make my own…”
- 2026-06-09 · brendoncarroll · [item 48461291](https://news.ycombinator.com/item?id=48461291) · _Ask HN: What are tools you have made for yourself since the_ — “No Nonsense Containers: a simple Linux containerization tool, secure by default, with support for presets. / https://github.com/brendoncarroll/nnc / I use it for running…”
- 2026-06-09 · maxk42 · [item 48459023](https://news.ycombinator.com/item?id=48459023) · _Ask HN: What are tools you have made for yourself since the_ — “A year ago I was using claude and found it unexpectedly blowing-away already-settled code. I found this frustrating and just wanted to drop a "save point" where I could c…”
- 2026-06-09 · pkhamre · [item 48457431](https://news.ycombinator.com/item?id=48457431) · _Ask HN: What are tools you have made for yourself since the_ — “This is my daily driver, a security-hardened Docker-image with OpenCode to run the coding agent in an isolated environment. / https://github.com/pkhamre/opencode-docker /…”
- 2026-06-09 · netcoyote · [item 48456184](https://news.ycombinator.com/item?id=48456184) · _Ask HN: What are tools you have made for yourself since the_ — “Tools I’ve built for myself: / - sandvault https://www.codeofhonor.com/projects/sandvault/ runs agents in a separate macOS user account, hardened with sandbox-exec. It al…”
- 2026-06-08 · mixedbit · [item 48450581](https://news.ycombinator.com/item?id=48450581) · _Ask HN: What are tools you have made for yourself since the_ — “I made a sandbox to productively work with agents while restricting files they can read and write: https://github.com/wrr/drop…”
- 2026-06-08 · agentifysh · [item 48450550](https://news.ycombinator.com/item?id=48450550) · _Ask HN: What are tools you have made for yourself since the_ — “Most of it has been to maximize productivity with AI / 1) Use chatgpt pro from codex cli, opencode, claude etc as you can't get it via API. This has been the biggest boos…”
- 2026-06-08 · kstenerud · [item 48450453](https://news.ycombinator.com/item?id=48450453) · _Ask HN: What are tools you have made for yourself since the_ — “I made a tool that creates sandboxes (docker, podman, orbstack, seatbelt, tart, containerd, kata, firecracker) and then sets up an agent (claude, codex, gemini, aider, op…”
- 2026-05-06 · skeledrew · [item 48040003](https://news.ycombinator.com/item?id=48040003) · _Show HN: Tilde.run – Agent sandbox with a transactional, ver_ — “I made something pretty similar to this a couple months ago, when I was just getting into using coding agents. Has 2 parts that work individually but are better together:…”
- 2026-05-05 · Finbarr · [item 48025040](https://news.ycombinator.com/item?id=48025040) · _Treat your coding agents like developers_ — “Author here. Three months ago I posted a Show HN for yolobox (1) - a sandbox for running AI coding agents without them being able to nuke your home directory. / Since the…”
- 2026-04-23 · chiedo · [item 47874972](https://news.ycombinator.com/item?id=47874972) · _Permission Slip – Self-hostable approval layer for destructi_ — “Permission Slip is an open-source approval layer that sits between an AI agent and your accounts (I built it for Openclaw, but works with Claude code local, etc) / You co…”

### M. Shipping Mac software: signing, notarization, Gatekeeper — 13 items, 13 distinct authors, 0 dated Aug–Oct 2026

- 2026-05-18 · ashwani1242 · [item 48184244](https://news.ycombinator.com/item?id=48184244) · _Distributing Mac software is increasing my cortisol levels_ — “I just went through this with a small paid macOS menu bar app. The hardest part was not the code, it was figuring out which app store rules I had accidentally stepped on-…”
- 2026-05-10 · johnofthesea · [item 48083182](https://news.ycombinator.com/item?id=48083182) · _Distributing Mac software is increasing my cortisol levels_ — “I just wish Homebrew was not planning to remove packages because of this. / › $ brew doctor / › Warning: Some installed casks are deprecated or disabled. You should find…”
- 2026-05-10 · kokada · [item 48082393](https://news.ycombinator.com/item?id=48082393) · _Distributing Mac software is increasing my cortisol levels_ — “› but then, like, what do you actually want? / As an author of some homebrewed Go software in the past and trying to distribute in all 3 big OSes, I completely understand…”
- 2026-05-10 · mixologic · [item 48080690](https://news.ycombinator.com/item?id=48080690) · _Distributing Mac software is increasing my cortisol levels_ — “Theres two different steps, there is signing and there is notarization. You sign with the developer certificate using productsign/codesign, and then there is notarization…”
- 2026-05-09 · chr15m · [item 48079529](https://news.ycombinator.com/item?id=48079529) · _Distributing Mac software is increasing my cortisol levels_ — “› what do you actually want? / To make gatekeeper happy without paying a large amount of money and own Apple hardware (same thing).…”
- 2026-05-09 · newman314 · [item 48079399](https://news.ycombinator.com/item?id=48079399) · _Distributing Mac software is increasing my cortisol levels_ — “I do not think this is the right way. The right way would be for Apple to allow for a free Developer ID for distribution if the app is free and has no in-app purchases. /…”
- 2026-05-09 · tclancy · [item 48078466](https://news.ycombinator.com/item?id=48078466) · _Distributing Mac software is increasing my cortisol levels_ — “Don't be fair. I finally signed up for an Apple Developer Account and it took weeks and I think it took weeks because I finally decided the system wasn't accepting my Dri…”
- 2026-05-09 · jedberg · [item 48078155](https://news.ycombinator.com/item?id=48078155) · _Distributing Mac software is increasing my cortisol levels_ — “As a user I actually like Gatekeeper. 95% of the time it's not a problem. the other 5% of the time I have to click a button in my settings to allow unsigned code. But at…”
- 2026-05-09 · LoganDark · [item 48077621](https://news.ycombinator.com/item?id=48077621) · _Distributing Mac software is increasing my cortisol levels_ — “Apple's ID verification failed for me and I am now banned for life. There is no opportunity to appeal this or to ever participate in the Developer Program for me. Which s…”
- 2026-05-09 · drcongo · [item 48077568](https://news.ycombinator.com/item?id=48077568) · _Distributing Mac software is increasing my cortisol levels_ — “I went through this recently. Got as far as verifying my identity, which Apple happily accepted as verified from my UK driving license. Unfortunately, they then automatic…”
- 2026-05-09 · ryandrake · [item 48077524](https://news.ycombinator.com/item?id=48077524) · _Distributing Mac software is increasing my cortisol levels_ — “10 seconds or 30 seconds, it's just too much friction to ask end users to do. I actually develop on a Mac, but I've written off Apple as a target system for hobby/open so…”
- 2026-05-09 · novafunc · [item 48077436](https://news.ycombinator.com/item?id=48077436) · _Distributing Mac software is increasing my cortisol levels_ — “Rather than just having the options "Done" and "Move to Bin", give me an option to actually run it without having to manually go into System Settings each and every time…”
- 2026-05-09 · LorenDB · [item 48075366](https://news.ycombinator.com/item?id=48075366) · _Distributing Mac software is increasing my cortisol levels_ — “…”

### N. Freelancer time tracking and invoicing churn (Harvest price hike) — 13 items, 13 distinct authors, 7 dated Aug–Oct 2026

- 2026-09-02 · Normal_gaussian · [item 49543571](https://news.ycombinator.com/item?id=49543571) · _Show HN: OwnTime – a chess clock for your day's priorities_ — “This is a great (and tight) execution of a neat concept. I'm not in the garden of Apple so unfortunately I can't play with it, but the preview is thorough. I particularly…”
- 2026-08-20 · SyneRyder · [item 49376164](https://news.ycombinator.com/item?id=49376164) · _Harvest hikes bills by 1500% after purchased by Bending Spoo_ — “The small print here is the gotcha: / "Your base rate includes core features. As your team grows, additional invoices, projects, clients, and tasks are billed based on wh…”
- 2026-08-20 · mherrmann · [item 49376085](https://news.ycombinator.com/item?id=49376085) · _Harvest hikes bills by 1500% after purchased by Bending Spoo_ — “They doubled my bill from $130 to $280 per year and graciously also offered me a $19,000 per year plan (1). I declined and am now using Clockify. / 1: https://x.com/m\_her…”
- 2026-08-20 · orliesaurus · [item 49375697](https://news.ycombinator.com/item?id=49375697) · _Harvest hikes bills by 1500% after purchased by Bending Spoo_ — “I posted about my friend Igor who had a similar experience on my LI (1) - from a few hundred to $3000+ a month - and a lot of people reacted saying you could simply vibe-…”
- 2026-08-20 · molf · [item 49375595](https://news.ycombinator.com/item?id=49375595) · _Harvest hikes bills by 1500% after purchased by Bending Spoo_ — “But it's not enterprise SaaS, is it? It's just a time tracking and invoicing tool. And it's not the only SaaS they will need? / Companies with 25 employees generally don'…”
- 2026-08-06 · oplero · [item 49202831](https://news.ycombinator.com/item?id=49202831) · _(dead)_ — “For years I kept adding more tools to my workflow. / One for projects and tasks, another for time tracking, another for CRM, another for invoicing, another for support. /…”
- 2026-08-02 · springtimesun · [item 49141854](https://news.ycombinator.com/item?id=49141854) · _Things I would have done differently (consulting)_ — “I’m a one person team, but I went the other direction and replaced my paid time tracking and invoicing software with something custom. The decider wasn’t the monthly paym…”
- 2026-07-15 · ddyy · [item 48920389](https://news.ycombinator.com/item?id=48920389) · _Show HN: Minvoice – invoicing app that runs on Cloudflare Wo_ — “Hi HN, / The invoicing SaaS I was using to bill my clients raised its credit card processing fee to 6.9% for free accounts (4% on top of Stripe's 2.9% + 30c fee), so I de…”
- 2026-06-15 · christoph123 · [item 48537502](https://news.ycombinator.com/item?id=48537502) · _Ask HN: What are you working on? (June 2026)_ — “For most people, time is more valuable than money, yet we obsess over budgets and never look into time spent. / I think that's because time tracking is hard and annoying,…”
- 2026-06-11 · CognitiveLens · [item 48497205](https://news.ycombinator.com/item?id=48497205) · _I stopped tracking my time. Now I can't focus_ — “It sounds like two factors are at work - reducing personal time-tracking AND doing more AI-assisted work, both of which can reduce our ability to focus. In the case of AI…”
- 2026-06-09 · davedx · [item 48457252](https://news.ycombinator.com/item?id=48457252) · _Ask HN: What are tools you have made for yourself since the_ — “I made a timesheet entry, invoicing, and basic bookkeeping system for my freelance business. It works pretty well, I used "spec driven development" with Codex and it one-…”
- 2026-06-03 · pmontra · [item 48389272](https://news.ycombinator.com/item?id=48389272) · _Uber's $1,500/month AI limit is a useful signal for AI tool_ — “› Your other plans are fixed price with rate limits where you get more tokens than the dollar equivalent you pay monthly. / Or the fixed cost plans reflect the real cost…”
- 2026-04-28 · soarbill · [item 47938722](https://news.ycombinator.com/item?id=47938722) · _(dead)_ — “I’m a freelancer and got tired of using time-reporting and invoicing tools. Most of the tools in the market are designed for teams and enterprise companies. They have ton…”

### O. 'Claudespeak': verbose AI voice leaking into tickets, PRs and docs — 15 items, 15 distinct authors, 11 dated Aug–Oct 2026

- 2026-10-13 · pertymcpert · [item 50079535](https://news.ycombinator.com/item?id=50079535) · _Redesigning source control at Anthropic_ — “This is such a Claude written post. Obvious tells everywhere, but the most annoying is how it uses private terms without defining them. What the fuck is "Spanner"? It ref…”
- 2026-10-10 · incognito124 · [item 50037652](https://news.ycombinator.com/item?id=50037652) · _Why We Still Cannot Read Etruscan_ — “I wish Claude's raw output was at least moderately edited. This way it feels like I spent time and energy reading something no human wrote…”
- 2026-10-07 · ninininino · [item 49996766](https://news.ycombinator.com/item?id=49996766) · _Berthd_ — “Frankly 'box' feels like classic Claude-slop of 'throw a random synonym in that is less precise/internal jargon'. I wish Claude would fix this (if my guess is correct and…”
- 2026-10-07 · lowenbjer · [item 49995809](https://news.ycombinator.com/item?id=49995809) · _Show HN: Terse, a Claude Code plugin that halves reply lengt_ — “I struggle with the way Claude speaks to me when I do work. So much text, every, single, time. / When I ask a question, I get an essay back, and with so many weird constr…”
- 2026-09-23 · invalidusernam3 · [item 49817128](https://news.ycombinator.com/item?id=49817128) · _Claude Opus 5.5_ — “I would happily pay more for a claude model that performs the same but speaks normal English. The proliferation of claudespeak in the workplace is driving me insane. Ever…”
- 2026-09-09 · squalvj · [item 49626814](https://news.ycombinator.com/item?id=49626814) · _Ask HN: Anyone still coding like 2021? Where do you work?_ — “In my company they give each one claude code. / The transition of winning an argument change to “claude said…” which are fucking annoying facing this shit in daily basis.…”
- 2026-09-08 · hk1337 · [item 49612030](https://news.ycombinator.com/item?id=49612030) · _I-have-ADHD: A skill to stop coding agents from burying the_ — “› A skill to stop your coding agent from burying the answer / This is just an annoying thing for anyone. It gives a 10 page dissertation that sums up to, "it's good, noth…”
- 2026-09-03 · PaulStatezny · [item 49546688](https://news.ycombinator.com/item?id=49546688) · _Gemini 3.8 Flash and 3.8 Flash Cyber_ — “It struck me today using Google Antigravity (Claude Code alternative) just how direct and usably terse Gemini is in prose. / I've complained plenty on here about Claude v…”
- 2026-08-27 · simlevesque · [item 49466558](https://news.ycombinator.com/item?id=49466558) · _Show HN: The load-bearing vocabulary of Claude_ — “I wish there was a search bar for the terms, I wanna see for "gate".…”
- 2026-08-27 · KronisLV · [item 49464375](https://news.ycombinator.com/item?id=49464375) · _The Harness Is the Thing_ — “› when Anthropic finally collapses their 50% usage increase at the end of August, I'll definitely be forced to switch my workflow / I cancelled my Anthropic subscription…”
- 2026-08-21 · preg_match · [item 49394742](https://news.ycombinator.com/item?id=49394742) · _Kagi added a setting for removing paywalled links from searc_ — “I use Claude code for basically everything, since the harness is pretty complete. The online chat interface works fine too. For basic research I downgrade the model and e…”
- 2026-07-14 · alxndr · [item 48908304](https://news.ycombinator.com/item?id=48908304) · _How to stop Claude from saying load-bearing_ — “I did something like this in my global 'CLAUDE.md'... / https://github.com/alxndr/dotfiles/blob/272475280d84e/claude... / › It can be tricky for humans to interpret the m…”
- 2026-07-10 · TimTheTinker · [item 48859248](https://news.ycombinator.com/item?id=48859248) · _AI doesn't know how to forgive and cannot forget_ — “Ugh, another LLM-voice article. / I'm getting to the point that I almost have a physical feeling of revulsion/nausea when I read something outside an open Claude Code ses…”
- 2026-06-09 · kkarpkkarp · [item 48456700](https://news.ycombinator.com/item?id=48456700) · _Ask HN: What are tools you have made for yourself since the_ — “https://undsh.com/ / in case you forgot instruct your ai text generating tool to do so: replaces — with -, removes emojis and changes quotes to look like human-typed (eve…”
- 2026-05-01 · roywashere · [item 47971628](https://news.ycombinator.com/item?id=47971628) · _I Got Sick of Remembering Port Numbers_ — “I hate these signs of LLM generated texts so much!! / › The real annoyance is that it wasn’t just one machine. It was layers.…”

---

## Query log (all Algolia queries run; comments unless tags say story/ask_hn; all filtered to created_at_i > 1776211200, typoTolerance=false)

| slug | query | tags | hits since 2026-04-15 |
|---|---|---|---|
| wtp_idpayfor | `"I'd pay for"` | comment | 43 |
| wtp_iwouldpayfor | `"I would pay for"` | comment | 47 |
| wtp_wouldhappilypay | `"would happily pay"` | comment | 37 |
| wtp_idhappilypay | `"I'd happily pay"` | comment | 20 |
| wtp_shutup | `"shut up and take my money"` | comment | 14 |
| wtp_takemymoney | `"take my money"` | comment | 69 |
| wtp_gladlypay | `"gladly pay"` | comment | 91 |
| wtp_paygoodmoney | `"pay good money"` | comment | 32 |
| wtp_wouldpay | `"would pay"` | comment | 688 |
| wtp_idbuy | `"I'd buy"` | comment | 173 |
| wtp_iwouldbuy | `"I would buy"` | comment | 129 |
| wtp_worthpaying | `"worth paying for"` | comment | 80 |
| wtp_payamonth | `"pay" "a month for"` | comment | 86 |
| wtp_onetimepurchase | `"one-time purchase"` | comment | 82 |
| wtp_onetimepurchase2 | `"one time purchase"` | comment | 82 |
| wtp_lifetimelicense | `"lifetime license"` | comment | 39 |
| wtp_paidfor_mac | `"paid for" mac app` | comment | 10 |
| seek_macapp | `"is there a mac app"` | comment | 0 |
| seek_tool | `"is there a tool"` | comment | 7 |
| seek_app | `"is there an app"` | comment | 8 |
| seek_anyoneknowtool | `"does anyone know a tool"` | comment | 0 |
| seek_anyoneknowof | `"anyone know of a"` | comment | 53 |
| seek_lookingfortool | `"looking for a tool"` | comment | 13 |
| seek_isthereanything | `"is there anything" tool` | comment | 18 |
| seek_somethinglike | `"is there something like"` | comment | 21 |
| seek_recommend | `"any recommendations for"` | comment | 52 |
| seek_whatdoyouuse | `"what do you use for"` | comment | 26 |
| wa_wroteascript | `"I wrote a script"` | comment | 18 |
| wa_builtascript | `"I built a script"` | comment | 3 |
| wa_hackedtogether | `"I hacked together"` | comment | 14 |
| wa_myworkaround | `"my workaround"` | comment | 13 |
| wa_endedupwriting | `"ended up writing"` | comment | 72 |
| wa_endedupbuilding | `"ended up building"` | comment | 115 |
| wa_builtmyown | `"built my own"` | comment | 244 |
| wa_vibecodedmyown | `"vibe coded my own"` | comment | 15 |
| wa_ivibecodeda | `"I vibe coded a"` | comment | 53 |
| wa_wishtherewas | `"wish there was"` | comment | 484 |
| wa_wishthereweresome | `"wish there were"` | comment | 183 |
| wa_someoneshouldbuild | `"someone should build"` | comment | 12 |
| wa_someoneshouldmake | `"someone should make"` | comment | 45 |
| wa_whyisthereno | `"why is there no"` | comment | 56 |
| wa_nobodyhasbuilt | `"nobody has built"` | comment | 9 |
| ag_iwishcc | `"I wish Claude Code"` | comment | 3 |
| ag_iwishcodex | `"I wish Codex"` | comment | 2 |
| ag_iwishcursor | `"I wish Cursor"` | comment | 0 |
| ag_wishclaude | `"wish Claude"` | comment | 8 |
| ag_cc_annoying | `"Claude Code" annoying` | comment | 106 |
| ag_cc_frustrating | `"Claude Code" frustrating` | comment | 45 |
| ag_codingagents_pain | `"coding agents" pain` | comment | 30 |
| ag_agent_annoying | `"coding agent" annoying` | comment | 15 |
| ag_painpoint_agent | `"pain point" agent` | comment | 32 |
| ag_worktrees | `worktrees` | comment | 413 |
| ag_worktree | `worktree` | comment | 615 |
| ag_parallelagents | `"parallel agents"` | comment | 87 |
| ag_multipleagents | `"multiple agents" code` | comment | 111 |
| ag_agent_secrets | `agent secrets` | comment | 485 |
| ag_agent_env | `agent .env` | comment | 63 |
| ag_apikeys_agent | `"API keys" agent` | comment | 123 |
| ag_devserver_ports | `"dev server" ports` | comment | 6 |
| ag_portinuse | `"port" "already in use"` | comment | 3 |
| ag_devservers | `"dev servers"` | comment | 22 |
| ag_usagelimits | `"usage limits"` | comment | 428 |
| ag_weeklylimit | `"weekly limit"` | comment | 148 |
| ag_ratelimit_cc | `"rate limit" "Claude Code"` | comment | 7 |
| ag_hitlimit | `"hit the limit"` | comment | 57 |
| ag_ctxwindow_claudemd | `"context window" CLAUDE.md` | comment | 16 |
| ag_claudemd | `"CLAUDE.md"` | comment | 975 |
| ag_agentsmd | `"AGENTS.md"` | comment | 1124 |
| ag_mcp_config | `MCP config` | comment | 226 |
| ag_mcpservers | `"MCP servers"` | comment | 394 |
| ag_vibecoded_looks | `"vibe coded" looks` | comment | 379 |
| ag_sideprojects_abandoned | `"side projects" abandoned` | comment | 12 |
| ag_sideprojects_graveyard | `"side projects" graveyard` | comment | 2 |
| ag_slop_design | `"AI slop" design` | comment | 149 |
| ag_slop_ui | `"AI slop" UI` | comment | 53 |
| ag_permprompts | `"permission prompts"` | comment | 57 |
| ag_dangerously | `"dangerously-skip-permissions"` | comment | 106 |
| ag_yolo | `"YOLO mode"` | comment | 150 |
| ag_sandbox_cc | `sandbox "Claude Code"` | comment | 128 |
| ag_babysit | `babysit agent` | comment | 68 |
| ag_babysitting | `babysitting` | comment | 223 |
| ag_compaction | `compaction context` | comment | 332 |
| ag_fromphone | `"from my phone" agent` | comment | 43 |
| ag_fromphone_cc | `"from my phone" claude` | comment | 26 |
| ag_tmux_agents | `tmux agents` | comment | 230 |
| ag_ccusage | `ccusage` | comment | 44 |
| ag_tokenusage | `"token usage"` | comment | 861 |
| ag_skills_cc | `skills "Claude Code"` | comment | 614 |
| ag_hooks_cc | `hooks "Claude Code"` | comment | 173 |
| ag_subagents | `subagents` | comment | 1442 |
| ag_claudemax | `"Claude Max"` | comment | 286 |
| ag_multiaccounts | `"multiple accounts" claude` | comment | 10 |
| ag_notify_done | `notification agent finished` | comment | 3 |
| ag_voice_dictation | `dictation coding` | comment | 12 |
| ag_wispr | `wispr` | comment | 81 |
| ag_superwhisper | `superwhisper` | comment | 25 |
| st_askhn_tools | `Ask HN tools` | story | 533 |
| st_askhn_agent | `Ask HN agent` | story | 726 |
| st_askhn_claude | `Ask HN Claude` | story | 547 |
| st_askhn_codex | `Ask HN Codex` | story | 188 |
| st_askhn_workflow | `Ask HN workflow` | story | 187 |
| st_askhn_pay | `Ask HN pay` | story | 234 |
| st_askhn_mac | `Ask HN Mac` | story | 273 |
| st_askhn_side | `Ask HN side project` | story | 81 |
| st_askhn_solo | `Ask HN solo` | story | 65 |
| st_askhn_vibe | `Ask HN vibe` | story | 102 |
| st_askhn_manage | `Ask HN how do you manage` | story | 67 |
| st_askhn_all | `(empty)` | ask_hn | 206 |
| st_showhn_mac | `Show HN macOS` | story | 786 |
| st_showhn_mac2 | `Show HN Mac app` | story | 433 |
| st_showhn_menubar | `Show HN menu bar` | story | 137 |
| st_showhn_claudecode | `Show HN Claude Code` | story | 1600 |
| st_showhn_agents | `Show HN agents` | story | 4261 |
| mac_nativeapp | `"native mac app"` | comment | 21 |
| mac_nativemacos | `"native macOS"` | comment | 102 |
| mac_menubar | `"menu bar" app` | comment | 122 |
| mac_tableplus | `TablePlus` | comment | 4 |
| mac_proxyman | `Proxyman` | comment | 6 |
| mac_orbstack | `OrbStack` | comment | 122 |
| mac_raycast | `Raycast` | comment | 115 |
| mac_setapp | `Setapp` | comment | 7 |
| mac_cleanshot | `CleanShot` | comment | 15 |
| mac_littlesnitch | `"Little Snitch"` | comment | 46 |
| mac_xcode_agent | `Xcode claude` | comment | 42 |
| mac_xcode_codex | `Xcode codex` | comment | 19 |
| mac_simulator_agent | `"iOS simulator" agent` | comment | 3 |
| mac_testflight | `TestFlight` | comment | 121 |
| mac_appstorereview | `"App Store" review rejected` | comment | 7 |
| mac_notarization | `notarization` | comment | 60 |
| mac_appstoreconnect | `"App Store Connect"` | comment | 17 |
| mac_keepawake | `caffeinate agent` | comment | 3 |
| mac_lidclosed | `"lid closed"` | comment | 16 |
| mac_amphetamine | `Amphetamine mac` | comment | 10 |
| vc_lovable | `Lovable` | comment | 297 |
| vc_bolt | `"Bolt.new"` | comment | 12 |
| vc_replit | `Replit agent` | comment | 24 |
| vc_v0 | `v0 vercel` | comment | 8 |
| vc_vibecoders_stuck | `"vibe coders" stuck` | comment | 3 |
| vc_nontechfounder | `"non-technical founder"` | comment | 9 |
| vc_nontech | `"non-technical" vibe` | comment | 102 |
| vc_supabase_rls | `Supabase RLS` | comment | 27 |
| vc_vibecodedapp_security | `"vibe coded" security` | comment | 144 |
| vc_vibecodedapp_prod | `"vibe coded" production` | comment | 87 |
| ops_surprisebill | `"surprise bill"` | comment | 14 |
| ops_spendcap | `"spending cap"` | comment | 15 |
| ops_budgetcap | `"budget cap"` | comment | 17 |
| ops_vercelbill | `Vercel bill` | comment | 41 |
| ops_uptime | `"uptime monitoring"` | comment | 15 |
| ops_backups | `backups "side project"` | comment | 4 |
| ops_pgbackups | `postgres backups` | comment | 93 |
| ops_sentry | `Sentry pricing` | comment | 1 |
| ops_emaildeliv | `"email deliverability"` | comment | 15 |
| ops_soc2 | `SOC2 solo` | comment | 7 |
| ops_coolify | `Coolify` | comment | 45 |
| ops_dokploy | `Dokploy` | comment | 14 |
| dl_devserver_logs | `agent "dev server"` | comment | 13 |
| dl_logs_agent | `agent logs "can't see"` | comment | 2 |
| dl_playwright_mcp | `"Playwright MCP"` | comment | 26 |
| dl_devtools_mcp | `"devtools mcp"` | comment | 12 |
| dl_screenshots_agent | `screenshots agent UI` | comment | 45 |
| dl_contextswitch | `"context switching" agents` | comment | 58 |
| dl_needsattention | `agent "needs input"` | comment | 3 |
| dl_notifydone | `notify agent done` | comment | 6 |
| dl_copypaste_cc | `"copy paste" "Claude Code"` | comment | 50 |
| dl_copypaste_term | `copy terminal "line breaks"` | comment | 2 |
| dl_sessionhistory | `"session history" agent` | comment | 18 |
| dl_resume_session | `"/resume"` | comment | 4844 |
| dl_transcripts | `transcripts "Claude Code"` | comment | 67 |
| dl_plannotator | `Plannotator` | comment | 35 |
| dl_plan_review | `plan review comment agent` | comment | 32 |
| dl_db_agent_prod | `agent deleted production database` | comment | 17 |
| dl_migrations_agent | `agent migrations database` | comment | 15 |
| dl_overnight | `overnight agent tasks` | comment | 23 |
| dl_phone_approve | `approve phone agent permission` | comment | 3 |
| dl_remotecontrol | `"remote control" claude` | comment | 101 |
| fl_clients_cc | `clients "Claude Code"` | comment | 237 |
| fl_billing_ai | `billing clients AI hours` | comment | 10 |
| fl_timetracking | `"time tracking"` | comment | 69 |
| fl_freelance_ai | `freelance agents clients` | comment | 9 |
| fl_fixedprice | `"fixed price" AI` | comment | 33 |
| fl_invoice | `invoicing freelance` | comment | 12 |
| st_ports | `port numbers` | story | 12 |
| st_localhost | `localhost` | story | 96 |
| st_devserver | `dev server` | story | 288 |
| st_worktree | `worktree` | story | 150 |
| st_secrets_agents | `secrets agents` | story | 120 |
| st_env | `.env` | story | 67 |
| st_sandbox | `sandbox agents` | story | 301 |
| st_distributing_mac | `distributing Mac` | story | 3 |
| st_screenshot | `screenshot Claude Code` | story | 61 |
| st_remote_agents | `remote coding agents phone` | story | 6 |
| st_session_search | `search agent sessions history` | story | 9 |
| st_memory_agents | `memory coding agents` | story | 160 |
| c_localhost_ports | `localhost port` | comment | 65 |
| c_port_conflicts | `"port conflicts"` | comment | 4 |
| c_port_collision | `ports collide` | comment | 1 |
| c_whichport | `"which port"` | comment | 12 |
| c_dotlocalhost | `".localhost"` | comment | 26 |
| c_dockercompose_worktree | `"docker compose" worktree` | comment | 4 |
| c_paste_images | `paste images terminal` | comment | 9 |
| c_screenshot_terminal | `screenshot terminal agent` | comment | 18 |
| c_image_ssh | `images ssh agent` | comment | 12 |
| fl_billable | `billable hours AI` | comment | 19 |
| fl_billable2 | `"billable" agents` | comment | 3 |
| fl_harvest | `Harvest alternative` | comment | 6 |
| fl_toggl | `Toggl` | comment | 1320 |
| fl_clients_ai_disclose | `clients know AI wrote` | comment | 12 |
| fl_charge_less | `charge clients less AI` | comment | 5 |
| ops_serverless_horror | `"serverless horrors"` | comment | 0 |
| ops_bill_shock | `bill shock` | comment | 48 |
| ops_hardcap | `"hard cap" billing` | comment | 9 |
| ops_api_key_leak_bill | `API key leaked bill` | comment | 3 |
| wtp_subscription_fatigue | `"subscription fatigue"` | comment | 15 |
| wtp_buy_once | `"buy once"` | comment | 44 |
| wtp_paid_upgrade | `"paid upgrades"` | comment | 5 |
| wtp_nobody_pays | `"nobody pays" developers` | comment | 0 |
| wtp_devs_dont_pay | `"developers don't pay"` | comment | 1 |
| wtp_devs_wont_pay | `developers "won't pay"` | comment | 7 |
| pl_zombie | `zombie processes agent` | comment | 5 |
| pl_eaddrinuse | `EADDRINUSE` | comment | 1 |
| pl_addrinuse | `"address already in use"` | comment | 0 |
| pl_devserver_agent_kill | `agent kills dev server` | comment | 2 |
| pl_background_process | `"background process" agent` | comment | 6 |
| pl_logs_devserver | `dev server logs claude` | comment | 4 |
| pl_hotreload_agent | `hot reload agent` | comment | 8 |
| pl_process_compose | `process-compose` | comment | 3 |
| pl_overmind | `overmind foreman Procfile` | comment | 0 |
| pl_tilt | `tilt dev environment` | comment | 0 |

228 queries.

## Files

- Raw API responses: `/tmp/claude-0/-home-user-experiments/71b6e69a-350a-5a54-b87d-67380633b427/scratchpad/research/hn_raw/` (search pages as `<slug>_p<N>.json`; full threads under `items/`).
- Curated cluster evidence IDs: `/tmp/claude-0/-home-user-experiments/71b6e69a-350a-5a54-b87d-67380633b427/scratchpad/research/data/clusters.json`; scripts in `/tmp/claude-0/-home-user-experiments/71b6e69a-350a-5a54-b87d-67380633b427/scratchpad/research/scripts/`.
