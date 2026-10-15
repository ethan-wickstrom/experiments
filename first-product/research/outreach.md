# Sizewise launch outreach list: people who described Mac disk-space pain (2026-09-01 to 2026-10-15)

Compiled 2026-10-15. There are 39 people. Each one described their own problem in public. Each entry gives the link, a verbatim quote, what is filling the disk, whether a reply is still possible, and one helpful thing a reply could tell them even if they never install anything.

**Counts**

| Platform | Group A (developers) | Group B (general Mac users) | Total |
|---|---|---|---|
| Reddit | 12 | 14 | 26 |
| Hacker News | 3 | 2 | 5 |
| GitHub issues | 7 | 0 | 7 |
| MacRumors forums | 0 | 1 | 1 |
| X/Twitter | 0 | 0 | 0 (see the X section) |
| **Total** | **22** | **17** | **39** |

30 of the 39 posts are from the last three weeks (2026-09-24 or later).

**Before reaching out**
- **Reddit.** The data comes from the Arctic Shift archive. PullPush refused agent access, and reddit.com was blocked from this machine. Two leads were dropped because their posts were later removed or deleted. Open each link once to confirm the post is still up. Threads archive about 6 months after the *post* date.
- **Hacker News.** HN has no DMs. Reply windows are estimated as the story date plus about 14 days, which is a guess.
- **GitHub.** These are vendor repos, where comments that pitch a product read as spam. Lead with the fix. Mention Sizewise only if they ask, or use contact details from their GitHub profile.
- **"Mac" field.** This field says *stated* when the post says so, *other posts* when I checked their post history, and *not stated* otherwise. Any inference is marked as a guess. Sizewise is Mac-only, so check this field before writing.
- **Shell commands.** Commands in the helpful-reply lines are standard macOS, git, Xcode and cargo tools. Anything less certain is marked "(guess)" or "(per another user)".

---

## Reddit (26, newest first)

Found by keyword search (System Data, disk space, worktrees, DerivedData and similar) across r/MacOS, r/mac, r/macbookpro, r/macbookair, r/codex, r/ClaudeCode and r/cursor.

- **u/BrownCowStunning_**, r/MacOS, 2026-10-14, **Group B**. <https://www.reddit.com/r/MacOS/comments/1x640lz/>
  - Quote: "Just got a new MacBookPro a bit more than 2 weeks ago and since yesterday, my storage has been completely flooded for whatever reason." (title: "over 800GB of system data")
  - Filling the disk: about 800 GB of System Data on a 1 TB MacBook Pro, appearing in a day. They already checked Time Machine and /Library/Caches and tried OmniDiskSweeper.
  - Mac: stated.
  - Reply possible: yes. The thread archives around 2027-04-14. It had 0 comments when captured.
  - Helpful reply: OmniDiskSweeper misses protected folders. Give Terminal Full Disk Access and run `sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h | tail -15`, then drill into the largest folder. 800 GB in a day almost always means one app is writing nonstop, such as a VM, a sync client's cache or a crash-report loop.

- **u/GoPhotoshopYourself**, r/mac, 2026-10-13, **Group B**. <https://www.reddit.com/r/mac/comments/1x58ewu/> (also posted to r/applehelp: <https://www.reddit.com/r/applehelp/comments/1x58fnv/>)
  - Quote: "I just deleted 100+ GB worth of data a week ago and now my System Data is at capacity again and I cant use my computer."
  - Filling the disk: unknown. System Data refills within days after every cleanup.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-13). It had 0 comments when captured.
  - Helpful reply: Because it refills, something is writing all the time. Run `sudo du -xh -d 2 /System/Volumes/Data 2>/dev/null | sort -h > ~/du-day1.txt`, repeat it the next day into `~/du-day2.txt`, and `diff` the two files to see which folder grew.

- **u/ineed100000gecs**, r/macbookpro, 2026-10-12, **Group B**. <https://www.reddit.com/r/macbookpro/comments/1x49pa4/>
  - Quote: "I was just working on Photoshop and got the good old disclaimer, that file cant be saved due to storage. So I cant even save sht rn."
  - Filling the disk: 110 GB of System Data plus 69 GB of Adobe apps, on a 13-inch M2 MacBook Pro (2022) with 8 GB of RAM.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-12). 27 comments.
  - Helpful reply: Restart once to clear leftover Photoshop scratch files. Then run `tmutil listlocalsnapshots /` and check `~/Library/Application Support/Adobe` and `~/Library/Caches/Adobe` with `du -sh`, which are the usual System Data hogs on Creative Cloud Macs (guess, based on their app mix).

