# Run 002: Staying in the room with users when building takes five minutes

- **Asker:** Ethan Wickstrom
- **Date:** 2026-11-26 (draft; not yet sent)
- **Bet id:** pending (record in `bets.jsonl` right before the first message goes out)

## Before asking

- **Problem, in the asker's words:**
  I've been building software for people since I was eight, and the hardest part has consistently been figuring out what is actually worth building. When I ran Minecraft servers, working inside the server meant spending hours alongside my users. I learned things I wouldn't have known to ask about. As I've moved on to building other software, I've found that this kind of continuous, incidental contact with users is much harder to recreate. AI is making implementation extraordinarily cheap, but much of the knowledge I need to decide what to implement historically came from the building process itself. I haven't figured out how to preserve that.

- **What people do now, and what it costs:**
  - Rely on analytics dashboards alone, which tell you what happened without why or how it felt ("like the shop owner staying in his office, poring over spreadsheets, rather than walking through the shop floor", Paul Adams, 2014).
  - Ask users hypothetical questions ("Would you use feature X?"), which trigger authority bias and the query effect so users invent stories about things they never needed (Paul Adams, 2013).
  - Run heavy, scheduled user-research sessions or literal in-person observation (Intuit's Follow Me Home, 1984 onward), which take hours per user and rarely stay continuous once a solo builder is shipping with agents.
  - Watch live escape hatches users build themselves (Viaweb's RTML scripting language becoming an unintentional suggestion box, Paul Graham, 2001), which only works when the software already has an escape hatch and the builder is watching it live.

- **People who named this problem (verified primary sources; ask list to be filled with active solo/AI builders who stated it recently):**
  - **Paul Graham** (Viaweb, 2001) — [The Other Road Ahead](https://paulgrahamessays.com/road.html): "you can't have any idea what users will be thinking, believe me, until you watch them... RTML became a kind of suggestion box, because users only used it when the predefined page styles couldn't do what they wanted."
  - **Paul Adams** (Intercom, 2013–2014) — [Asking customers what you want to hear](https://www.intercom.com/blog/asking-customers-what-you-want-to-hear) and [The blind product manager](https://www.intercom.com/blog/the-blind-product-manager): hypothetical questions create false demand; analytics alone blind product teams to why users struggle.
  - **Scott Cook** (Intuit, 1984+) — [Inc. profile (2004)](https://www.inc.com/magazine/20040401/25cook.html) and [Inc. (1995)](https://www.inc.com/articles/1995/01/11165.html): Follow Me Home — watching new buyers install and use Quicken silently to spot every pause and confusion.

- **People to ask (all strangers; active 2026 solo builders who publicly stated this problem):**
  1. **Muhamad J. Akoum** (stranger) — [Building a Product Solo With AI](https://akoum.me/blog/built-solo-with-ai-and-what-it-didnt-do) (2026-07-04): "An agent can draft a message, produce a landing-page variant, or cluster interview notes. It cannot make another person care, and it cannot notice the weight behind a hesitation unless I am present enough to hear it."
  2. **Piotr Czerwinski** (stranger) — [Running a Product Solo With AI Agents: 8 Months In](https://piotrczerwinski.dev/writing/ai-agents-as-co-engineers) (2026-07-24): "Product decisions. Which feature to build, which segment to serve, what to cut. An agent will happily argue any position with equal confidence. The decision quality comes from talking to users and watching real behavior, and no model does that for me."
  3. **Daniel Goldman** (stranger) — [When AI Writes Most of the Code, My Job Is Deciding What Not to Build](https://danielthegoldman.com/blog/when-ai-writes-most-of-the-code-my-job-is-deciding-what-not-to-build/en/) (2026-09-01): "what decides whether a product works has nothing to do with who typed the code. It's how fast I decide what to build, what to skip, and what to reject outright."
  4. **Stefan-Iulian Tesoi** (stranger) — [Solo founder coding agents: shipping a product alone](https://laimonade.com/blog/running-a-product-single-handed-with-coding-agents) (2026-09-24): "They help least with the work where knowing what to build is the work. That distinction matters more when you are alone, because a team has people whose judgement differs from yours and a solo founder has only the agent's agreement."
  5. **Martin Dimoski** (stranger) — [Building Got Cheap. Judgement Didn't.](https://martindimoski.dev/blog/building-got-cheap) (2026-10-17): "Three things took exactly as long as they always have. Deciding what is worth building... Knowing whether it is any good... Knowing what 'right' means."
  6. **Nan Liang** (stranger) — [I Built a Few Products Nobody Used: Honest Lessons](https://javaeye.dev/blog/first-products-nobody-used/) (2026-09-29): shipped multiple AI-built tools with zero revenue; "The products went live, and then nothing happened. No users, no feedback."

- **Proposed stake:**
  A change to their work plus booked time: connect one live product with active users (or share 5 recent unedited user sessions / support threads) and book a 20-minute live working session next week to review the unasked-for friction and workarounds found in real usage. Both must be in hand for a yes to count.

- **Delivery date, and what is returned if it is missed:**
  Within 5 days of receiving access, deliver one concrete change worth building (and one requested feature worth refusing) backed by unedited moments from their actual users — things the builder did not ask about. If missed, a public failure note is sent to them.

- **Proposed rule (fix before sending):**
  At least 2 of the 6 builders (or 3 of 10 if 4 more are added) put up the stake within 48 hours of being asked. Silence is a no.

## Draft message (for Ethan to edit and send; agent sends nothing per V4)

> Subject: your post on [their post title]
>
> I read your post on [specific 1-line detail from their post]. I've hit the same wall: when implementation took hours alongside users, I overheard what was actually broken without knowing to ask. When coding agents shrink the build to minutes, that incidental contact disappears.
>
> I'm testing whether a solo builder can get the same unasked-for user signal continuously without living in support threads or asking leading "would you use X?" questions.
>
> If you'll connect one live product with active users (or share 5 recent unedited user sessions / support threads) and book 20 minutes next week, I'll deliver one concrete change worth building and one requested feature worth refusing within 5 days, backed by unedited moments from your users. If I miss the date or it isn't useful on the call, I'll send you a short note on what failed.
>
> Worth 20 minutes, or have you already found a way to stay close to users?

## Answers
| Person | Tie | Answer | Stake in hand? | Counts? |
|---|---|---|---|---|

## Verdict
- **Rule met?**
- **What the people who said no do instead:**

## Six weeks
- **Outcome named on day one:** During week six (days 36 to 42), without prompting, at least half of the builders who put up the stake have shipped or refused a change citing a new unprompted user moment from live usage observed in weeks five or six (not the week-one report; V7).
- **Result on day 42:**
