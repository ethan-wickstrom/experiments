# Sizewise developer launch: plan and measurement

Target: $10,000 from strangers by 31 December 2026. Today: $0 from strangers (Sizewise's own sales so far unknown; asked Ethan).

## The test

- Pass: 10 paid licenses from strangers within 7 days of the first public post.
- First post: by Tuesday 20 October 2026.
- Under 3 paid licenses in 7 days: run the runner-up (design pass for agent-built web apps).
- 3 to 9: keep Sizewise as a slow search business and run the runner-up anyway.

## Sequence (each step needs Ethan's account; drafts are in this folder)

| Day | Where | What | Draft |
|---|---|---|---|
| 0, a weekday 8 to 10am US Eastern | Hacker News | Show HN of https://getsizewise.app/macos, then the first comment | hn-macos-page.md |
| 0 | X | One post with a screenshot of the /macos map, linking the page. No ask for upvotes. | waits on Ethan's voice samples |
| 1 or 2 | r/MacApps | Sizewise post under Tier 2, Problem / Comparison / Pricing | r-macapps.md |
| 1 to 7 | Reddit, X, GitHub | Replies to people who described the problem, each useful on its own, each saying how we found them | outreach.md (in progress) |
| 5 to 7 | Hacker News | Show HN for Sizewise itself, only if the /macos post didn't already bring the app most of its traffic | show-hn.md |

Rules that apply to every post: no friends asked to upvote; answer every comment for the first two hours; no em dashes on Reddit (auto-removal); never post the same text twice; every claim true of Sizewise 1.4 as shipped.

## What to measure (Ethan reads these; I keep the scoreboard)

- Paid licenses and revenue: Polar dashboard, orders by day.
- Where buyers came from: Cloudflare Web Analytics referrers for getsizewise.app (news.ycombinator.com, reddit.com, t.co/x.com, github.com, search), daily, from day 0.
- Downloads: requests for the .dmg through the site's Worker (Cloudflare), daily.
- Conversion: licenses divided by downloads, and downloads divided by visits.

## After the test

- If it passes: the developer lens is worth building (worktrees, build folders, model caches as named rows in Not in this map or in the legend), and the price deserves a test (DaisyDisk is $9.99; Proxyman and TablePlus buyers pay $89 to $99 for depth).
- Either way: an `llms.txt` and the developer guide page help assistants recommend Sizewise, which compounds.