- **u/cecoondog**, r/MacOS, 2026-10-11, **Group B**. <https://www.reddit.com/r/MacOS/comments/1x3hej6/>
  - Quote: "which maybe helped clear up a couple of gigs but then it goes right back up after a day, so I do it all over again and then bang my head on more walls."
  - Filling the disk: 198 GB of System Data on an M1 MacBook Air with 8 GB of RAM, running Sequoia 15.4.1. They can't update for lack of space and can't open Adobe.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-11). With 214 comments and a score of 354, it may already be answered, so read the thread first.
  - Helpful reply: Run `tmutil listlocalsnapshots /`, then `tmutil thinlocalsnapshots / 999999999999 4` to release Time Machine snapshots. Then run `du -sh ~/Library/Application\ Support/* | sort -h | tail`. Old iPhone backups in `~/Library/Application Support/MobileSync/Backup` are a frequent 50 GB or larger surprise.

- **u/Independent_Syllabub** (comment), r/ClaudeCode, 2026-10-11, **Group A**. <https://www.reddit.com/r/ClaudeCode/comments/1x2x7bn/comment/pf6avj8/>
  - Quote: "Before I made this script a cron job, I was constantly seeing 500gb+ of worktrees taking up space on my hard drives."
  - Filling the disk: parallel-agent git worktrees, 500 GB or more. They now delete unused ones with a cron script every 2 hours.
  - Mac: not stated.
  - Reply possible: yes (until about 2027-04-11). The parent post is by a vendor (Assay), but this commenter is not.
  - Helpful reply: Add `git worktree prune` after the script deletes folders, so stale `.git/worktrees` entries don't keep branches locked. On a Mac, seeding new worktrees with `cp -cR` (an APFS clone) for node_modules and build dirs makes each copy nearly free until files change.

- **u/Calrose_rice** (comment), r/codex, 2026-10-10, **Group A**. <https://www.reddit.com/r/codex/comments/1x1ytxw/comment/pf0898j/>
  - Quote: "Disk usage always at 100% like I cleared 100gb and then the next day I'm already full up. It's crashing my computer daily."
  - Filling the disk: Codex (not itemized). The disk refills overnight.
  - Mac: from other posts (MacBook Pro 2021; they built a macOS tray utility).
  - Reply possible: yes (until about 2027-04-09).
  - Helpful reply: Run `du -sh ~/.codex/sessions ~/.codex/archived_sessions ~/.codex/worktrees ~/Library/Application\ Support/Codex/Crashpad`. If the Crashpad `pending` folder is the one refilling (one user reached 168 GB, openai/codex#52194), quit Codex and reboot before clearing it, or it comes straight back.

- **u/rongw2** (comment), r/codex, 2026-10-09, **Group A**. <https://www.reddit.com/r/codex/comments/1x1ytxw/comment/pexw6nb/>
  - Quote: "i had to uninstall it after it added 50gb of garbage in 3 weeks. Simply unusable."
  - Filling the disk: about 50 GB from the Codex app in 3 weeks.
  - Mac: not stated.
  - Reply possible: yes (until about 2027-04-09).
  - Helpful reply: Uninstalling the app leaves `~/.codex` (sessions, worktrees) and, on a Mac, `~/Library/Application Support/Codex` in place, so the 50 GB is probably still there. `du -sh ~/.codex/*` will show it.

- **u/joseeek**, r/MacOS, 2026-10-08, **Group B**. <https://www.reddit.com/r/MacOS/comments/1x0xpfy/>
  - Quote: "Since MacOS27 my 2020 M1 Macbook constantly tells me that the disk is almost full. I almost deleted everything I really don't need anymore but it just eats up the freed space instantly"
  - Filling the disk: unknown. Freed space disappears right away after the macOS 27 upgrade.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-08). 32 comments.
  - Helpful reply: macOS 27 now counts what used to be "purgeable" space (snapshots, caches) as System Data, per the Apple Community user tip DOC-250012471. Space that vanishes instantly means something is writing, so compare `sudo du -xh -d 2 /System/Volumes/Data | sort -h` run an hour apart.

- **u/nicejaelle**, r/MacOS, 2026-10-08, **Group B**. <https://www.reddit.com/r/MacOS/comments/1x0pbqj/>
  - Quote: "My Mac is almost out of storage, even though I went through everything and I don't seem to have any particularly large files. So I have no idea what's actually taking up so much space."
  - Filling the disk: unknown. They asked whether to use a disk analyzer or built-in tools, and don't want "a cleanup app just for the sake of it".
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-08). With 29 comments, others have probably already recommended analyzers.
  - Helpful reply: The built-in route is to give Terminal Full Disk Access and run `sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h`, then drill down. Also run `tmutil listlocalsnapshots /`, because snapshots don't appear as files at all.

