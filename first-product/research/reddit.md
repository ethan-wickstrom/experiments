# Reddit pain research: solo devs building with coding agents (window 2026-04-15 to 2026-10-15, weighted to Aug–Oct)

## 1. Data source and freshness

- **PullPush was not usable.** Every call returned HTTP 429 with the message "This website does not provide free scraping resources for agents" (2026-10-15 08:00 UTC). I did not try to get around it.
- **reddit.com was not usable either.** Its JSON returned 403, and WebSearch refuses the reddit.com domain.
- **I used the Arctic Shift archive API (arctic-shift.photon-reddit.com) instead.** It is a public Reddit archive that allows light use. It is fresh: the newest r/ClaudeAI post it held was from 2026-10-15 06:40 UTC, and the newest r/ClaudeCode post from 08:08 UTC.
- **Posts downloaded (title and body):** about 390k in total.
  - Full window: r/ClaudeCode 41.9k, r/ClaudeAI 62.6k, r/codex 34.7k, r/cursor 6.2k, r/vibecoding 45.1k, r/macapps 6.4k, r/ChatGPTCoding 2.2k, r/reactjs 3.5k, r/ExperiencedDevs 4.6k, r/indiehackers 21k.
  - Recent window only: r/SideProject (Aug–Oct, 72.6k), r/SaaS (Jul–Oct, 25.8k), r/MacOS (Jul–Oct, 6.5k), r/webdev (Jul–Oct, 11k), r/programming (Jul–Oct, 3.1k), r/selfhosted (Aug–Oct, 5.6k), r/OpenAI (Aug–Oct, 8.9k).
  - Not finished: r/microsaas, r/iOSProgramming and r/swift. I stopped those downloads when told to wrap up, so coverage of iOS/Swift is thin.
- **Comments:** I read about 60 full comment trees for the largest threads. I also ran full-text phrase searches:
  - "I'd pay" across r/ClaudeCode, Apr–Oct.
  - One combined query ("I'd pay", "take my money", "happily/gladly/willing to pay", "worth paying", and similar) on r/macapps, r/indiehackers, r/microsaas and r/ChatGPTCoding.
  - Comment search on the very large subs kept timing out, so comment-level counts are partial.
