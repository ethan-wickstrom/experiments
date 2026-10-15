# What developers who build with coding agents pay for on the desktop (2025 – Oct 2026)

Checked 2026-10-15. Scope: desktop and CLI tools sold to people who use Claude Code, Codex and Cursor. The goal is to find an underserved niche for a focused paid Mac app or developer tool.

## How to read this

- **[V]** means verified revenue from a TrustMRR profile, which reads payment-provider APIs (Stripe, Polar, Paddle, Lemon Squeezy, Dodo). Figures were synced 2026-10-14/15 unless noted. TrustMRR describes its method at [trustmrr.com/llms.txt](https://trustmrr.com/llms.txt).
- **[S]** means self-reported by the vendor. **[3P]** means a third-party estimate or listing.
- **Stars** are GitHub stars on 2026-10-15, read through the GitHub search API.
- **Mac App Store ratings caveat:** the iTunes lookup API returns 0 ratings for Mac-only apps. Magnet shows 0 there but 167,549 ratings on its store page. All Mac rating counts below come from `apps.apple.com/us/app/id<ID>?see-all=reviews&platform=mac`, which lists "most helpful" reviews, not all of them.
- **Prices:** dated 2026-10-15 when read from the vendor page. Otherwise the source is marked [3P].

---

## 1. Where money changes hands (summary)

| Job | Who actually gets paid | Strongest evidence | Saturation / verdict |
|---|---|---|---|
| Voice dictation for prompting | Wispr Flow (VC), Superwhisper (bootstrapped), MacWhisper, Spokenly, VoiceInk | Wispr raised $280M at $2B ([TechCrunch](https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/)). Superwhisper has "hundreds of thousands" of weekly active users ([aiwiki](https://aiwiki.ai/wiki/superwhisper)). MacWhisper has 4.3 from 1,226 Mac ratings ([MAS](https://apps.apple.com/us/app/whisper-transcription/id1668083311)). | Very crowded. Handy is free with 33.8k stars. Indie clones earn almost nothing: VibeWhisper $92 all-time [V]. |
| Demo videos and launch assets | Screen Studio (subscription), one-time Screen Studio clones, B2B demo SaaS | Screen Studio has 25k MAU ([systemaic](https://www.systemaic.com/teardowns/screen-studio)). Screen Charm $54.4k and ScreenSage $50.4k all-time [V]. Arcade charges $50 per seat per month. | Screen recorders are crowded. Scripted, repeatable demo and store assets are close to empty. |
| UI and design quality for agent-built apps | shadcnblocks, AI Designer, Skillry; static UI kits are collapsing | shadcnblocks has 5,420 Pro customers [S]. AI Designer has $9.0k MRR [V]. Tailwind Plus closed to new buyers on 2026-09-09. | Static kits are dying. "Taste" tooling is paid but competes with free skills that have 80k–136k stars. |
| Running parallel agents (ADEs) | VC-backed apps sell cloud VMs and teams. A few indie apps sell one-time licences. | Conductor raised a $22M Series A. cmux charges $40–$160/mo for cloud VMs. CNVS made $49.4k [V]. | Extreme saturation. Orca is free with 92.8k stars, Vibe Kanban shut down, and first-party tools now cover this. |
| Usage meters and spend reduction | SessionWatcher, Headroom | SessionWatcher $13.0k all-time [V]. Headroom has $1.8k MRR [V]. | Meters are saturated (CodexBar is free with 22.5k stars, plus 20+ Mac App Store clones). Optimization is emerging, but RTK is free with 83k stars. |
| Terminals | Warp, and what it really sells is AI inference | Warp's ARR claims are self-reported ([PMF Show](https://www.pmf.show/blog/warp-zach-lloyd-agentic-development-environment-1m-arr-every-10-days)) | Free open source dominates: Ghostty, iTerm2, cmux. |
| Local environments, ports and tunnels | Laravel Herd Pro, OrbStack, LocalCan | Herd Pro $99. OrbStack requires a commercial licence. LocalCan $8–$45/mo. | Isolating environments per agent is unclaimed. Ports alone are solved for free by portless. |
| Secrets for agents | Incumbents: 1Password, Doppler, Infisical | Infisical $20 per identity per month. 1Password ships an agent `.env` mount. | Incumbents are moving in. Indie tools are open source. |
| Sandboxes | Cloud: Docker Cloud Sandboxes, E2B | From $0.07/hr | Local sandboxing is free and partly first-party. |
| Context and docs for agents | Context7 Pro, Nia | $10/seat, $14.99/mo | Desktop context builders are dead: Repo Prompt went open source. |
| Skills | Skillry, Agensi | Skillry $2.5k MRR [V] | Free skills with 80k–300k stars dominate. |
| MCP managers, notifications | Almost no one | MCP Router shut down 2026-09-18 | Avoid. |

---

## 2. Category landscapes

### 2.1 Prompt and context building

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Repo Prompt | Native app that curates repo context and coordinates agents over MCP and CLI | **Now free and open source.** Community Edition is Apache-2.0. Classic is "Legacy, No longer supported" ([pricing page](https://repoprompt.com/pricing), checked 2026-10-15). Earlier: Pro ~$14.99/mo, ~$149/yr, lifetime $349–399 [3P] ([rywalker](https://rywalker.com/research/repo-prompt)). | macOS 14+ | The CE repo has 959 stars and 203 open issues ([GitHub](https://github.com/repoprompt/repoprompt-ce)). The founder joined OpenAI and open-sourced the app ([X post](https://x.com/pvncher/status/2062866814695092511), [blog](https://repoprompt.com/blog/repo-prompt-next-chapter/)). | The founder calls the manual copy-paste workflow "a bit too clunky". Agents now explore codebases themselves. |
| 16x Prompt | Desktop app for building prompts from code | Free (10 prompts/day). Lifetime licence $48 individual, $68 team ([pricing](https://prompt.16x.engineer/pricing)). | Desktop | n/a | Same structural decline as Repo Prompt. No refunds. |
| repomix / gitingest / code2prompt | Pack a repo into one file for an LLM | Free open source | CLI and web | 28.8k / 15.9k / 7.7k stars ([repomix](https://github.com/yamadashy/repomix), [gitingest](https://github.com/coderamp-labs/gitingest), [code2prompt](https://github.com/mufeedvh/code2prompt)) | A commodity |
| Context7 (Upstash) | Up-to-date library docs served to agents over MCP | Free: 1,000 API calls/mo. Pro: $10 per seat per month plus $5 per 1k extra calls ([plans](https://context7.com/plans), checked 2026-10-15). | Cloud MCP | 63.1k stars ([GitHub](https://github.com/upstash/context7)) | Free users are blocked after 1,000 calls. It is cloud, not desktop. |
| Nia (YC S25) | Indexes docs and packages for agents | Free, or Cracked at $14.99/mo [3P] ([mcp.directory](https://mcp.directory/blog/top-context7-mcp-alternatives)) | Cloud MCP | Launch HN, 131 points ([HN](https://news.ycombinator.com/item?id=46194828)) | n/a |
| Ref | Was docs for agents; the site now reads "Review the Plan before the Code" | Not listed ([ref.tools](https://ref.tools/pricing)) | Cloud | n/a | Appears to have pivoted |

**Verdict:** desktop context assembly is no longer a paid category. The money that remains is in hosted documentation and context services.

### 2.2 Voice dictation for prompting

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Wispr Flow | Cloud dictation in any app. Reads identifiers from the open editor in VS Code, Cursor and Windsurf, and tags files ([developersdigest](https://www.developersdigest.tech/blog/wispr-flow-voice-prompts-coding-agents)). | Free: 2,000 words/week on desktop. Pro: $15 per user per month, or $12 billed annually ([pricing](https://wisprflow.ai/pricing), checked 2026-10-15). | Mac, Windows, iOS, Android | $280M Series B at $2B in Aug 2026, $361M raised in total ([TechCrunch](https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/)). Wikipedia reports about $3.8M revenue for Jul 2024–Jul 2025, a payment rate of about 19% and 6-month retention of about 80% ([Wikipedia](https://en.wikipedia.org/wiki/Wispr_Flow)). | Users complained of a quality dip; Wispr says its new Canto model cuts errors "from 30% to less than 10%" (TechCrunch). Cloud-only. A Reddit user reported screenshot uploads, and idle use is about 800MB RAM / 8% CPU; these come via competitor-affiliated write-ups ([getvoibe](https://www.getvoibe.com/resources/wispr-flow-review/), [embertype](https://embertype.com/blog/the-day-wispr-flow-banned-a-user/)). Editor context works only in IDEs, not terminal agents. |
| Superwhisper | Local and cloud dictation with modes | Free (local Whisper, unlimited). Pro $8.49/mo, $84.99/yr, or $249.99 lifetime; one licence covers Mac, Windows, iOS and Android ([plans](https://superwhisper.com/docs/billing/plans.md), checked 2026-10-15). | Mac, Windows, iOS, Android | "Hundreds of thousands of weekly active users", bootstrapped ([aiwiki citing Globe and Mail](https://aiwiki.ai/wiki/superwhisper)). Shipped open-weights S1-mini ([HN](https://news.ycombinator.com/item?id=49364361)). | Pricier than the open-source alternatives |
| VoiceInk | Open-source (GPL) local dictation | Lifetime $29 / $49 / $69 for 1 / 2 / 3 Macs, up from $25 / $39 / $49 before Aug 2026 [3P] ([getvoibe](https://www.getvoibe.com/resources/voiceink-pricing/)). Free if you build it from source. | macOS; iOS was in beta in Sep 2025 ([HN](https://news.ycombinator.com/item?id=45415307)) | 6.8k stars ([GitHub](https://github.com/Beingpax/VoiceInk)). Site claims "13,469+" users [S] ([site](https://tryvoiceink.com/)). | Solo maintainer. Anyone can compile it for free. |
| MacWhisper | Transcription plus system-wide dictation | Pro via Gumroad ([listing](https://goodsnooze.gumroad.com/l/macwhisper), 2,762 ratings). Mac App Store build is "Whisper Transcription". | Mac, iOS | 4.3 from 1,226 Mac ratings ([MAS](https://apps.apple.com/us/app/whisper-transcription/id1668083311)) | 1★ "Dictation removed from App-store version" (2026-09-29). 1★ "Overpriced, just get Spokenly for $5". "Mac & iOS subscriptions are separate!" "Getting Worse… shoves more and more stuff into the app" (same page). |
| Spokenly | Dictation with local models or your own API keys | Pro $9.99/mo; local models free per the vendor ([comparison](https://spokenly.app/comparison/wispr-flow)) | Mac, iOS | 4.8 from 769 Mac ratings ([MAS](https://apps.apple.com/us/app/spokenly-audio-to-text-ai-app/id6740315592)) | 1★ 2026-02-27 "Surprise Fee Structure… local models now require subscription… $10… overpriced". This conflicts with the vendor page. |
| Aqua Voice / Willow / Monologue | Cloud dictation | Aqua ~$8/mo; Willow ~$15/mo or $144/yr; Monologue $15/mo or $144/yr [3P] ([getvoibe Aqua](https://www.getvoibe.com/resources/aqua-voice-pricing/), [getvoibe Willow](https://www.getvoibe.com/resources/willow-voice-pricing/), [toolquestor](https://toolquestor.com/vs/willow-voice-vs-monologue)) | Mac and others | TechCrunch names all three as Wispr's competitors | Accuracy claims are vendor-made ([Willow blog](https://willowvoice.com/blog/ai-voice-dictation-cursor-code-faster)) |
| Handy / FreeFlow / Yap | Free open-source dictation | Free | Cross-platform / Mac | Handy 33.8k stars ([GitHub](https://github.com/cjpais/Handy)). FreeFlow's Show HN got 277 points ([HN](https://news.ycombinator.com/item?id=47040375)). Yap got 30 points ([HN](https://news.ycombinator.com/item?id=48703848)). | These set a $0 price anchor |
| Indie developer-focused clones | Push-to-talk tuned for prompting | $19–$49 one-time | macOS | **VibeWhisper $92 all-time** [V] ([TrustMRR](https://trustmrr.com/startup/vibewhisper)). **WalkAITalkie $181** [V] ([TrustMRR](https://trustmrr.com/startup/walkaitalkie)). **VoxBee $586** [V] ([TrustMRR](https://trustmrr.com/startup/voxbee)). **Dictato $1,277** [V] ([TrustMRR](https://trustmrr.com/startup/dictato)). Also VocalCode ([HN](https://news.ycombinator.com/item?id=49323797)). | No differentiation and no distribution |

**Developer-specific pain:** general speech models turn identifiers into English words, so "axios" becomes "axe eos" ([AssemblyAI](https://assemblyai.com/blog/voice-coding-dictate-to-coding-agents)). Wispr's code context covers IDEs only.

**Verdict:** this is the biggest pool of money in the landscape, and the worst place for a new generic entrant.

### 2.3 Agent session managers and parallel-agent environments (ADEs)

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Conductor | Parallel Claude Code, Codex and Cursor agents in git-worktree workspaces | Free locally. Pro $50/mo (Vercel-sandbox cloud workspaces, multiplayer, API, mobile). Teams $60 per user per month ([pricing](https://www.conductor.build/pricing), checked 2026-10-15). | macOS | $22M Series A from Spark and Matrix, 2026-03-30 ([blog](https://www.conductor.build/blog)). Show HN 228 points ([HN](https://news.ycombinator.com/item?id=44594584)). "Used by engineers at Linear, Vercel, Notion, Stripe" ([YC jobs](https://www.ycombinator.com/companies/conductor/jobs/MYjJzBV-product-engineer)). | Mac-only and needs GitHub ([caprock](https://caprock.dev/guides/coding-agent-desktop-apps/)). Cloud sessions are stored on Conductor's servers (pricing FAQ). Local DBs and Docker stacks are left to user scripts: "use nonconcurrent when your project depends on… one local database, one Docker stack" ([docs](https://www.conductor.build/docs/reference/scripts)). |
| cmux (Manaflow, YC S24 [3P], [rywalker](https://rywalker.com/research/cmux)) | Ghostty-based terminal with vertical tabs and agent notifications | Free (GPL). Pro $40/mo and Max $160/mo for cloud VMs and the iOS app; Team and Enterprise tiers ([pricing](https://cmux.com/pricing), checked 2026-10-15). | macOS | 28.2k stars ([GitHub](https://github.com/manaflow-ai/cmux)). Show HN 198 points ([HN](https://news.ycombinator.com/item?id=47079718)). | 3,246 open issues. Flaky status indicators (#1027) and notifications (#2322). Memory and idle-CPU growth (#2962) ([issues](https://github.com/manaflow-ai/cmux/issues)). "Ask HN: Why does cmux need 200 settings?" ([HN](https://news.ycombinator.com/item?id=49743291)). Server components are under BSL 1.1, so "production use or self-hosting requires a commercial license" ([README](https://github.com/manaflow-ai/cmux)). |
| Orca (Stably, YC) | Open-source ADE: worktrees, diffs, embedded browser with design mode, usage view, phone apps | Free ([onorca.dev](https://www.onorca.dev/)) | Mac, Windows, Linux, iOS, Android | **92.8k stars** in 7 months; 8,401 open issues ([GitHub](https://github.com/stablyai/orca)) | It bundles usage meters, account switching, a design mode and mobile control for free, which squeezes every single-purpose utility |
| Superset (YC) | ADE for "100+ agents" | Free for 1 user. Pro $20 per user per month, or $15 billed annually (remote access, automations, Linear and Slack) ([pricing](https://superset.sh/pricing)). | macOS | 15.2k stars, 966 open issues ([GitHub](https://github.com/superset-sh/superset)) | Paid tier only matters for teams |
| Emdash (YC W26) | Open-source ADE | No public paid tier found (pricing URL returns 404) | Cross-platform | 6.0k stars ([GitHub](https://github.com/generalaction/emdash)). Show HN 206 points ([HN](https://news.ycombinator.com/item?id=47140322)). | n/a |
| Nimbalyst (successor to Crystal) | Visual workspace with sessions, markdown, mockups and kanban | Individual $0. Teams "TBD" ([pricing](https://nimbalyst.com/pricing)). | Mac, Windows, Linux | Crystal had 3.1k stars and is deprecated ([GitHub](https://github.com/stravu/crystal)) | No paid plan yet |
| Vibe Kanban (bloop) | Kanban board plus multi-agent workspaces | **Company shut down 2026-04-10.** The project is community-maintained and its cloud features were removed ([shutdown post](https://www.vibekanban.com/blog/shutdown)). | Cross-platform | 28.4k stars ([GitHub](https://github.com/BloopAI/vibe-kanban)) | "The vast majority are free users and we couldn't find a business model" |
| Claude Squad / opcode / Paseo / Happy / CloudCLI | tmux manager, GUI, mobile and web front ends | Free open source | Various | 8.6k / 22.4k / 20.9k / 24.2k / 14.1k stars ([claude-squad](https://github.com/smtg-ai/claude-squad), [opcode](https://github.com/winfunc/opcode), [paseo](https://github.com/getpaseo/paseo), [happy](https://github.com/slopus/happy), [claudecodeui](https://github.com/siteboon/claudecodeui)) | No revenue model. Omnara pivoted to "managed agent platform" ([GitHub](https://github.com/omnara-ai/omnara)). |
| Sculptor (Imbue) | Parallel agents in containers | No public price ([page](https://imbue.com/sculptor/)) | Apple Silicon Mac, Linux | 239 stars ([GitHub](https://github.com/imbue-ai/sculptor)) | Low adoption |
| Caprock | Agent manager with per-repository cost tracking | Free; optional $30/yr licence ([caprock](https://caprock.dev/guides/coding-agent-desktop-apps/)) | Cross-platform | n/a | n/a |
| **CNVS** (indie) | Native Swift Mac app: voice-directed agents on an infinite canvas | $99–$199 one-time ([site](https://cnvs.dev/)) | macOS | **$49,389 all-time; $4,179 last 30 days** [V] ([TrustMRR](https://trustmrr.com/startup/cnvs)) | Sales lean on the founder's 24k X followers (same page) |
| **1DevTool** (indie) | Multi-agent "vibe coding IDE" | $29 one-time | Desktop | **$8,460 all-time** [V] ([TrustMRR](https://trustmrr.com/startup/1devtool)) | n/a |
| First-party | Claude Code agent view (`claude agents`, background sessions, automatic worktrees) shipped 2026-05-11 ([docs](https://code.claude.com/docs/en/agent-view), [claudefa.st](https://claudefa.st/blog/guide/agents/agent-view)). OpenAI's Codex Mac app with parallel agents and worktrees shipped 2026-02-02 ([VentureBeat](https://venturebeat.com/orchestration/openai-launches-a-codex-desktop-app-for-macos-to-run-multiple-ai-coding)). Cursor 3 Agents Window shipped 2026-04-02 ([Cursor](https://cursor.com/blog/design-mode)). Claude Code Remote Control lets the phone drive local sessions, since Feb 2026 ([Help Net Security](https://www.helpnetsecurity.com/2026/02/25/anthropic-remote-control-claude-code-feature/)). | Included in existing plans | | | |

There are also dozens of further open-source orchestrators ([awesome list](https://github.com/andyrewlee/awesome-agent-orchestrators), 2.2k stars; agent-orchestrator 13.2k stars, [GitHub](https://github.com/OrchestratorInc/agent-orchestrator)).

**Verdict:** the most crowded category in the landscape. VC-backed players charge only for cloud and teams. Indie money comes from audience and native polish, as with CNVS.

### 2.4 Usage meters, limit trackers and spend reduction

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| CodexBar (steipete) | Menu bar windows, credits and resets for "103 providers" | Free ([codexbar.app](https://codexbar.app/)) | macOS | 22.5k stars ([GitHub](https://github.com/steipete/CodexBar)) | The most-reacted issues are repeated Keychain prompts (#2115, #1991, #340), lag and freezes (#1274, #1360, #1387), and "CodexBar is becoming bloated" (#1364) ([issues](https://github.com/steipete/CodexBar/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc)) |
| ccusage / Claude-Code-Usage-Monitor / ccstatusline / Claude-Usage-Tracker | CLI, statusline and menu bar meters | Free | CLI / macOS | 19.0k / 8.7k / 13.3k / 3.7k stars ([ccusage](https://github.com/ccusage/ccusage), [monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor), [ccstatusline](https://github.com/sirmalloc/ccstatusline), [tracker](https://github.com/hamed-elfayome/Claude-Usage-Tracker)) | A commodity |
| SessionWatcher | Paid menu bar and taskbar tracker; handles multiple Claude licences | Solo $6.99 one-time, Bundle $14.99, Pro $24/yr, Teams $40 per seat per year ([TrustMRR](https://trustmrr.com/startup/sessionwatcher)). Says prices rise Nov 1 ([site](https://sessionwatcher.com/)). | Mac, Windows | **$13,024 all-time; $1,748 in 30 days (−41.5%)** [V]. "1,494+ users" [S]. | Revenue is declining against free tools |
| ClaudeUsageBar | Menu bar percentage | Listed as free | macOS | $614 all-time [V] ([TrustMRR](https://trustmrr.com/startup/claudeusagebar)) | n/a |
| Mac App Store clones (20+ since Nov 2025) | Menu bar meters | Mostly free; Orb for Codex costs $4.99 | macOS | Mac ratings: Usage for Claude 4.0/33 ([MAS](https://apps.apple.com/us/app/usage-for-claude/id6755173244)); ClaUse Bar 4.1/10 ([MAS](https://apps.apple.com/us/app/clause-bar/id6759294136)); Code Meter 4.4/9 ([MAS](https://apps.apple.com/us/app/code-meter-claude-codex-usage/id6760511858)); Orb for Codex 1 rating ([MAS](https://apps.apple.com/us/app/orb-for-codex-usage-tracker/id6792640952)); TokenBar 0 ([MAS](https://apps.apple.com/us/app/tokenbar/id6760401627)); AI Limits & Reset Tracker 0 ([MAS](https://apps.apple.com/us/app/ai-limits-reset-tracker/id6758946226)) | 2★ "Often loses connection… no indication on the menubar". 1★ "Requires Claude password… don't feel comfortable". 1★ re-login loops (pages above). |
| **Headroom** | Menu bar app that compresses tool output and logs before they reach Claude Code or Codex; claims about 50% savings | Priced by the plan it stretches: $3–4/mo for Pro, $15–20 for Max x5, $30–40 for Max x20 ([site](https://extraheadroom.com/)) | Mac, Windows, Linux | **$11,107 all-time; MRR $1,827** [V] ([TrustMRR](https://trustmrr.com/startup/headroom)). 7,081 installs [S]. | RTK does a similar job free and open source, with 83.4k stars ([GitHub](https://github.com/rtk-ai/rtk)) |
| VibeMeter | Cost meter for Cursor | Archived | macOS | 387 stars ([GitHub](https://github.com/steipete/VibeMeter)) | Dead |

**Demand driver:** limit pain is real. A Max 20x subscriber hit the weekly cap in about 2.5 hours in July–August 2026 ([upriseri](https://upriseri.com/article/what-are-you-actually-buying-with-a-claude-plan/)). BleepingComputer framed a September limit change as a 17% cut ([BleepingComputer](https://www.bleepingcomputer.com/news/artificial-intelligence/anthropic-is-cutting-claude-codes-current-weekly-limits-by-17-percent/)). See also [issue #9424](https://github.com/anthropics/claude-code/issues/9424).

**Verdict:** meters are a dead end. "Do more within my plan" sells modestly.

### 2.5 Terminals

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Warp | Terminal-based "agentic development environment" | Free. Build includes "$20 of agent usage", Max includes $200, plus Business and Enterprise ([pricing](https://www.warp.dev/pricing), checked 2026-10-15). Build is $20/mo and Business $50 per seat [3P] ([dev.to](https://dev.to/jovan_chan_9500711396d4e6/warp-terminal-review-2026-open-source-ade-the-20-build-plan-and-who-should-actually-pay-for-it-5cin)). | Mac, Linux, Windows | 65.5k stars. Client open-sourced under AGPL on 2026-04-28 ([blog](https://www.warp.dev/blog/warp-is-now-open-source)). Self-reported "+$1M ARR every 10 days" ([PMF Show](https://www.pmf.show/blog/warp-zach-lloyd-agentic-development-environment-1m-arr-every-10-days)). | 5,421 open issues ([GitHub](https://github.com/warpdotdev/warp)). The paid tiers are mainly bundled agent usage, so Warp is effectively reselling inference ([pricing](https://www.warp.dev/pricing)). |
| Ghostty | Fast native terminal | Free (MIT). Became a non-profit through Hack Club in Dec 2025 ([OMG! Ubuntu](https://www.omgubuntu.co.uk/2025/12/ghostty-terminal-non-profit-fiscal-sponsorship)). | Mac, Linux | 62.2k stars ([GitHub](https://github.com/ghostty-org/ghostty)) | n/a |
| iTerm2 / Wave | Terminals | Free ([iterm2.com](https://iterm2.com/); Wave 22.5k stars, [GitHub](https://github.com/wavetermdev/waveterm)) | macOS / cross-platform | n/a | n/a |

**Verdict:** avoid. Nobody pays for the terminal itself.

### 2.6 Screenshots and visual context for agents

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| CleanShot X | Screenshot and recording utility | $29 one-time plus $19/yr for updates; Cloud $8/mo billed annually [3P] ([Setapp comparison](https://setapp.com/app-reviews/cleanshot-x-vs-shottr), [toolradar](https://toolradar.com/tools/cleanshot-x/pricing)) | macOS | Category leader by web coverage [3P] | No agent or CLI hooks found [3P] |
| Shottr | Screenshot utility | $12 one-time [3P] (Setapp, above) | macOS | n/a | No recording [3P] |
| React Grab | Copies a UI element with component name and file:line to paste into an agent | Free open source ([site](https://www.react-grab.com/)) | Browser / React | 7.7k stars ([GitHub](https://github.com/aidenybai/react-grab)) | React only |
| Agentation | Annotates the live UI and sends structured feedback to agents (has MCP) | "Free for individuals and companies for internal use" ([site](https://www.agentation.com/)) | Browser | 5.0k stars ([GitHub](https://github.com/benjitaylor/agentation)) | Desktop-only and needs React 18+ [3P] ([stork.ai](https://www.stork.ai/es/agentation)). It structures feedback but you still need a paid agent ([banani](https://www.banani.co/blog/agentation-dev-review)). |
| PinVari | Point, circle and speak; saves screenshot, marks and words for agents | $39.99 one-time | macOS | **$58 all-time** [V] ([TrustMRR](https://trustmrr.com/startup/pinvari)) | Little demand so far |
| First-party | Cursor 3 Design Mode: select elements in the built-in browser, multi-select and voice since June 2026 ([docs](https://cursor.com/docs/agent/design-mode.md)). Claude Code desktop Browser pane: previews the running app and auto-verifies with screenshots, DOM checks and clicks (Jul 2026) ([docs](https://code.claude.com/docs/en/desktop), [w28](https://code.claude.com/docs/en/whats-new/2026-w28)). | Included | | | |
| Onlook / Stagewise | Visual code editor / browser toolbar repositioned as "The Open Source Agentic IDE" | Open source | Desktop and web | 26.9k / 6.8k stars ([onlook](https://github.com/onlook-dev/onlook), [stagewise](https://github.com/stagewise-io/stagewise)) | Stagewise has left the visual-context niche |

**Verdict:** "show the agent what I mean" is now free (React Grab, Agentation) or first-party. Don't build here.

### 2.7 Dev servers, ports and local domains

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| portless (Vercel Labs) | Named `https://app.localhost` URLs; each worktree gets its own subdomain automatically | Free ([docs](https://port1355.dev/)) | CLI (Node) | 12.7k stars in 8 months ([GitHub](https://github.com/vercel-labs/portless)) | Pre-1.0. HTTP naming only, with no database or service isolation. |
| LocalCan | Pivoted to public URLs and tunnels "for developers, designers and agents", with MCP | Free; Solo $8/mo; Pro $12/mo; Teams $45/mo (3 seats); Lifetime $99 as a limited offer ([pricing](https://www.localcan.com/pricing), checked 2026-10-15) | Mac (+CLI) | Logos of "dev teams" [S] | Competes with ngrok and Cloudflare tunnels |
| Laravel Herd | Native PHP environment | Free. Pro $99 (yearly per one guide), Teams $299 for 10 [3P] ([toolradar](https://toolradar.com/tools/laravel-herd/pricing)). | Mac, Windows | "Loved by thousands" [S] ([site](https://herd.laravel.com/)) | PHP only. Proof that Mac developers pay for local environment tooling. |
| OrbStack | Docker and Linux VMs on Mac | Commercial licence required for businesses earning over $10k/yr ([licensing](https://docs.orbstack.dev/licensing)). ~$8 per user per month [3P] ([toolradar](https://toolradar.com/tools/orbstack/pricing)). | macOS | n/a | Not aware of agents or worktrees |
| PortKiller, Port Kill / Bosun, devglow, Seeports | Menu bar port killers and process managers | The first two are free open source; Bosun (trial) and devglow are paid ([AlternativeTo](https://alternativeto.net/software/port-kill/), [korben](https://korben.info/en/port-kill-macos-app-kill-squatted-ports.html)) | macOS | n/a | A commodity |
| Coasts / workz / isola / lich | Per-worktree service isolation, ports, databases and Compose projects | Free open source | CLI | Coasts 433 stars, HN 99 points ([GitHub](https://github.com/coast-guard/coasts), [HN](https://news.ycombinator.com/item?id=47575417)). lich 10 stars ([GitHub](https://github.com/RPate97/lich)). workz ([HN](https://news.ycombinator.com/item?id=47256056)). | Immature, CLI-only, no GUI |

**Pain evidence:** "Git worktrees isolate files, not processes… agents… fight over :3000, local test databases" ([dev.to](https://dev.to/jsmanifest/parallel-ai-coding-with-git-worktrees-run-multiple-agents-without-conflicts-11na)). One survey says "no tool connects worktree code isolation with full environment isolation" ([zylos](https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development/)). Conductor gives each workspace 10 ports and leaves databases and Docker to user scripts ([env vars](https://www.conductor.build/docs/reference/environment-variables), [first workspace](https://www.conductor.build/docs/first-workspace)).

### 2.8 Secrets for agents

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| 1Password Environments | Mounts `.env` as a named pipe; Claude Code plugin; agent hooks | Part of a 1Password subscription ([docs](https://www.1password.dev/environments/local-env-file), [Claude plugin](https://www.1password.dev/integrations/claude-plugin)). "Trusted access layer for OpenAI's Codex" ([blog](https://1password.com/blog/1password-trusted-access-layer-for-openai-codex)). | Mac and Linux only for local `.env` | Incumbent | Its own hook "does not prevent an authorized process from reading the values" ([agent-hooks](https://github.com/1Password/agent-hooks/blob/main/hooks/1password-validate-mounted-env-files/README.md)). Mounted files "aren't designed for concurrent access", and file watchers such as Vite may restart repeatedly ([1Password docs](https://www.1password.dev/environments/local-env-file); deep dive: [flaviocopes](https://flaviocopes.com/1password-environments/)). |
| Infisical | Secrets platform, now pitched "for… AI Agents" | Pro $20 per identity per month annually, Advanced $40 ([pricing](https://infisical.com/ai/pricing)) | Cloud and self-host | 29.8k stars ([GitHub](https://github.com/Infisical/infisical)) | Team and infrastructure focus |
| Doppler / dotenvx / Bitwarden | Secret managers | Doppler Team $21/user [3P] ([toolradar](https://toolradar.com/tools/doppler/pricing)); dotenvx free, Ops $1.99/mo ([pricing](https://dotenvx.com/pricing)); Bitwarden ([blog](https://bitwarden.com/blog/secure-ai-agent-access-with-secrets-manager/)) | Various | dotenvx 5.8k stars | Bitwarden: Claude Code reads the root `.env` after an auth error, and hiding the file doesn't help |
| LLM Secrets / KeyEnv / Envkeep / EnvManager | Indie vaults that inject secrets per command | LLM Secrets is free under AGPL ([site](https://llmsecrets.com/)); others unpriced ([HN comment](https://news.ycombinator.com/item?id=47210774), [dev.to](https://dev.to/jack_baum_08809d366a13558/i-built-an-encrypted-secrets-manager-so-my-ai-coding-agent-stops-leaking-api-keys-3386), [EnvManager](https://envmanager.com/solutions/secrets-for-ai-agents)) | CLI | No revenue data | All concede that a trusted agent running code can still read the secret |

There is an open feature request for built-in secrets management in Claude Code ([#29910](https://github.com/anthropics/claude-code/issues/29910)).

### 2.9 Sandboxing and permissions

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Docker Sandboxes / Docker Cloud Sandboxes | MicroVMs for Claude Code and Codex (`sbx`) | Local `sbx` is free (Mar 2026). Cloud from $0.07/hr (Micro) to $1.12/hr (XL), launched 2026-09-24 ([how2shout](https://www.how2shout.com/ai/docker-cloud-sandboxes-pricing-agents.html), [Docker](https://www.docker.com/products/docker-sandboxes/)). | Mac and others | Incumbent | n/a |
| Claude Code built-in sandbox | OS-level sandboxing | Included ([Cobus Greyling](https://cobusgreyling.substack.com/p/claude-code-sandboxing), [infralovers](https://www.infralovers.com/blog/2026-02-15-sandboxing-claude-code-macos/)) | Mac, Linux | First-party | n/a |
| Leash (StrongDM) / Agent Safehouse / SandVault / nono / container-use | Policy wrappers and containers | Free open source ([leash](https://github.com/strongdm/leash) 592 stars, [Safehouse](https://agent-safehouse.dev/), [SandVault](https://github.com/webcoyote/sandvault), [nono](https://www.justinmklam.com/posts/2026/05/sandboxing-with-nono/), [container-use](https://github.com/dagger/container-use) 4.1k stars) | Mac and Linux | n/a | No revenue model; free and fragmented |
| E2B and similar cloud sandboxes | Hosted sandboxes | Usage-based | Cloud | 14.4k stars ([GitHub](https://github.com/e2b-dev/E2B)) | Infrastructure, not a desktop app |

**Verdict:** local isolation is free or first-party, and cloud isolation is infrastructure. The paid version is cloud VMs inside ADE subscriptions: Conductor $50/mo, cmux $40–$160/mo.

### 2.10 MCP managers

- **MCP Router:** "development, support and security updates ended 2026-09-18". The final release removes sign-in, billing and cloud sync ([release](https://github.com/mcp-router/mcp-router/releases/tag/v0.6.4)). It had 2.1k stars.
- **ToolHive and MetaMCP:** 2.3k and 2.7k stars, enterprise and self-host oriented ([toolhive](https://github.com/stacklok/toolhive), [metamcp](https://github.com/metatool-ai/metamcp)).
- **Mac App Store managers:** MCP Server Manager has 1 Mac rating ([MAS](https://apps.apple.com/us/app/mcp-server-manager/id6753700883)).

**Verdict: avoid.** A commercial attempt is already dead.

### 2.11 Agent notification apps

- **Free tools:** Claude Code Notifier ([Indie Hackers](https://www.indiehackers.com/post/i-built-a-free-mac-app-that-tells-you-when-claude-code-needs-you-so-you-can-stop-watching-your-terminal-Nem4tXVTIa7HyAV3jgDh)), [claude-status-bar](https://github.com/m1ckc3s/claude-status-bar), [Clabar](https://github.com/Magir/clabar) and [claude-notify](https://github.com/armandsalle/claude-notify).
- **Paid tools:** Trgr: Agent Notification Inbox costs $2.99 and has 0 Mac ratings ([MAS](https://apps.apple.com/us/app/trgr-agent-notification-inbox/id6759818499)). brrr has 3 ratings ([MAS](https://apps.apple.com/us/app/brrr-send-push-notifications/id6755617665)).
- **Built in:** notifications are built into cmux, Conductor and Orca (above).

**Verdict: avoid.**

### 2.12 Design and UI quality for agent-built apps

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Tailwind Plus | Official UI blocks and templates | Was $299 personal / $979 team, one-time. **New sign-ups closed when Tailwind Labs joined Shopify on 2026-09-09** ([AlternativeTo](https://alternativeto.net/news/2026/9/tailwind-labs-joins-shopify-and-keeps-tailwind-css-mit-licensed/)). | Web | Revenue fell about 80% and 75% of engineers were laid off in Jan 2026 ([devclass](https://devclass.com/2026/01/08/tailwind-labs-lays-off-75-percent-of-its-engineers-thanks-to-brutal-impact-of-ai/)) | Agents broke the docs-to-purchase funnel |
| shadcnblocks | shadcn blocks installable through the shadcn CLI and MCP | $149 / $299 / $399 one-time ([pricing](https://www.shadcnblocks.com/pricing), checked 2026-10-15) | Web | "5,420 Pro customers", "22,162 free users" [S] | Exposed to the same AI pressure |
| Efferd | shadcn blocks | One-time | Web | $17,573 all-time [V] ([TrustMRR](https://trustmrr.com/startup/efferd)) | n/a |
| Design skills: ui-ux-pro-max, taste-skill, impeccable, Anthropic frontend-design | Prompt packs that steer agents away from "AI slop" | Free | Any agent | **136.0k / 96.8k / 81.3k stars** ([ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), [taste-skill](https://github.com/Leonxlnx/taste-skill), [impeccable](https://github.com/pbakaus/impeccable)). The skills repo has 181k stars ([anthropics/skills](https://github.com/anthropics/skills)). | Text rules with no visual verification loop ([roundup](https://ruoqijin.com/blog/frontend-design-skills-ai-agents)) |
| **AI Designer** | "We hate the look of AI coded websites": generates UI design | Freemium SaaS | Web | **$78,713 all-time; MRR $9,013** [V] ([TrustMRR](https://trustmrr.com/startup/ai-designer)) | Web generation tool, not wired into the local loop |
| **Skillry** | Paid library of agent skills (websites, slides, visuals) | $9.99/mo, $79/yr, $169 lifetime | Any agent | **MRR $2,470 two months after launch** [V] ([TrustMRR](https://trustmrr.com/startup/skillry)) | Competes with free skills |
| Agensi / cuedesign / UIDrop | Skill store / component library with prompts / design-system extractor | Various | Web | $3,472 / $1,438 / $115 all-time [V] ([agensi](https://trustmrr.com/startup/agensi), [cuedesign](https://trustmrr.com/startup/cuedesign), [uidrop](https://trustmrr.com/startup/uidrop)) | Extraction alone doesn't sell |
| Superdesign | Open-source design agent | Open source (paid tiers not checked) | Editor extension | 7.3k stars ([GitHub](https://github.com/superdesigndev/superdesign)) | n/a |

**Verdict:** static kits are collapsing. Paying for "make agent output look good" is real (AI Designer, Skillry), but free skills set a low price anchor.

### 2.13 Demo videos and launch assets for indie products

| Product | What it does | Price and model | Platform | Traction | Weakness |
|---|---|---|---|---|---|
| Screen Studio | Recorder with automatic zoom and polish | $29/mo or $108/yr. The $229 lifetime was dropped for new buyers in Oct 2025 ([AlternativeTo](https://alternativeto.net/news/2025/10/screen-studio-has-removed-their-non-subscription-licensing-options-for-new-customers/), [cursorclip](https://cursorclip.com/blog/cursorclip-vs-screenstudio/)). | macOS | **25,000 MAU** (founder, May 2026); about 5 staff; no investors ([systemaic](https://www.systemaic.com/teardowns/screen-studio)) | Backlash on r/macapps over subscriptions ([prequel](https://prequel.sh/blog/screen-studio-alternatives)). Fully manual: you re-record every release. |
| Screen Charm / ScreenSage Pro / CursorClip | One-time Screen Studio alternatives | $79–$99; $59 / $99 / $299; $59 lifetime or $7/mo | macOS | **$54,428 / $50,435 / $9,564 all-time** [V] ([screen-charm](https://trustmrr.com/startup/screen-charm), [screensage-pro](https://trustmrr.com/startup/screensage-pro), [cursorclip](https://trustmrr.com/startup/cursorclip)) | Clones keep arriving |
| Prequel / Matte / FocuSee / ScreenKite / debut.sh / Lumiko / Screenshow | More alternatives | $29–$199 one-time | macOS | debut.sh $1,710 all-time and $0 in the last 30 days [V] ([TrustMRR](https://trustmrr.com/startup/debut-sh)). Lumiko $109 [V] ([TrustMRR](https://trustmrr.com/startup/lumiko)). Screenshow $2,136 [V] ([TrustMRR](https://trustmrr.com/startup/screenshow)). | Late clones earn little |
| Cap | Open-source Loom and Screen Studio alternative | Free; desktop licence $29/yr or $58 one-time; Pro ~$12/mo [3P] ([trupeer comparison](https://trupeer.ai/tools-comparison/cap-vs-trupeer-pricing)) | Mac, Windows | 23.3k stars ([GitHub](https://github.com/CapSoftware/Cap)) | n/a |
| Tella / Arcade / Trupeer / Clueso | Async video, interactive demos, AI demo videos | Tella $13–19/mo [3P] ([costbench](https://costbench.com/stats/screen-recording-pricing-2026/)). Arcade Growth $50 per seat per month ([pricing](https://www.arcade.software/pricing), checked 2026-10-15). Trupeer $49/mo ([vendor](https://trupeer.ai/tools-comparison/clueso-vs-trupeer-pricing)). Clueso $120–200/mo [3P] ([pricingsaas](https://pricingsaas.com/companies/clueso)). | Web | B2B | Priced for teams, not solo indies |
| Playwright-to-video open source (Argo, Playwright-recast, aidemo) | Scripted product demos with zoom and AI voiceover | Free | CLI | Argo has 45 stars ([GitHub](https://github.com/shreyaskarnik/argo)); [dev.to](https://dev.to/thepatriczek/i-was-tired-of-re-recording-product-demos-every-sprint-so-i-built-a-tool-that-turns-playwright-21od) | **No commercial end-to-end product found.** Immature. |
| App Store screenshot tools | Device frames, captions, store sizes | ButterKit $79 one-time or $39/yr ([vendor](https://butterkit.app/compare/butterkit-vs-appscreens/)). AppScreens ~$25/mo [3P]. | Mac and web | Picasso 4.5 from 235 Mac ratings ([MAS](https://apps.apple.com/us/app/picasso-app-screenshot-studio/id6472062986)). Screenshot Studio 4.5/75 ([MAS](https://apps.apple.com/us/app/screenshot-studio-app-mockup/id6473832582)). AppMakerKit $7,539, AppMockupGenerator $4,478, Launch Shots $3,159, Appshots $2,829, Lingue $35 all-time [V] ([appmakerkit](https://trustmrr.com/startup/appmakerkit), [appmockupgenerator](https://trustmrr.com/startup/appmockupgenerator), [launch-shots](https://trustmrr.com/startup/launch-shots), [appshots](https://trustmrr.com/startup/appshots), [lingue](https://trustmrr.com/startup/lingue-app-store-screenshot-studio)) | Picasso 3★ "too buggy… exports wrong sized image and apple rejects them… switched to another cheaper non-subscription app" (2026-06-30). Screenshot Studio 3★ "Happy to pay, but please fix the bugs". Mockview 1★ over the paywall ([MAS](https://apps.apple.com/us/app/mockview-mockup-generator/id1592728145)). |
| App Store Connect operators and analytics | Repricing, localisation, insights | MetaRun $15–99/mo; AppSignals $79–499/yr | Web | $0 and $1,289 all-time [V] ([metarun](https://trustmrr.com/startup/metarun), [appsignals](https://trustmrr.com/startup/appsignals)) | Little demand yet |

**Market tailwind:** new App Store submissions rose about 84% year on year in Q1 2026 ([9to5Mac](https://9to5mac.com/2026/04/06/app-store-sees-84-surge-in-new-apps-as-ai-coding-tools-take-off/)). Downloads rose only about 2% in H1 2026 ([TweakTown](https://www.tweaktown.com/news/112818/vibe-coding-is-flooding-the-app-store-with-new-apps-on-track-for-record-submissions-in-2026/index.html)), so more apps compete on presentation.

### 2.14 Other categories with paying users

| Category | Examples and evidence |
|---|---|
| Planning layer above agents | Traycer Lite $20, Pro $40, Ultra $100 per user per month, with credits ([docs](https://docs.traycer.ai/account/pricing)). Plannotator is free with 9.4k stars ([GitHub](https://github.com/backnotprop/plannotator)). |
| Git clients and agent-diff review | GitButler raised a $17M Series A from a16z in Apr 2026 ([a16z](https://a16z.com/announcement/investing-in-gitbutler/)). Tower costs $69–99/yr [3P] ([toolradar](https://toolradar.com/tools/tower/pricing)). Free diff reviewers: [revu](https://eddmann.com/revu/), GitWarren, PostHog Desktop ([docs](https://posthog.com/docs/posthog-desktop/code-review)). Diff review is also built into Conductor, Orca and the Codex app. |
| LLM gateways and routing | LLM Gateway: $1.0M all-time, MRR $78.8k [V] ([TrustMRR](https://trustmrr.com/startup/llm-gateway)). claude-code-router is free with 37.7k stars ([GitHub](https://github.com/musistudio/claude-code-router)). This is cloud resale of inference. |
| Worktree CLIs | Worktrunk is free with 9.2k stars ([GitHub](https://github.com/max-sixty/worktrunk)) |
| Setup kits, history search, skills methodology | ClockedCode Claude Code kit at $39: $123 all-time [V] ([TrustMRR](https://trustmrr.com/startup/clockedcode)). Inventory, AI chat search at $19.99: $43 [V] ([TrustMRR](https://trustmrr.com/startup/inventory)). superpowers is free with 299k stars ([GitHub](https://github.com/obra/superpowers)). |

---

## 3. Gaps, ranked by evidence of willingness to pay

### Gap 1. Repeatable launch assets: demo videos and store screenshots generated from scripts an agent writes

**What developers already spend:**
- Screen Studio sustains a team of 5 on $108/yr subscriptions with 25k MAU ([systemaic](https://www.systemaic.com/teardowns/screen-studio)).
- One-time Mac recorders made $54k and $50k [V] ([Screen Charm](https://trustmrr.com/startup/screen-charm), [ScreenSage](https://trustmrr.com/startup/screensage-pro)).
- B2B demo tools charge $49–$200/mo (Arcade, Trupeer, Clueso).
- App Store screenshot tools earn $3–7.5k [V], and Picasso has 235 Mac ratings.
- New App Store submissions are up 84% ([9to5Mac](https://9to5mac.com/2026/04/06/app-store-sees-84-surge-in-new-apps-as-ai-coding-tools-take-off/)).

**What's weak:**
- Every recorder is manual, so videos must be re-recorded each release.
- Screen Studio's subscription switch caused backlash ([AlternativeTo](https://alternativeto.net/news/2025/10/screen-studio-has-removed-their-non-subscription-licensing-options-for-new-customers/)).
- Screenshot tools are buggy and export wrong sizes that Apple rejects ([Picasso reviews](https://apps.apple.com/us/app/picasso-app-screenshot-studio/id6472062986)).
- Script-to-video tools exist only as immature open-source CLIs ([Argo](https://github.com/shreyaskarnik/argo), 45 stars).

**Possible product:** a Mac app plus CLI/MCP. The agent writes the Playwright, XCUITest or simulator script. The app re-renders a polished video (zooms, cursor, captions, optional voiceover) and every store-size screenshot set on each release, priced one-time.

**Risks:** the recorder market is crowded, and Screen Studio could add scripting.

### Gap 2. Design taste and visual QA for agent-built UIs

**What developers already spend:**
- AI Designer has $9.0k MRR [V] ([TrustMRR](https://trustmrr.com/startup/ai-designer)).
- Skillry reached $2.5k MRR within two months [V] ([TrustMRR](https://trustmrr.com/startup/skillry)).
- shadcnblocks has 5,420 paying customers [S] ([pricing](https://www.shadcnblocks.com/pricing)).
- Free "anti-slop" skills have 81k–136k stars, which shows enormous demand.

**What's weak:**
- Skills are text rules with no visual feedback.
- First-party browsers check that the UI works, not that it is good ([Claude desktop](https://code.claude.com/docs/en/desktop), [Cursor Design Mode](https://cursor.com/docs/agent/design-mode.md)).
- Static kits are dying: Tailwind Plus closed to new buyers ([AlternativeTo](https://alternativeto.net/news/2026/9/tailwind-labs-joins-shopify-and-keeps-tailwind-css-mit-licensed/)).
- Users complain about vibe-coded apps ([Digital Trends](https://www.digitaltrends.com/phones/vibecoded-apps-are-flooding-apples-app-store-and-users-are-getting-sick-of-them/)).

**Possible product:** a local tool that renders the running app across states and breakpoints, scores it against a design system and a "taste" rubric, and emits fix tasks for the agent.

**Risks:** the free skills are good enough for many people, and model progress may close the gap. Extraction-only tools don't sell (UIDrop $115 [V]).

### Gap 3. Doing more within a subscription (limit-aware scheduling, routing and compression)

**What developers already spend:**
- Headroom has $1.8k MRR and $11.1k all-time [V] ([TrustMRR](https://trustmrr.com/startup/headroom)), with 7,081 installs [S] ([site](https://extraheadroom.com/)). It prices by the plan it stretches.
- SessionWatcher made $13k all-time despite free CodexBar [V] ([TrustMRR](https://trustmrr.com/startup/sessionwatcher)).
- Max 20x users hit weekly caps in hours ([upriseri](https://upriseri.com/article/what-are-you-actually-buying-with-a-claude-plan/)).

**What's weak:**
- Meters only observe. CodexBar has Keychain-prompt and lag issues ([issues](https://github.com/steipete/CodexBar/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc)).
- Nobody sells queueing work into reset windows, or routing subtasks to cheaper models and plans.

**Risks:** RTK does compression free with 83k stars ([GitHub](https://github.com/rtk-ai/rtk)). Providers can change limits or terms overnight. The price ceiling is low ($3–40/mo).

### Gap 4. Local per-worktree environments: ports, databases, services and URLs for parallel agents

**Willingness to pay is indirect:**
- Developers pay $40–$160/mo for ADE cloud VMs partly to get isolation ([cmux](https://cmux.com/pricing), [Conductor](https://www.conductor.build/pricing)).
- Mac developers pay for local environment tools: Herd Pro $99, OrbStack's commercial licence, LocalCan $8–45/mo ([localcan](https://www.localcan.com/pricing), [orbstack](https://docs.orbstack.dev/licensing)).

**What's weak:**
- Conductor leaves databases and Docker to user scripts ([docs](https://www.conductor.build/docs/reference/scripts)).
- portless covers HTTP names only ([docs](https://port1355.dev/)).
- Isolation tools are small CLIs: Coasts 433 stars, lich 10.

**Possible product:** "Herd/OrbStack for parallel agents". Copy-on-write database clones per worktree, a port and service namespace, `.localhost` URLs, teardown on merge, and an agent-callable CLI.

**Risks:** ADEs or Docker could absorb this, and there is no direct revenue proof yet.

### Gap 5. Voice for terminal agents (repo-aware vocabulary and routing speech to the right agent)

**What developers already spend:** the category's spend is the largest in this landscape: Wispr Flow at $2B, Superwhisper with hundreds of thousands of weekly users. CNVS sells voice-commanded agents at $99–199 and made $49k [V] ([TrustMRR](https://trustmrr.com/startup/cnvs)).

**What's weak:**
- Identifiers are misheard ([AssemblyAI](https://assemblyai.com/blog/voice-coding-dictate-to-coding-agents)).
- Wispr's code context is IDE-only and cloud-only, and it had a quality dip ([TechCrunch](https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/)).

**Risks:** new generic entrants make $92–$1.3k all-time [V], and Handy is free with 33.8k stars. Only a sharply developer-specific product has a chance.

### Gap 6. Brokering secrets for agents (per-command approval, redaction, audit)

**Willingness to pay is indirect:** it comes through seats developers already pay for, such as Infisical at $20 per identity ([pricing](https://infisical.com/ai/pricing)).

**What's weak:**
- There is real pain and an open feature request ([#29910](https://github.com/anthropics/claude-code/issues/29910)).
- No tool stops an authorized agent from reading a value ([1Password hook docs](https://github.com/1Password/agent-hooks/blob/main/hooks/1password-validate-mounted-env-files/README.md)).

**Risks:** 1Password is already shipping agent integrations, and the indie tools are free and open source.

---

## 4. Categories to avoid

- **Usage meters:** CodexBar is free with 22.5k stars and covers 103 providers. More than 20 Mac App Store clones have 0–33 Mac ratings. SessionWatcher revenue fell 41.5% in 30 days.
- **Agent notifications:** free tools exist, and notifications are built into cmux, Conductor and Orca. Trgr has 0 ratings.
- **MCP managers:** MCP Router shut down on 2026-09-18.
- **Session managers and ADEs:** Orca is free with 92.8k stars, and many more open-source alternatives exist. Vibe Kanban died because users were free. Claude Code agent view, the Codex app and the Cursor 3 Agents Window now cover the job.
- **Terminals:** free open source dominates, and Warp monetizes inference, not the terminal.
- **Desktop context builders:** Repo Prompt went open source, and repomix is free with 28.8k stars.
- **Local sandboxes:** Docker `sbx` is free and Claude Code has a built-in sandbox.
- **Mobile remote control:** Claude Remote Control, Happy (24k stars) and Orca's mobile apps cover it.
- **Visual pointing tools:** React Grab, Agentation, Cursor Design Mode and the Claude desktop browser cover it. PinVari made $58 [V].
- **Generic dictation clones:** they earn $92–$1.3k [V].
- **Static UI kits:** Tailwind Plus closed to new buyers.
- **Port killers:** free open-source tools dominate.

## 5. Method notes

- **Search and discovery:** WebSearch, Exa and HN Algolia (`hn.algolia.com/api/v1/search`). Revenue came from TrustMRR startup pages (`trustmrr.com/startup/<slug>.md`). Mac reviews came from apps.apple.com see-all review pages. GitHub stars came from the GitHub search API on 2026-10-15.
- **Raw data:** saved under `/tmp/claude-0/-home-user-experiments/71b6e69a-350a-5a54-b87d-67380633b427/scratchpad/research/raw/`.
- **Competitor-authored sources:** many third-party pricing pages are written by competitors (getvoibe, cursorclip, prequel, butterkit, trupeer). They are marked [3P] and should be re-checked before quoting externally.
- **TrustMRR coverage:** TrustMRR only covers founders who opt in. It under-represents larger players, so absence of a listing doesn't mean absence of revenue.