- **u/Shuma665**, r/codex, 2026-10-08, **Group A**. <https://www.reddit.com/r/codex/comments/1x0cq3p/>
  - Quote: "Seriously doing any fast iterative work just kisses the disk space good by. I need to think up some good self cleaning rules."
  - Filling the disk: Codex "evidence" and receipt artifacts written on every iteration. The post had a score of 260.
  - Mac: not stated.
  - Reply possible: yes (until about 2027-04-08).
  - Helpful reply: Add an AGENTS.md rule that sends all evidence and artifacts to one scratch folder per task outside the repo, and prune it weekly with `find <scratch> -mtime +7 -delete`. `git clean -ndX` previews ignored junk inside the repo without deleting anything.

- **u/thebananageek94**, r/mac, 2026-10-06, **Group B**. <https://www.reddit.com/r/mac/comments/1wz8yz8/>
  - Quote: "Over 160GB System Data for a week now and idk how to get rid of it."
  - Filling the disk: 160 GB of System Data on an M4 MacBook Pro with 1 TB, on macOS 27. They report Siri at about 20 GB and the OS at 30 GB. Messages has an "save in iCloud" prompt that never goes away.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-06). 22 comments.
  - Helpful reply: On macOS 27, System Data now includes the old purgeable space, so `tmutil listlocalsnapshots /` and `tmutil thinlocalsnapshots / 999999999999 4` may shrink it a lot. Also check `du -sh ~/Library/Messages`, given the stuck iCloud Messages sync.

- **u/No_Accident8684** (comment), r/codex, 2026-10-05, **Group A**. <https://www.reddit.com/r/codex/comments/1wxjgzz/comment/pdyvxpm/>
  - Quote: "i have a 512gb mac studio, because when i bought it, we had things like llama3 or whatever. however, things have changed and its not enough, not even close."
  - Filling the disk: local LLM weights.
  - Mac: stated (Mac Studio).
  - Reply possible: yes (until about 2027-04-04). The comment sits in an unrelated thread.
  - Helpful reply: Duplicates pile up across `ollama list`/`ollama rm`, `huggingface-cli delete-cache` (or `hf cache` in newer versions) and LM Studio's models folder. The `OLLAMA_MODELS` setting and LM Studio's model-directory setting can point at an external Thunderbolt SSD.

- **u/Beatsu**, r/MacOS, 2026-10-04, **Group B**. <https://www.reddit.com/r/MacOS/comments/1wxr0it/>
  - Quote: "When I open "Storage settings" it says I have 208GB of "System Data" which after a google search says I can't do anything about..."
  - Filling the disk: 208 GB of System Data, plus 187 GB of "Documents" that don't match any visible files. They can't download anything.
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-04). 22 comments.
  - Helpful reply: Storage settings only itemizes what it can classify. `sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h`, with Terminal given Full Disk Access, shows where the roughly 400 GB actually sits, including hidden folders the Documents view never lists.

- **u/Kremiorspokke**, r/MacOS, 2026-10-02, **Group A**. <https://www.reddit.com/r/MacOS/comments/1wvzue0/>
  - Quote: "CoreSimulator is taking up 60gbs of free space tried deleting it in recovery mode with the help of chatgpt but it's still there"
  - Filling the disk: `~/Library/Developer/CoreSimulator`, 60 GB (Xcode simulators).
  - Mac: stated.
  - Reply possible: yes (until about 2027-04-02). Only 1 reply so far.
  - Helpful reply: No Recovery Mode is needed. `xcrun simctl delete unavailable` removes dead simulators, and `xcrun simctl runtime list` followed by `xcrun simctl runtime delete <identifier>` (or Xcode ▸ Settings ▸ Components) removes runtimes so the space actually comes back.

- **u/Infamous_Tomatillo53**, r/codex, 2026-10-01, **Group A**. <https://www.reddit.com/r/codex/comments/1wvcw0q/>
  - Quote: "man I am managing 5 agent sessions today and they're slow. not sharp enough sometimes. and my laptop got slower and I had to figure out why it ran out of disk."
  - Filling the disk: not itemized. Five parallel Codex sessions.
  - Mac: from other posts ("My Codex app got removed from my Mac").
  - Reply possible: yes (until about 2027-04-01).
  - Helpful reply: With parallel Codex sessions, the usual suspects are `~/.codex/worktrees` and `~/.codex/sessions`, because every subagent writes its own transcript. `du -sh ~/.codex/*` shows which one, and removing finished worktrees followed by `git worktree prune` frees the space.

