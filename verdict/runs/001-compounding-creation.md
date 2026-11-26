# Run 001: Compounding creation without maintenance drag

- **Asker:** Ethan Wickstrom
- **Date:** 2026-11-26 (draft; not yet sent)
- **Bet id:** pending (record in `bets.jsonl` right before the first message goes out)

## Before asking

- **Problem, in the asker's words:**
  The more I create, the more I become responsible for maintaining. When I move on to another project, knowledge gets lost, software becomes outdated, experiments go undocumented, and previous commitments continue to require my attention. Returning to old projects often means reconstructing knowledge I once had. Documentation, knowledge management, automation, and better software architecture each introduce responsibilities of their own. I want each thing I build to increase my capacity to build the next thing, rather than diminish it.

  A second constraint from the asker's own experience (2026-11-26): making building take 5 minutes without staying in the live world of users loses the unsolicited context you only hear by being present, and a feature someone asks for is not always what the project needs.

- **What people do now, and what it costs:**
  - Hand-kept docs, ledgers and decision logs (in this repository alone: 487 lines across three project ledgers), which decay whenever attention moves.
  - Artificial caps on creation: coding every day to avoid multi-week context loss (Resig), stopping side projects for three years (Hall), capping active projects at one on a Kanban board (Schmelyun), deleting ~50 AI-built projects and considering cancelling an AI subscription (Wilson), or hoping for "discipline" (Willison).
  - Abandoning projects that are still useful when upkeep exceeds value (Hoffman).

- **People to ask (all strangers unless noted; each stated this problem publicly):**
  1. **David Wilson** (stranger) — [The solution might be cancelling my AI subscription](https://thoughts.hmmz.org/2026-05-31.html) (2026-05-31): spun up 16+ AI projects and deleted ~50; "I can't afford to maintain any of them, not in terms of time, commitment, belief, attention or willingness to spend on tokens."
  2. **Simon Willison** (stranger) — [The solution might be cancelling my AI subscription](https://simonwillison.net/2026/May/31/the-solution-might-be-cancelling-my-ai-subscription/) (2026-05-31): "Even if the code is rock solid, there's a limit to how many projects like that I can sensibly care for - and if they're instantly abandoned, what value was there from creating them in the first place?"
  3. **Andrew Schmelyun** (stranger) — [The crippling problem of being able to build whatever you want](https://www.aschmelyun.com/blog/the-crippling-problem-of-being-able-to-build-whatever-you-want/) (2023-10-26): 143 ideas in backlog; "The more projects you release, the more potential time you lose with recurring support and maintenance."
  4. **Matthew Hall** (stranger) — [Build Maintainable Side Projects](https://matthewhall.com/posts/build-maintainable-side-projects/) (2019-12-09): left users behind on GrowlerFill and Ferries App; killed a USB-C database over ongoing maintenance burden.
  5. **John Resig** (stranger) — [Write Code Every Day](https://johnresig.com/blog/write-code-every-day/) (2014-04-10): "a week between working on some code is a long time, it's very easy to forget what you were working on or what you left off on (even if you keep notes)... I've had many side projects die due to attention starvation."
  6. **Karly Hoffman** (stranger) — [Reviving an Abandoned Side Project with Spec-Driven Development](https://dev.to/karlyhoffman/reviving-an-abandoned-side-project-with-speckit-and-copilot-3517) (2026-06-07): stopped maintaining a recipe app she used every week because upkeep exceeded value.
  7. **Diego Cervera** (stranger) — [The Hard Part About Consistency When Building Products](https://journal.messyfounder.com/the-hard-part-about-consistency-when-building-products-a0e65acdf9cf) (2026-06-15): accumulated solo projects with no structure to sustain them once initial excitement fades.

- **Proposed stake (requires no payment account yet):**
  A change to their work plus booked time: grant read access to 2 real repositories (one active, one untouched for 30+ days) and book a 20-minute live working session next week to return to the paused repo and review live user/dependency drift in the active one, with zero manual documentation written by them. (If R3 is set up before sending, optionally pair with a refundable deposit.)

- **Delivery date, and what is returned if it is missed:**
  Within 5 days of receiving repo access, deliver a runnable re-entry brief for the paused repo (what it does, why recent choices were made, what broke since they left, what is waiting for a human call) and a zero-noise drift report for the active repo. If missed, any deposit is refunded in full and a public failure note is sent to them.

- **Proposed rule (fix before sending):**
  At least 2 of the 7 builders (or 3 of 10 if 3 more are added) put up the stake within 48 hours of being asked. Silence is a no.

## Draft message (for Ethan to edit and send; agent sends nothing per V4)

> Subject: your post on [their post title]
>
> I read your post on [specific 1-line detail from their post]. I've lived with the same problem for years: every project I build adds maintenance and context-reconstruction debt that slows down the next one, and docs/automation become one more thing to maintain.
>
> I'm testing whether a paused project can have zero re-entry tax and an active project can surface only what actually needs your judgment, without you writing or maintaining any docs.
>
> If you'll point me at 2 real repos (one active, one you haven't touched in 30+ days) and book 20 minutes next week, I'll have a live re-entry brief and drift report in your hands within 5 days. If I miss that date or it isn't useful on the call, you owe nothing and I'll send you a short note on what failed.
>
> Worth 20 minutes, or have you already solved this for yourself?

## Answers
| Person | Tie | Answer | Stake in hand? | Counts? |
|---|---|---|---|---|

## Verdict
- **Rule met?**
- **What the people who said no do instead:**

## Six weeks
- **Outcome named on day one:** On day 42, without prompting, the builder ships a real change to a previously paused project using the brief, or pays for a second month.
- **Result on day 42:**
