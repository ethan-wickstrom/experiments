# Replies to people who described the problem

Status: drafts for Ethan. Nothing is posted. Threads re-read on 2026-10-15 (Reddit through the Arctic Shift archive, HN through Algolia, GitHub with WebFetch). The full list of 39 people is in `../research/outreach.md`.

Voice: written in the voice of getsizewise.app, because I haven't seen your X posts. Change anything that doesn't sound like you before posting.

## What the re-check changed

Most of the 39 had their answer within hours of posting, so a reply now would land on a solved thread.

- u/cecoondog (r/MacOS, 214 comments) bought DaisyDisk four and a half hours after posting, on commenters' advice, and found 137 GB of media cache in five minutes: "It was $9.99 and you get a lifetime registration for up to 5 Mac's. Best $10 purchase I've ever made." They had passed on Mole and OnyX as "too techie". Another commenter downloaded DaisyDisk from the same thread. ([thread](https://www.reddit.com/r/MacOS/comments/1x3hej6/))
- u/joseeek fixed theirs with Mole. u/adecareddit found two Time Machine snapshots. u/TimJamesS restarted. u/TheUsualSuspect_____ dropped 130 GB after a macOS update. Apple told u/melvin3v1978 that connecting their external SSD creates a temporary snapshot of about 90 GB.
- Developers increasingly ask their agent. On HN, icantevenhold "asked Claude where all my disk space went and it gave me a really useful breakdown" ([comment](https://news.ycombinator.com/item?id=50064993)). In r/codex's "Codex disk usage" thread, the most upvoted comment asks "Can Codex prune this back?" and the answer under it is "It can. It's pretty good at it too" ([thread](https://www.reddit.com/r/codex/comments/1x1ytxw/)).
- All five HN comments already have answers. A disk-app maker offered Gigachad a free lifetime license, so a second maker replying there would look worse than silence.
- Disk-app makers already work these threads: neodisk.app, SpaceWise, FinderTools, Diskaroo, Mole's author. On funky_surprise's r/mac thread, a moderator removed one maker's answer ("Promotion/ advertisement is against r/mac's rules"), after another user called it an AI answer posted "because you're trying to sell your garbage software".

Subreddit rules, read from the Arctic Shift rules endpoint: r/mac bans self-promotion outright; r/macbookpro and r/macbookair ban promotion; r/MacOS rule 6 says "If you wish to promote something you have created or are involved with, please contact the moderators via Modmail first." r/codex's rules page is stale (it still describes a bookbinding subreddit). r/ClaudeCode's couldn't be read from here.

So the drafts follow three rules:

1. Replies in the Mac subreddits name no app. They help, and that's all.
2. Sizewise is named in one reply where it fits exactly (a disk that refills overnight, in r/codex), with how I found the person and the price. A second mention links the agent-disk guide, and only once that page is live.
3. The modmail below asks r/MacOS for the one post that reaches the people who pay: macOS 27 users watching System Data grow.

Every reply that names Sizewise says how I found the person. The help-only replies answer a public request for help, so they need no explanation.

## Order

1. **Today, 2026-10-15:** u/BrownCowStunning_ (posted yesterday, three comments, the poster is replying).
2. **By 2026-10-17:** the r/MacOS modmail, so the answer arrives before the first post on 2026-10-20. Then u/Calrose_rice and u/andysurtees.
3. **Optional, this week:** u/rongw2, u/Federal-Glove-3200, u/radim11, u/pp_amorim, mrmachine on GitHub.

Post from the Reddit account you'll use for r/MacApps. Its Tier 2 rules ask for a real identity anyway.

---

## 1. Modmail to r/MacOS

Send at https://www.reddit.com/message/compose?to=/r/MacOS

Subject: Asking first: a map of every file macOS 27 puts on a Mac

~~~text
Hi, I make Sizewise, a disk space app for the Mac, so per rule 6 I'm asking before posting anything connected to it.

I scanned the signed system volume and cryptexes of macOS 27.0.1 and 26.5.1 and put both on one page as a map you can zoom into, colored by what changed between them: https://getsizewise.app/macos

It's free, needs no signup, and holds no one's personal files. It answers a question that keeps coming up here: 27.0.1 takes 4.37 GB more than 26.5.1, and the biggest change is a new 7.3 GB Rosetta cryptex.

Under the map there's a short section about my app. May I post the page once? If the answer is no, that's fine.

Ethan Wickstrom
~~~

Facts checked: the numbers are the ones the live page shows (see `hn-macos-page.md`, "Numbers check").

---

## 2. u/BrownCowStunning_, r/MacOS, help only

<https://www.reddit.com/r/MacOS/comments/1x640lz/>, posted 2026-10-14. "Just got a new MacBookPro a bit more than 2 weeks ago and since yesterday, my storage has been completely flooded". Over 800 GB of System Data on a 1 TB disk. They moved their old Mac's data over, already checked Time Machine and /Library/Caches, and OmniDiskSweeper found nothing. Thread now: one reply says OmniDiskSweeper needs Full Disk Access; another suggests a reset, and they asked whether to reset and move everything over by hand. Unsolved.

~~~text
I wouldn't reset it yet. If an app or a setting is writing nonstop, it comes back with your data after a reset.

Part of the number may be space macOS clears by itself: since macOS 27, System Data includes caches and Time Machine snapshots that older versions listed as purgeable ([Apple Community user tip](https://discussions.apple.com/docs/DOC-250012471)). But hundreds of GB in a day means something wrote them, so find what's writing:

1. Open Activity Monitor, click Disk, and sort by Bytes Written. A process near the top with hundreds of GB written is your answer. On a new Mac with migrated data it's often a sync app (iCloud Photos, Dropbox, Google Drive) downloading everything, or a virtual machine.
2. In Terminal, `tmutil listlocalsnapshots /` lists Time Machine's local snapshots, which never show up as files.
3. To find the folder, give Terminal Full Disk Access (System Settings > Privacy & Security > Full Disk Access) and run:

        sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h | tail -15

    It takes a few minutes. Run it again on the biggest folder to go one level deeper.
~~~

Checked: the user tip by neuroanatomist (last modified 2026-10-03) says purgeable data "are now included in System Data" on macOS 27. Apple's Activity Monitor guide says the Disk pane shows the amount of data each process reads and writes ([View disk activity](https://support.apple.com/guide/activity-monitor/view-disk-activity-actmntr1005/mac)). `du`, `sort -h` and `tmutil listlocalsnapshots` are standard macOS commands.

---

## 3. u/Calrose_rice, r/codex, names Sizewise

<https://www.reddit.com/r/codex/comments/1x1ytxw/comment/pf0898j/>, 2026-10-10. "Disk usage always at 100% like I cleared 100gb and then the next day I'm already full up. It's crashing my computer daily." On a Mac per their other posts (MacBook Pro 2021). No replies to their comment. A disk that refills overnight is what Show Changes is for, so this is the one reply that names the app.

~~~text
If it refills overnight, it's usually one of these. Each has a report on the Codex GitHub from the last few weeks:

    du -sh ~/.codex/sessions ~/.codex/worktrees "$TMPDIR" /private/tmp ~/Library/Application\ Support/Codex/Crashpad/pending ~/Library/Caches/com.openai.codex 2>/dev/null

Run it now and again tomorrow, and see which one grew.

- `$TMPDIR` filling with tmp.* folders and tmp_pack files: workspace diffs leave temporary Git data behind, and one person reached 424 GB ([#43158](https://github.com/openai/codex/issues/43158)). In that thread, adding big generated files in the repo (videos, screenshots) to .gitignore stopped new folders appearing. Don't empty all of `$TMPDIR`, other apps use it too.
- Crashpad/pending: a crash-report loop that reached 168 GB ([#52194](https://github.com/openai/codex/issues/52194)). A reboot stopped it for that person. Clear the folder with Codex closed.
- ~/.codex/worktrees or /private/tmp: worktrees and run copies that the keep count doesn't clean up ([#35383](https://github.com/openai/codex/issues/35383)). Archive chats you're done with, or `git worktree remove` them.
- ~/Library/Caches/com.openai.codex: every auto-update leaves the previous app behind, about 1.5 GB each time ([#49803](https://github.com/openai/codex/issues/49803)).
- ~/.codex/sessions: transcripts stay until you delete them. `codex delete` removes one.

I found your comment while searching r/codex for disk-space posts. I make Sizewise, a disk map app for the Mac that does this comparison on a map: scan your home folder today and again tomorrow, and Show Changes colors what grew. Scanning is free, and Show Changes is part of the $12.99 license. The du line does the same job in text.
~~~

Checked on GitHub, 2026-10-15: #43158 open (paths `$TMPDIR/tmp.*` with `tmp_pack_*`, 424 GiB from one reporter, the .gitignore workaround from the original reporter); #52194 closed by its reporter (168 GB, reboot fixed it, OpenAI support advised clearing with the app closed); #35383 open (61 worktrees, about 100 GB, with the keep count set to 10; 202 GB of run copies in /private/tmp); #49803 open (about 1.5 GB per update in `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle/Installation/`). Sessions and `codex delete`: Codex's docs, cited in `agent-disk/agent-disk.md` rows 25 to 27. Sizewise pricing: the 1.4 release notes.

---

## 4. u/andysurtees, r/codex

<https://www.reddit.com/r/codex/comments/1wnp5q6/>, 2026-09-22, title "800gb of worktrees?". "Now I realise my SSD is completely full, half of which is the .codex folder, mostly worktrees." Two replies: a bot, and "Just put a cleanup unneeded test files and worktrees statement in your agents.md". Mac not stated (Codex's desktop app suggests a Mac, a guess). The last paragraph names Sizewise; post it only once https://getsizewise.app/agent-disk is live, and drop it otherwise.

~~~text
Codex's docs say the app keeps your 15 most recent worktrees and deletes older ones, and deletes a chat's worktree when you archive the chat, after saving a snapshot you can restore. Worktrees the CLI makes with --worktree aren't cleaned up at all. And several people report the keep count isn't enforced: one had 61 worktrees, about 100 GB, with it set to 10 ([openai/codex#35383](https://github.com/openai/codex/issues/35383)).

What works:

1. Archive the chats you're done with, so Codex removes their worktrees itself. It keeps pinned and running chats' worktrees.
2. For the rest, run `git worktree list` in each repo, then `git worktree remove <path>` for the ones you're done with. Git refuses when a worktree has uncommitted or untracked files, which makes a good safety check. Then run `git worktree prune`.
3. Check `du -sh ~/.codex/sessions` too. Transcripts stay until you delete them: archiving only moves them to archived_sessions, and `codex delete` removes one.

Settings > Worktrees > Worktree root changes where new worktrees go, if you'd rather keep them on another drive.

I found your post while searching r/codex for disk-space posts. I make a Mac disk app, Sizewise, and wrote up where Codex, Claude Code, Cursor and Conductor keep worktrees and how each one cleans up, with sources: https://getsizewise.app/agent-disk
~~~

Checked: Codex's worktree docs and source, and git's docs, as cited in `agent-disk/agent-disk.md` rows 6, 21 to 27; #35383 read on 2026-10-15.

---

## 5. u/rongw2, r/codex, help only (optional)

<https://www.reddit.com/r/codex/comments/1x1ytxw/comment/pexw6nb/>, 2026-10-09. "i had to uninstall it after it added 50gb of garbage in 3 weeks. Simply unusable." Mac not stated, so the Mac path is conditional.

~~~text
Uninstalling probably didn't give those 50 GB back. Codex keeps sessions and worktrees in ~/.codex, outside the app, so deleting the app leaves them. `du -sh ~/.codex/* | sort -h` shows what's there, and on a Mac ~/Library/Application Support/Codex can hold more (crash reports reached 168 GB for one person). Check ~/.codex/worktrees for work you haven't pushed before you delete anything. The folder also holds your settings and sign-in.
~~~

Checked: `agent-disk/agent-disk.md` rows 21, 25 and 76; #52194.

---

## 6. u/Federal-Glove-3200, r/ClaudeCode, help only (optional)

<https://www.reddit.com/r/ClaudeCode/comments/1wsmwjp/>, 2026-09-28. "My Mac mini only has 256GB of storage, and since I started vibe coding iOS apps, I'm constantly running out of space." They run a Mole automation below 5 GB free and plan to buy external SSDs. u/verstands already gave the strategy (repos inside, rebuildable data outside), so this adds the exact settings.

~~~text
Adding the exact switches to verstands' list, since Xcode is usually the biggest piece of an iOS setup:

- DerivedData: Xcode > Settings > Locations, set Derived Data to Custom and pick a folder on the SSD. Everything in it rebuilds.
- Simulator runtimes live in /Library/Developer/CoreSimulator, outside your home folder, several GB per iOS version. Delete the ones you don't test on in Xcode > Settings > Components: click the info button next to one, then Delete.
- `xcrun simctl delete unavailable` deletes the simulators your current Xcode doesn't support, with their apps and data.
- ~/Library/Developer/Xcode/iOS DeviceSupport keeps a folder for each iOS version you've plugged in. Old versions can go, except any you still read crash logs from.
- Claude Code puts worktrees in .claude/worktrees inside each repo. It removes a clean one when you exit, but runs with -p leave theirs behind.
~~~

Checked: getsizewise.app/xcode-storage and its Apple sources (Components pane, DeviceSupport, `simctl delete unavailable`); "several GB per iOS version" from u/lil_curry_verse's two iOS 18 runtimes taking about 18.25 GB ([post](https://www.reddit.com/r/MacOS/comments/1wgqmtd/)); Claude Code behavior from `agent-disk/agent-disk.md` rows 10 to 13.

---

## 7. u/radim11, r/ClaudeCode, help only (optional)

<https://www.reddit.com/r/ClaudeCode/comments/1wsmwjp/comment/pcyil9u/>, 2026-09-30. "Having 256GB on Mac is just not much for serious work." Multiple repos and Docker containers; uses Mole "from time to time".

~~~text
If that's Docker Desktop, its disk image is often the biggest single thing on a 256 GB Mac, and Finder shows it bigger than it is. Docker.raw is a sparse file, and this prints the space it takes first and its maximum size after:

    ls -klsh ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw

`docker system df` shows what's reclaimable. `docker system prune` removes stopped containers, unused networks, dangling images and build cache; add -a to remove every image no container uses, but push or `docker save` images you built first. Docker says the space comes back to the Mac a few minutes after images are deleted, and `docker run --privileged --pid=host docker/desktop-reclaim-space` asks for it at once.

Settings > Resources > Advanced also has a slider for the image's maximum size, but Docker warns that lowering it deletes the disk image, with every container and image in it.
~~~

Checked: getsizewise.app/docker-disk and the Docker docs it cites (Mac FAQ, `docker system df`, `docker system prune`).

---

## 8. u/pp_amorim, r/cursor, help only (optional)

<https://www.reddit.com/r/cursor/comments/1w8558g/comment/p88jbkx/>, 2026-09-06. "Cursor eats around 50 gb of storage every day." A guess that it's a Mac (their other posts mention their team's Mac mini).

~~~text
If Cursor's agents use worktrees, look there first: they live in ~/.cursor/worktrees, a folder per repo, and each one gets its own node_modules and build output once something installs or builds in it. Since Cursor 3.5 it keeps at most 25 across all projects by default (the cursor.worktreeMaxCount setting), and /delete-worktree removes one. This shows whether it's the worktrees or Cursor's own app data that keeps growing:

    du -sh ~/.cursor/worktrees/* ~/Library/Application\ Support/Cursor 2>/dev/null | sort -h
~~~

Checked: Cursor's docs, cited in `agent-disk/agent-disk.md` rows 39 and 40; row 3 for ignored folders in new worktrees.

---

## 9. mrmachine, orbstack/orbstack#2691, help only (optional)

<https://github.com/orbstack/orbstack/issues/2691>, opened 2026-09-11, open, no replies. "Codex said I had 119MB free but Finder says 240GB free. Daisy Disk says 240GB free + purgeable." OrbStack 2.2.1 stopped with Storage Full on macOS 26.5.2. The footer marks the text as drafted with Claude Code; keep it if you post the text as is.

~~~text
This looks like the purgeable-space gap. On macOS 26, Finder's figure counts purgeable space as available (caches, iCloud files that are also in the cloud, and Time Machine's local snapshots, which macOS clears when something needs the room), while `df` and Disk Utility's Free figure show only what's free right now. Apple says snapshots don't take the space needed "for tasks like downloading files, copying files, or installing new software", but in Howard Oakley's tests Finder itself refused a copy for lack of space while showing that space as available: https://eclecticlight.co/2023/04/17/the-finder-confuses-with-wildly-inaccurate-figures-for-available-space/

Until OrbStack handles it, turning snapshots into real free space before heavy container work should avoid the error:

    tmutil listlocalsnapshots /
    tmutil deletelocalsnapshots <date>    # for each one listed

Disk Utility does the same under View > Show APFS Snapshots. Then compare `df -h /System/Volumes/Data` with Finder's number.

On macOS 27 this changes: according to an Apple Community user tip, purgeable space is no longer counted as available there, so Finder and OrbStack should agree on what's free: https://discussions.apple.com/docs/DOC-250012471

---
_Generated by [Claude Code](https://claude.ai/code)_
~~~

Checked: getsizewise.app/purgeable-space and its sources (Apple's Storage and Time Machine pages, Oakley's tests, `tmutil deletelocalsnapshots`); the user tip read on 2026-10-15.

---

## Dropped after the re-check

- u/cecoondog, u/joseeek, u/adecareddit, u/TimJamesS, u/TheUsualSuspect_____, u/melvin3v1978, u/Odd-Anything1768, u/Independent_Syllabub: solved (DaisyDisk, Mole, snapshots, restart, update, Apple's answer, own cleanup, own cron script).
- u/GoPhotoshopYourself, u/nicejaelle, u/ineed100000gecs, u/jchannon, u/Beatsu, u/Shuma665: several good answers already; a reply would repeat them.
- u/Kremiorspokke: their screenshot is Mole's view of /Library/Developer (CoreSimulator, 60.9 GB), and the one reply already gives the fix (Xcode Settings, plus a Stack Overflow link).
- u/thebananageek94: talking to another app's maker about Messages attachments, which Sizewise doesn't handle.
- u/funky_surprise: a moderator removed a maker's answer on the r/mac copy; on r/MacOS another user found most of the gap was GiB against GB.
- u/No_Accident8684, u/Infamous_Tomatillo53: the disk comment sits in an unrelated thread or a vent post.
- HN (antoineMoPa, icantevenhold, busymom0, singularity2001, Gigachad): all answered; icantevenhold fixed it by asking Claude; a maker already pitched Gigachad.
- GitHub aunitt (claude-code#99672): the issue already describes the WorktreeCreate hook with `cp -c` as the reporter's own workaround, so a reply adds nothing. uaalah, aervium, LinusAuditore, mandyleidinger, dellapolla-lab: issues already document the cause and the reporter's workaround; nothing to add beyond a +1.
- lmaodzedun / u/jeerobus (1.43 TB): the poster hasn't replied to anyone in a month.

New posts like these appear daily (30 of the 39 came in the last three weeks), and they get answered within hours. If you want to keep helping, it has to be the same day.