- **u/TheUsualSuspect_____**, r/MacOS, 2026-09-30, **Group B**. <https://www.reddit.com/r/MacOS/comments/1wu7kxs/>
  - Quote: "When I checked a few days ago, I had around 150 GB of free space, but now my storage is completely full. It's showing that the System Data is using around 357 GB"
  - Filling the disk: 357 GB of System Data, after losing 150 GB of free space in a few days.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-30). 21 comments.
  - Helpful reply: A jump that fast is usually one app writing. `sudo find /System/Volumes/Data -xdev -size +5G -mtime -7 2>/dev/null` lists the big files changed in the last week.

- **u/melvin3v1978**, r/mac, 2026-09-30, **Group B**. <https://www.reddit.com/r/mac/comments/1wu2wzx/>
  - Quote: "after using my Crucial X9 Pro external SSD it started increasing by roughly 10GB per day until it reached about 152GB."
  - Filling the disk: System Data grows about 10 GB a day while an external SSD is connected. It's a Mac mini M6 (512 GB) on macOS 27, and Apple has collected logs.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-30). 28 comments.
  - Helpful reply: Save `sudo du -xh -d 2 /System/Volumes/Data 2>/dev/null | sort -h` with the SSD connected and again a day later. The diff names the folder gaining 10 GB a day, which is also useful evidence for Apple's case.

- **u/radim11** (comment), r/ClaudeCode, 2026-09-30, **Group A**. <https://www.reddit.com/r/ClaudeCode/comments/1wsmwjp/comment/pcyil9u/>
  - Quote: "I do normal agentic development with my own company and I'm running low on storage too. Having 256GB on Mac is just not much for serious work."
  - Filling the disk: multiple repos plus Docker containers on a 256 GB Mac. They use Mole "from time to time".
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-28). Their company is stashbase.dev, which is not a disk tool.
  - Helpful reply: `docker system df` shows what's reclaimable, and `docker builder prune` plus `docker image prune -a` usually free the most. Check Docker.raw's real size with `du -h`, because Finder shows the sparse file's maximum size, not what it actually uses.

- **u/jchannon**, r/MacOS, 2026-09-29, **Group B**. <https://www.reddit.com/r/MacOS/comments/1wt32r2/>
  - Quote: "Just upgraded from Sequoia and my disk space dropped by 100GB. Apart from deleting downloads folder and emptying my trash, how can I reclaim that space?"
  - Filling the disk: about 100 GB lost after upgrading to macOS 27 (Golden Gate).
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-29). 43 comments.
  - Helpful reply: Part of it is a reporting change. macOS 27 folds former purgeable data into System Data, and its Apple Intelligence models take about 20 GB more than Tahoe's (per Apple Community user tip DOC-250012471). `tmutil listlocalsnapshots /` shows the pre-upgrade snapshot, which `tmutil thinlocalsnapshots / 999999999999 4` can release.

- **u/TimJamesS**, r/macbookair, 2026-09-29, **Group B**. <https://www.reddit.com/r/macbookair/comments/1wt1tjd/>
  - Quote: "this morning I checked my MBA I had about approaching 90Gb storage free, now its about 78 GB storage free. What could have caused this increase in disk utilisation?"
  - Filling the disk: unknown. They lost 12 GB in 1–2 hours.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-29). Only 3 comments.
  - Helpful reply: A drop like that in an hour or two is usually a local Time Machine snapshot, an iCloud download or Spotlight indexing. Run `tmutil listlocalsnapshots /` and compare two runs of `du -xh -d 2 ~ 2>/dev/null | sort -h` an hour apart.

- **u/Federal-Glove-3200**, r/ClaudeCode, 2026-09-28, **Group A**. <https://www.reddit.com/r/ClaudeCode/comments/1wsmwjp/>
  - Quote: "My Mac mini only has 256GB of storage, and since I started vibe coding iOS apps, I'm constantly running out of space."
  - Filling the disk: iOS development artifacts. They run a Mole automation whenever free space drops below 5 GB and are planning external SSDs.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-28).
  - Helpful reply: Keep the repos on the internal drive and move the regenerable data. Xcode ▸ Settings ▸ Locations can put DerivedData on the external SSD, `xcrun simctl runtime delete` removes old simulator runtimes (about 8 GB each), and old folders in `~/Library/Developer/Xcode/iOS DeviceSupport` can be deleted.