- **How to read the counts:** they come from regular-expression matches on post titles and bodies, counted as distinct authors of "demand" posts. Demand means I excluded showcase and "I built" posts by flair and wording. The counts are approximate and noisy; use them for ranking, not as exact numbers.
- **Treat stated willingness to pay with caution.** Several founders in the data point out that "I'd pay" seldom turns into a card payment. One example: "Five said they would pay for a fix. I have two actual sales" ([u/felixbuilds, 2026-09-09](https://www.reddit.com/r/microsaas/comments/1wb278k/comment/p8pf91q/)).
- **Many posts and replies are AI-written or hidden promotion.** I flagged the obvious cases.
- **Files:**
  - Raw data: `reddit_raw/` (`posts_all__*.jsonl`, `tree__*.json`, `comments__*.json`).
  - Scripts: `scripts/arctic.py`, `bulk.py`, `rd_search.py`, `rd_cluster.py`, `rd_deep.py`, `rd_thread.py`.
  - Working notes: `rd_notes.md`.

## 2. Background (how the market looked in Aug–Oct 2026)

- **SpaceX bought Cursor in August 2026.** Many users then left Cursor for Claude Code. Examples: "OpenAI is ending its Cursor partnership" ([239 comments](https://www.reddit.com/r/cursor/comments/1w19lrl/)) and "1 year of cursor, switched to claude" ([link](https://www.reddit.com/r/cursor/comments/1wrx24u/)).
- **Plan limits and resets dominate r/codex and r/ClaudeCode.** Most of the money people say they would spend is aimed at the vendors' plans, not at tools (see cluster A).
- **Builders keep replacing paid apps with things they build themselves.** This works against simple utilities (see the surprises in section 5).

## 3. Clusters ranked by evidence that people would pay

How I ranked: first, money already being spent or explicitly offered; second, how often the pain comes up; third, how recent it is. Section 3a covers pain with a money signal. Section 3b covers complaints that are frequent but show weak money.

### 3a. Real pain with a money signal

#### A. Running out of usage limits, and juggling plans and accounts (rank 1 on frequency; the money goes to the vendors)

**What it is:** developers keep hitting 5-hour and weekly caps. They cannot see how much is left or when it resets, they run two to five accounts and switch between them by hand, and they want per-session budgets.

**How common:**
- About 2,140 distinct authors posted about hitting limits; 877 of those posts are from Aug–Oct.
- About 670 authors posted about wanting to see usage.
- About 390 authors posted about juggling several accounts.
- The heaviest subs are r/codex, r/ClaudeCode and r/ClaudeAI.

**Quotes:**
- "I would pay 75 - 100 for a weekly reset on my max plan" ([u/hanasato, 2026-09-07](https://www.reddit.com/r/ClaudeCode/comments/1wa6opl/))
- "I'd pay $150 tomorrow if it existed" (a mid-tier Max plan) ([u/czioscerny, 2026-09-07](https://www.reddit.com/r/ClaudeCode/comments/1w9ourm/))
- "I think ability set limits for our work should be in our hands" (asking for a per-session or daily usage budget; 266 comments, score 941) ([2026-07-16](https://www.reddit.com/r/codex/comments/1uxzgef/))
- "Codex badly needs a cache timeout indicator, like Claude recently added" (score 566) ([2026-09-17](https://www.reddit.com/r/codex/comments/1wixw9c/))
- "Is there a way to get notified or a webhook to know when the limit window gets reset?" ([2026-09-15](https://www.reddit.com/r/ClaudeCode/comments/1wh038i/))
- An account switcher built because the vendors won't "shut up and take our money with one single big subscription" ([hotseat, 2026-09-16](https://www.reddit.com/r/codex/comments/1whjgd7/))

**What people use now:**
- Many free menu-bar usage meters: UsageNow, claudebar, Watt, codeburn, Meter Beater, a Windows usagebar.
- ccusage.
- Account switchers: sessionflip, claude-transplant, hotseat, and an app that moves a session to another account mid-task.
- A "menu bar app that shows how much of your usage limit is left" heads one creator's list of the most-requested tools, "threads with ~2.7k upvotes combined" ([link](https://www.reddit.com/r/ClaudeCode/comments/1wh64b4/)).

**Money signal:** strong but pointed at Anthropic and OpenAI (more capacity, resets, in-between tiers). I found no evidence that people pay for meters.

**Risks (guesses):** the vendors keep adding meters and cache indicators, and juggling accounts runs into terms-of-service problems.

#### B. Apps built with AI that are not ready for production: security, compliance and rescue

**What it is:** apps built by non-developers or quickly with agents work in a demo, then fail on security, auth, backups or compliance questionnaires. The owners want someone to tell them the truth.

**How common:** about 1,040 distinct authors (523 posts in Aug–Oct), mostly in r/vibecoding, r/SaaS and r/SideProject.

**Quotes:**
- "I'd happily pay a real human to look at my code and tell me the truth." ([u/JohnyGhost, 2026-09-29](https://www.reddit.com/r/ClaudeCode/comments/1wtnagf/))
- "I absolutely would pay one to look at something I want to put into production and tell me what the robot did that I'm not qualified to notice." ([u/ops_and_chaos](https://www.reddit.com/r/ClaudeCode/comments/1wtnagf/comment/pcvq0eb/))
- Counter-evidence: "They laughed at me and told me they would pay claude (or codex) to fix the issues." ([u/WinterWalk2020](https://www.reddit.com/r/ClaudeCode/comments/1wtnagf/comment/pcvrjwd/))
- An agency owner: "a big chunk of our work this year has quietly become taking AI-built apps and getting them ready for real users" (183 comments, score 1,107) ([2026-07-17](https://www.reddit.com/r/vibecoding/comments/1uypcye/))
- "vibe coding is amazing at 'make it work' and terrible at 'prove it can't go wrong'" ([u/mohn93, 2026-09-05](https://www.reddit.com/r/SideProject/comments/1w88c58/comment/p823c45/))
- Shutting a SaaS down partly because a security audit would cost "about 5K out of my personal savings" ([2026-08-23](https://www.reddit.com/r/SaaS/comments/1vwejv6/))

**What people use now:**
- Prompt-based "security audit" skills.
- Free pentests offered on Reddit ([link](https://www.reddit.com/r/vibecoding/comments/1vx0q8h/)).
- launchworthy (MIT), gstack.
- OpenAI's own "Codex Security / Daybreak" ([link](https://www.reddit.com/r/codex/comments/1w2x94a/)), which shows the platform taking over this job.
- Paid agencies.

**Money signal:** real, but it is for services and audits. A tool sold to vibe coders faces the "they'd rather pay Claude" problem.

#### C. Finding first users (frequent, but the client has already looked at this)

**How common:** about 2,430 distinct authors (1,911 posts in Aug–Oct), dominated by r/SaaS and r/SideProject.

**Examples:**
- "I can build the product. I keep getting stuck on distribution." ([2026-09-07](https://www.reddit.com/r/SideProject/comments/1w9gilk/))
- "Built something and nobody saw it?" (262 comments) ([link](https://www.reddit.com/r/SideProject/comments/1wxb5ur/))
- "AI cold email has not brought me one paying customer. 1,104 emails, 0 paid." ([link](https://www.reddit.com/r/SideProject/comments/1w73u24/))
- "Do AI-looking landing pages make you instantly leave?" ([link](https://www.reddit.com/r/SideProject/comments/1wkawzo/))

**Money signal:** founders do pay for ads, directories and video services, and the market is full of service sellers ("Drop your product, I'll make a video"). Nothing here is new compared with the client's positioning and launch ideas.

#### D. Dictating prompts to agents (a proven paid category, but crowded and easy to clone)

**How common:** about 570 distinct authors (320 posts in Aug–Oct).

**Quotes:**
- Wispr Flow is "one of the very few paid subscriptions I have in my life" ([u/UnionPacifik, 2026-07-09](https://www.reddit.com/r/ClaudeCode/comments/1urria9/comment/owi1i85/))
- "i dictate pretty much all my life to claude code now" ([u/Crackx17, 2026-09-19](https://www.reddit.com/r/macapps/comments/1wksxws/comment/patzvgc/))
- "Replaced my $15/mo Wispr Flow subscription with a free local macOS app I built using Claude Code" ([2026-05-14](https://www.reddit.com/r/ClaudeAI/comments/1tczjvp/))
- "I already cloned WisperFlow because they charge too much for that app and it took me a weekend" ([u/lovesToClap, 2026-10-14](https://www.reddit.com/r/macapps/comments/1x5ckfg/comment/pglm7zi/))

**Existing products:** Wispr Flow ($15/mo), Superwhisper, VoiceInk (one-time), Spokenly, FluidVoice and Handy (free).

#### E. Mac storage eaten by developer and agent files ("System Data"). Added on the coordinator's request; looks promising for a native Mac utility

**How common:** 129 posts in Aug–Oct matched across r/MacOS, r/macapps and the agent subs. Most are general "System Data" complaints; the developer-specific subset is smaller.

**Quotes:**
- "System Data Taking up over 198 GB, need help" (214 comments, 2026-10-11) ([link](https://www.reddit.com/r/MacOS/comments/1x3hej6/))
- "How I freed ~180GB on macOS: rebuild Spotlight index" (score 579) ([link](https://www.reddit.com/r/MacOS/comments/1vkyi1o/))
- Agent-specific: "five worktrees is 303,125 real files of nearly identical content, and Spotlight will dutifully index all" ([2026-08-24](https://www.reddit.com/r/ClaudeAI/comments/1vwwfq3/))
- Mole's developer: "AI tools added another problem. Caches, coding sessions, worktrees, and downloaded models can all take up a lot of space, but losing them has very different consequences" ([2026-10-06](https://www.reddit.com/r/macapps/comments/1wz36bh/))
- A user with a 256 GB M4 Air who "mainly do[es] software development": "96GB 'Documents'... storage completely full & apps crashing" ([link](https://www.reddit.com/r/MacOS/comments/1vu010t/))

**What people recommend:**
- Mole (free, open source, the most recommended): "Use MOLE" ([u/Kronologics](https://www.reddit.com/r/MacOS/comments/1x3hej6/comment/pfb3xq1/)).
- DaisyDisk at about $10: "worth every cent over the years" ([u/photosealand](https://www.reddit.com/r/MacOS/comments/1weda5x/comment/p9v4w5b/)); "It's kind of sad that you still need to pay for an app to have a function that should already be in MacOS... I don't mind buying it" ([u/CastorX](https://www.reddit.com/r/MacOS/comments/1x3hej6/comment/pfe4nv2/)).
- OmniDiskSweeper, OpenDisk (open source), CleanMyMac.
- New entrants: DiskFox ($9.99 one-time, "what grew this week"), Trace 2.0, MacPrune, LittleClean, Purge (these cover Xcode DerivedData, npm caches and simulators).

**Money signal:** people already pay at around the $10 level. My guess at a gap: a tool aware of agent work that knows which worktrees, node_modules, model caches, sessions and snapshots are safe to delete. Price headroom above about $10–30 is unproven.

#### F. Billing clients for work done by agents (niche, but close to existing spending)

**How common:** small and noisy. About 160 authors match, but the relevant core is a few dozen threads.

**Quotes:**
- "Anyone figured out reasonable and ethical ways to bill client hours when using Claude" (53 comments, 2026-07-11) ([link](https://www.reddit.com/r/ClaudeCode/comments/1utvrv1/)). The consensus was to bill for output or raise rates; one consultant's "clients all agreed to double my usual rate" ([u/proxiblue](https://www.reddit.com/r/ClaudeCode/comments/1utvrv1/comment/owytp18/)).
- "Freelancers using Claude Code: What are you using for timesheets and invoicing?" The OP calls Toggl and Harvest "pretty archaic" ([2026-08-07](https://www.reddit.com/r/ClaudeAI/comments/1vi5ihd/)).
- "Is anyone else logging the time your agents are putting in?" ([2026-10-13](https://www.reddit.com/r/ClaudeCode/comments/1x55cyk/))

**Existing products:** Toggl, Harvest, Timing, ManicTime, Flowara (a Mac app).

**Money signal:** freelancers already pay for time trackers. Stated willingness to pay for an agent-aware version is not proven.

#### Ideas the client already considered: strong new evidence only

- **Runaway third-party API spend (overlaps "cost screens").**
  - "i gave claude a batch job overnight, woke up to 96 clips and $2,500 in spends" (259 comments, score 921) ([2026-10-09](https://www.reddit.com/r/ClaudeAI/comments/1x1oxol/))
  - In the same thread: "i spent 6k the other month when i messed up auto renew" ([u/Smart_Department6303](https://www.reddit.com/r/ClaudeAI/comments/1x1oxol/comment/pevfihe/))
  - About 285 authors posted about runaway spend.
- **AI-looking UI (overlaps "design lint"). Coordinator question (2): has anyone paid for a tool that makes agent-built UI look less AI-generated?**
  - Lots of demand: "How are people actually getting Claude to build beautiful UIs instead of generic AI slop?" (120 comments) ([link](https://www.reddit.com/r/ClaudeAI/comments/1ws9oix/)); "Link me your website and Ill tell you if it looks vibe-coded" (112 comments) ([link](https://www.reddit.com/r/vibecoding/comments/1w6ia1d/)).
  - **I found no Aug–Oct comment saying someone paid for a tool that does this.** The fixes people use are free skills (Impeccable, "unslop", Taste Skill, ui-ux-pro-max, the frontend-design skill), Claude Design, Figma MCP, and copying references from Dribbble, Awwwards or Mobbin.
  - The money people mention goes to models: "for design I use a $20 Codex subscription" ([u/rbprepin, 2026-09-06](https://www.reddit.com/r/SaaS/comments/1w8exwz/comment/p833nh5/)).
  - The only "I would pay good money for this" is from June ([r/microsaas](https://www.reddit.com/r/microsaas/comments/1uc9qgx/comment/ot2cgea/)), and the same person adds "You cant beat the ai company at building wrappers."

### 3b. Frequent complaints with weak money signal

#### G. Agents deleting data or touching secrets (very common and very visible; weak money)

**How common:** about 710 authors posted about data loss (387 posts in Aug–Oct). About 380 posted about secrets.

**Quotes:**
- "Code just deleted 48k files." (1,375 comments, score 4,842) ([2026-09-20](https://www.reddit.com/r/ClaudeAI/comments/1wl5cgo/))
- "Claude rm -rf ed my pc" (score 1,773) ([link](https://www.reddit.com/r/ClaudeCode/comments/1vg18yu/))
- "Composer wiped out my whole drive" (143 comments) ([link](https://www.reddit.com/r/cursor/comments/1wur8i7/))
- "auto allow on everything I am basically gambling my files every prompt" ([u/Total-Management8023](https://www.reddit.com/r/cursor/comments/1wur8i7/comment/pd5kppw/))
- "The Claude Code active attack... 294,842 secrets stolen" (score 1,226) ([link](https://www.reddit.com/r/ClaudeAI/comments/1u1zv25/))
- Counter-evidence: a founder building a Mac rollback app asked "What's the worst thing an agent did on your PC?" Heavy users answered "nothing", e.g. "5 20x accounts: nothing" ([link](https://www.reddit.com/r/ClaudeCode/comments/1x3n0te/)).

**What people use now:** git plus backups (Backblaze "~$99 a year... well worth it"), Time Machine, Cursor hooks, many free guard hooks (AgentTrashGuard, ThumbGate, ContextVeil, bubbleclaude), and sandboxes (Stashbase, Docker, Claude Code's built-in sandbox).

**Money signal:** weak. The people who get hurt (no git) are the least likely to pay; professional developers say they don't need it.

#### H. Watching agents while away from the desk (crowded)

**How common:** about 1,260 authors match the keep-awake and remote pattern; this match is noisy.

**Examples:**
- "Closing the lid used to kill my Claude Code runs" ([link](https://www.reddit.com/r/ClaudeCode/comments/1wzx9tc/))
- "How do you guys stay in a flow state while waiting for Claude?" (258 comments) ([link](https://www.reddit.com/r/ClaudeCode/comments/1vkwiuw/))
- "I'd pay for something that pings me when Claude Code finishes a long batch" ([r/microsaas, 2026-07-26](https://www.reddit.com/r/microsaas/comments/1v79agm/comment/ozwfal1/))

**Existing products:** dozens of free or open-source apps (Lockpaw, Crema, AgentBoy, Claude Watch, SpectiX, herdr, Collie, BlurShield, Adrafinil, Amphetamine), plus the vendors' own Remote Control and Dispatch.

#### I. Memory, handoffs and carrying decisions between sessions (crowded)

**How common:** about 1,240 authors.

**Examples:** "How do you carry decisions (not chat history) across Claude Code sessions?" (144 comments) ([link](https://www.reddit.com/r/ClaudeCode/comments/1wmoost/)). The handoff-file thread shows dozens of home-built systems ([link](https://www.reddit.com/r/ClaudeCode/comments/1wewoy5/)).

**Money signal:** none convincing.

#### J. Attention, ADHD and review fatigue

**How common:** about 590 authors.

**Examples:** "Whoever created the ADHD skill god bless you" (score 2,710) ([link](https://www.reddit.com/r/ClaudeAI/comments/1v8o1jn/)); "Kind of burnt out reviewing every single line claude code writes" ([link](https://www.reddit.com/r/ClaudeAI/comments/1voyaox/)).

**Money signal:** none. This also falls into review tooling, which the client dislikes.

#### Smaller items

- Merge conflicts: 59 authors. One person said "Git conflicts. I'd pay $200 a month just for that." ([u/EddieBruvac](https://www.reddit.com/r/ClaudeCode/comments/1wjt3kc/comment/palexgl/))
- Worktree port and database collisions: 54 authors.
- Lost session history: 111 authors.

## 4. How Mac buyers think about price (relevant to a $30–100 one-time price)

- **Strong preference for one-time purchases on local apps.** For example, "against the subscription model for software that runs on my local... computer" (score 25) ([link](https://www.reddit.com/r/macapps/comments/1wb340e/comment/p8n3p6w/)).
- **Lifetime price people accept: about 1–2 years of the subscription.** One seller prices at "$7 a month, $60 a year, or $129 once" and cites median first-year renewal of 35% for utilities and 23% for productivity apps ([link](https://www.reddit.com/r/macapps/comments/1wb340e/comment/p8ybvsd/)).
- **Developers do pay for polished native tools.** Proxyman: "bought licenses for my entire team" ([link](https://www.reddit.com/r/macapps/comments/1wksxws/comment/pbcjc0u/)). Also mentioned: TablePlus, OrbStack, Fork ($60 once), CleanShot. Bobby Tables: "worth way more than 30/year to me" ([link](https://www.reddit.com/r/macapps/comments/1wksxws/comment/paxkbfa/)).
- **Trust is a selling point:** "I'd pay once for tools that keep high-stakes secrets in Keychain and run as a real Mac app" ([link](https://www.reddit.com/r/macapps/comments/1wb340e/comment/p8qnxtr/)).

## 5. Surprises

1. **The target buyer is also your strongest competitor.** "What paid software or subscription did you replace?" (212 comments) ([link](https://www.reddit.com/r/ClaudeAI/comments/1wr61sr/)) and "i've cancelled four subscriptions this year because i just built the thing myself" ([link](https://www.reddit.com/r/vibecoding/comments/1vlc7yf/)). Any tool you can build in a weekend gets cloned. The counterweight: "Paying a $100 Claude sub to replace a $10 sub and actually have to maintain it" (score 76) ([link](https://www.reddit.com/r/ClaudeAI/comments/1wr61sr/comment/pcb6mn1/)). What survives is trust, maintenance burden and deep OS integration.
2. **Most stated willingness to pay is aimed at the model vendors.** People offer to pay for resets, in-between tiers and "$2,000/mo just to have 10x the weekly quota" ([link](https://www.reddit.com/r/codex/comments/1uvpvir/)), not for tools.
3. **The most viral pain (agents wiping data) has the weakest buyers.** Heavy professional users report "nothing" ever happened to them, and the victims are people working without git. Meanwhile, plain Mac storage problems (System Data, Xcode and node_modules clutter, worktrees, model caches) are frequent and already monetised at about $10 (DaisyDisk, DiskFox).