- **u/adecareddit**, r/MacOS, 2026-09-24, **Group B**. <https://www.reddit.com/r/MacOS/comments/1wp8e08/>
  - Quote: "I noticed today that my disk is nearly full, and I could not figure out how. The totals from my Finder don't add up to this 560 GB of system data."
  - Filling the disk: 560 GB of System Data.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-24). 11 comments.
  - Helpful reply: Finder totals can't see snapshots or protected folders. `tmutil listlocalsnapshots /` plus `sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h` shows whether the 560 GB is snapshots or a real folder.

- **u/andysurtees**, r/codex, 2026-09-22, **Group A**. <https://www.reddit.com/r/codex/comments/1wnp5q6/>
  - Quote: "Now I realise my SSD is completely full, half of which is the .codex folder, mostly worktrees." (title: "800gb of worktrees?")
  - Filling the disk: Codex worktrees under `~/.codex`.
  - Mac: not stated (guess: Mac, since Codex Desktop is common there).
  - Reply possible: yes (until about 2027-03-22). Only 2 replies so far, one from a bot.
  - Helpful reply: Users report Codex's `worktree-keep-count` and auto-delete settings aren't enforced (openai/codex#35383). The reliable fix is, per repo, `git worktree list`, `git worktree remove` for merged branches, then `git worktree prune`. Also check `~/.codex/sessions`, where subagent transcripts can reach hundreds of GB.

- **u/funky_surprise**, r/mac, 2026-09-22, **Group B**. <https://www.reddit.com/r/mac/comments/1wne4l5/> (also posted to r/MacOS: <https://www.reddit.com/r/MacOS/comments/1wne7cc/> and r/applehelp: <https://www.reddit.com/r/applehelp/comments/1wne9xe/>)
  - Quote: "So depending on the measurement method, I get roughly 685–757 GB of files vs. 923 GB reported as used by the APFS Data volume."
  - Filling the disk: a gap of about 150–200 GB that no tool can attribute. They already ruled out Time Machine and Data-volume snapshots, deleted-but-open files and hard links. They have about 255 GB of OneDrive files stored locally, First Aid found and repaired corruption, and they ask explicitly about APFS clones and space accounting. It's a Mac mini M4 Pro with 1 TB on macOS 26.6.2. This is the closest fit to Sizewise's APFS question.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-22). Only 3 comments.
  - Helpful reply: Clones make `du` count *more*, not less, so the missing space is more likely blocks no file owns. Leaked extents after the corruption First Aid found are one candidate (guess). A read-only `sudo fsck_apfs -n` on the Data volume from Recovery, plus checking whether `diskutil apfs list` "Capacity Consumed" stays flat across a day, would tell leaked space apart from something still growing (guess).

- **u/Odd-Anything1768**, r/codex, 2026-09-07, **Group A**. <https://www.reddit.com/r/codex/comments/1w9m42z/>
  - Quote: "I've been troubleshooting why my MacBook storage kept filling up again—sometimes gaining more than 100 GB of "System Data" within 24 hours."
  - Filling the disk: abandoned temporary Git packs (`tmp_pack_*`) from Codex Desktop's workspace diffs, 177 GB in total. macOS showed 559 GB of System Data. They cleaned it up carefully themselves.
  - Mac: stated.
  - Reply possible: yes (until about 2027-03-07). One commenter said "Same issue!"
  - Helpful reply: `find ~ -path '*/.git/objects/pack/tmp_pack_*' -size +100M 2>/dev/null` is a quick recurring check. openai/codex#19588 tracks the same leak, with recurrences reported and a request for a per-workspace switch to turn it off.

- **u/pp_amorim** (comment), r/cursor, 2026-09-06, **Group A**. <https://www.reddit.com/r/cursor/comments/1w8558g/comment/p88jbkx/>
  - Quote: "I have 48gb of RAM. Cursor eats around 50 gb of storage every day."
  - Filling the disk: Cursor (not itemized).
  - Mac: other posts mention their team's self-hosted M1 Mac mini, an iOS shop (guess: Mac).
  - Reply possible: yes (until about 2027-03-05).
  - Helpful reply: Cursor's growth is usually `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` (agent and chat history) plus `workspaceStorage`. Another r/cursor user suggests quitting other windows and running "Developer: GC Agent KV Blobs" or "Delete Old Chats" from the Command Palette (unverified).

---

## Hacker News (5, newest first)

Found with HN Algolia keyword searches and full-thread scans of the macOS 27 and agent-tooling threads.

- **antoineMoPa**, 2026-10-14, **Group A**. <https://news.ycombinator.com/item?id=50086479> (story: "What agents mean for Rust (and vice versa)", 2026-10-14)
  - Quote: "I realize how terribly huge the target/ folder can grow. Then, you run cargo clean, get a clean disk but compilation takes forever again. I routinely run out of disk space."
  - Filling the disk: Rust `target/` folders in apps built with agents.
  - Mac: not stated. Other comments mention running a Linux project "this time on a mac" (guess: they use both).
  - Reply possible: yes, until about 2026-10-28 (guess).
  - Helpful reply: Run `cargo install cargo-sweep`, then `cargo sweep --time 7` in each project or worktree, which removes artifacts unused for a week without a full rebuild. Setting `debug = "line-tables-only"` under `[profile.dev]` shrinks `target/` substantially.

- **icantevenhold**, 2026-10-13, **Group A**. <https://news.ycombinator.com/item?id=50064993> (story: "Codex CLI installs a persistent, self-updating background daemon by default", 2026-10-12)
  - Quote: "turns out i had some unused local models in random folders ~200gb worth. Plus aforementioned harness bloat plus 100gb of unused npm stuff etc"
  - Filling the disk: about 200 GB of local models, agent-harness leftovers, and about 100 GB of npm data and node_modules.
  - Mac: not stated.
  - Reply possible: yes, until about 2026-10-26 (guess).
  - Helpful reply: `find ~ -name node_modules -type d -prune -exec du -sh {} + 2>/dev/null | sort -h` lists every node_modules folder by size, and `npm cache clean --force` clears the npm cache. For models, check `ollama list`, `huggingface-cli delete-cache` and `~/.lmstudio/models`.

- **busymom0**, 2026-10-07, **Group B**, and also a developer. <https://news.ycombinator.com/item?id=49993888> (story: "Tell HN: Apple not letting removal of AI models on macOS 27 is outrageous", 2026-10-07). Earlier post: <https://news.ycombinator.com/item?id=49792485>
  - Quote (2026-09-21): "My "system data" is taking up 193 GB. Is my Mac doing something wrong here? Anyway to see what's inside?" Their 2026-10-07 comment says System Data "exploded to 74 GB" after the RemoveMacAI script.
  - Filling the disk: 193 GB of System Data. They build macOS and iOS apps with Xcode and simulators, and say Apple Intelligence takes 30 GB on their Mac mini.
  - Mac: stated.
  - Reply possible: yes in the 10-07 thread, until about 2026-10-21 (guess). The 09-21 thread is closed.
  - Helpful reply: Since they use Xcode, check `du -sh ~/Library/Developer/*` first. CoreSimulator devices and runtimes (`xcrun simctl delete unavailable`, `xcrun simctl runtime list`) and DerivedData often account for 100 GB or more of "System Data".

- **singularity2001**, 2026-10-05, **Group A**. <https://news.ycombinator.com/item?id=49961708> (story: "Turn off Apple Intelligence on macOS 27 and get its disk space back", 2026-10-04)
  - Quote: "I'd rather have a mechanism to remove the 100 GB of old simulator images for Apple Watch and TVOS, which I never use and which can't be uninstalled without disabling security"
  - Filling the disk: about 100 GB of watchOS and tvOS simulator runtimes.
  - Mac: other posts ("on mac").
  - Reply possible: yes, until about 2026-10-18 (guess). Reply soon.
  - Helpful reply: Most runtimes come off without touching SIP: `xcrun simctl runtime list`, then `xcrun simctl runtime delete <id>` (or Xcode ▸ Settings ▸ Components). Leftovers that keep coming back live in `/System/Library/AssetsV2/com_apple_MobileAsset_*SimulatorRuntime`. One user documented the full cleanup here: <https://www.reddit.com/r/MacOS/comments/1wgqmtd/>

- **Gigachad**, 2026-10-05, **Group B**. <https://news.ycombinator.com/item?id=49960142> (same story, 2026-10-04)
  - Quote: "My 512gb mac is always running out of space so I have to use 3rd party tools to find where all the space went since macos just lumps it in "Applications" or "Documents""
  - Filling the disk: app leftovers "in deep system directories" on a 512 GB Mac.
  - Mac: stated.
  - Reply possible: yes, until about 2026-10-18 (guess). Reply soon.
  - Helpful reply: `du -sh ~/Library/{Application\ Support,Containers,Group\ Containers,Caches}/* 2>/dev/null | sort -h | tail -20` lists the deep app folders macOS lumps into System Data, and usually names the culprit app in one pass.

---

## GitHub issues (7, newest first)

Found with GitHub issue search (openai/codex, anthropics/claude-code, orbstack) and read on the issue pages. All are open or closed but **not locked**, so comments are possible.

- **uaalah**, 2026-10-08, **Group A**. <https://github.com/openai/codex/issues/52194> (closed by the author on 2026-10-09)
  - Quote: "The folder `~/Library/Application Support/Codex/Crashpad/pending` reached approximately 168 GB and I ran out of disk space."
  - Filling the disk: Codex Desktop crash dumps, which kept growing after cleanup.
  - Mac: stated (macOS 26.3.1, arm64).
  - Reply possible: yes, as a comment on the closed issue, or via their profile.
  - Helpful reply: Since it regrew after cleanup, a tiny launchd job that warns when `du -sk ~/Library/Application\ Support/Codex/Crashpad/pending` passes a few GB would catch the next crash loop early. The bot-linked duplicates #51739 and #51361 may have the root-cause fix.

- **aunitt**, 2026-10-05, **Group A**. <https://github.com/anthropics/claude-code/issues/99672>
  - Quote: "For repos that keep large gitignored caches in `.worktreeinclude`, this means every worktree now costs the full size of those files on disk."
  - Filling the disk: Claude Code stopped APFS-cloning `.worktreeinclude` files in 2.1.275. That costs about 9.4 GB per worktree, and `.claude/worktrees` reached about 200 GB across 22 worktrees. This is the strongest fit for clone-aware accounting.
  - Mac: stated (APFS).
  - Reply possible: yes (open).
  - Helpful reply: Until the fix ships, a WorktreeCreate hook that copies the `.worktreeinclude` paths with `cp -cR` (which uses clonefile) restores near-free copies. Because `du` counts every clone at full size, `df` before and after is the honest way to show the regression.

- **LinusAuditore**, 2026-10-01, **Group A**. <https://github.com/openai/codex/issues/49803>
  - Quote: "Every successful Sparkle auto-update leaks a full copy of the *previous* app version (~1.5 GB)"
  - Filling the disk: `~/Library/Caches/com.openai.codex/org.sparkle-project.Sparkle/Installation/`, about 6 GB after 4 updates.
  - Mac: stated (macOS 27.0.1).
  - Reply possible: yes (open).
  - Helpful reply: Until it's fixed, a weekly launchd job that empties that `Installation/` folder while the app is closed keeps the space from piling up again.

- **mrmachine**, 2026-09-11, **Group A** (purgeable-space confusion). <https://github.com/orbstack/orbstack/issues/2691>
  - Quote: "Codex said I had 119MB free but Finder says 240GB free. Daisy Disk says 240GB free + purgeable."
  - Filling the disk: local Time Machine snapshots counted as "purgeable". OrbStack stopped with a StorageFull error.
  - Mac: stated (M1 Max, macOS 26.5.2).
  - Reply possible: yes (open, no replies yet).
  - Helpful reply: Finder reports "available" (free plus purgeable), while OrbStack and Codex see actual free space. `tmutil listlocalsnapshots /`, then `tmutil thinlocalsnapshots / 999999999999 4`, turns the purgeable space into real free space immediately.

- **aervium**, 2026-09-07, **Group A**. <https://github.com/openai/codex/issues/43449> (closed by the author the same day; written in Portuguese)
  - Quote: "No macOS, ~/.codex/sessions ocupa aproximadamente 334 GB em 1.954 arquivos." ("On macOS, ~/.codex/sessions occupies approximately 334 GB across 1,954 files.")
  - Filling the disk: Codex session transcripts, about 294 GB of them from subagents. They asked for cleanup guidance that keeps active chats resumable.
  - Mac: stated.
  - Reply possible: yes, as a comment on the closed issue. Consider replying in Portuguese.
  - Helpful reply: Archiving only moves rollouts to `~/.codex/archived_sessions`. Running `codex delete <session>` on finished threads, or moving old `sessions/YYYY/MM` folders to an external drive, frees space while active threads stay resumable.

- **mandyleidinger**, 2026-09-04, **Group A**. <https://github.com/anthropics/claude-code/issues/92158>
  - Quote: "In a single active session, ~19 of these were created within a few hours of normal use, accounting for ~8GB."
  - Filling the disk: Claude desktop `local-agent-mode-sessions/*/local_*` sandboxes, each a full copy of `~/.claude` at about 300 MB. They had already deleted more than 100 GB and run their own 12-hour cleanup script.
  - Mac: stated.
  - Reply possible: yes (open).
  - Helpful reply: Each sandbox copies the whole `~/.claude/plugins` folder, so removing unused plugins and old plugin versions there shrinks every future per-task copy (guess, based on their own size breakdown).

- **dellapolla-lab**, 2026-09-04, **Group A**. <https://github.com/anthropics/claude-code/issues/92078>
  - Quote: "Two days of normal use left 11 pooled worktrees on disk, 72 GB."
  - Filling the disk: full checkouts of an 82k-file repo for Claude desktop's pooled worktrees under `.claude/worktrees/`.
  - Mac: stated (macOS 26.6.2, APFS).
  - Reply possible: yes (open).
  - Helpful reply: `git worktree list --porcelain` shows which pooled worktrees are idle. `git worktree remove` on those, then `git worktree prune`, reclaims the 72 GB without touching live sessions. A Medium write-up says Claude Code's `worktree.sparsePaths` setting can cut each checkout to the packages needed (per another user; verify).

---

## MacRumors forums (1)

- **lmaodzedun**, 2026-09-16, **Group B**. <https://forums.macrumors.com/threads/1-43-tb-of-system-data-on-a-mac-studio.2489533/>
  - Quote: "My Mac Studio is running macOS 27.0 (26A428), and System Data is taking up 1.43 TB. For comparison, it's just 56 GB on my MacBook Pro."
  - Filling the disk: 1.43 TB of System Data, cause unknown.
  - Mac: stated. u/jeerobus asked the same question on r/MacOS the same day (<https://www.reddit.com/r/MacOS/comments/1whunuu/>). This may be the same person (guess).
  - Reply possible: yes. The thread isn't locked, and replying needs a free MacRumors account. A conversation (DM) is also possible.
  - Helpful reply: At 1.43 TB it is almost always a single thing, such as VM disks, Docker.raw, a backup or sync app's cache, or snapshots. `tmutil listlocalsnapshots /` and `sudo du -xh -d 1 /System/Volumes/Data 2>/dev/null | sort -h`, with Terminal given Full Disk Access, will name it within a minute.

---

## X/Twitter (0 qualifying)

Exa and web search mostly return articles, cleaner-app marketing, LinkedIn posts, and tweets from before September. Mirrors drop the handles of people who replied. The two in-window posts found don't qualify:
- **@Da7_Tech**, 2026-10-06 (status 2107393548404289780, "200 GB of junk left behind by Codex"). Excluded because they promote their own "Storage Rescue" cleanup skill.
- **@Voxyz_ai**, 2026-09-25 ("~/.codex alone was 82 GB"). Excluded as a vendor account (founder of an AI-agent company posting tip threads).

**Worth checking by hand:** the replies under @Da7_Tech's post (<https://x.com/Da7_Tech/status/2107393548404289780>) include people who wrote "My 1TB SSD got completely full… I got more than 400GB back", "Agreed.. 88gb here. Killed me" and "My Opus found 475GB of junk". Mirrors didn't show their handles, so open the thread on X to see who they are.

---

## Considered and left out

- **Promoting a competing tool:** DiskFox (Plastic_Rip5046), DiskPress and App Archiver (JulyIGHOR), ByteSweep (Able-Place), SpareDisk (introvertmac, lazykid07), Mole (Hitw93), Trace (Argon_Analytik), OpenDisk (herovals), DuckDisk (eggyboy577), simless (Low-Future-9387), Assay (fuckme), ruprechttmb, ImaginationVarious30 (Docker), prtkgpt (DerivedData app), rusty-broom (orion_tvv), Wuntenn (own skill), and others.
- **Not on a Mac:** Plane_Garbage (98 GB of Codex chats, but on a Windows PC per other posts), dvduval (Windows), Shunpaw (Linux), JigSawPT ("PC", 2 TB), Background-Bank1798 (WSL), Sea_Donkey_669 (Windows), xBOBxSAGETx (Windows, claude-code#100290), eyueldk (Cursor state.vscdb at 160 GB, "PC"), Dangerous-Sport-2347 (DLSS mod, Windows; guess).
- **Post later removed or deleted:** optima-pacifist (a 127 GB disk filled by worktrees; post removed by moderators) and marsa-emreef (60 GB of stale Rust target dirs; parent post deleted).
- **HN thread closed (older than about 2 weeks):** vitalrune ("my macbook is almost out of space just from development cache"), viccis (256 GB Mac mini for iOS development), baggachipz, gushie, fhub and vjvjvjvjghv. yearolinuxdsktp ("200+ GB codex-rs target folder", 2026-10-01) is also excluded because its window ends today.
