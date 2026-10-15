# Show HN draft (Sizewise)

Status: draft for Ethan. Nothing here is posted. Every claim below is taken from getsizewise.app or the 1.0 to 1.4 release notes, checked 2026-10-15. Bracketed lines are Ethan's to fill in or delete.

Post from Ethan's HN account, on a weekday morning US Eastern, and stay in the thread for the first two hours. Show HN rules: something people can try with no signup (true: free scan, no account), no friends asked to upvote.

## Title (77 characters)

Show HN: Sizewise – a disk map for macOS that asks APFS what deleting frees

Alternates:
- Show HN: Sizewise – see where your Mac's disk space went since last week
- Show HN: A treemap for your Mac's disk that counts clones and hard links once

## URL

https://getsizewise.app

## Text

Sizewise draws a folder or a whole disk as a map. Every file is a rectangle sized by the space it takes, so the thing you forgot about stands out.

[One or two sentences, in your words: why you built it.]

A few details that took the most work:

- What deleting frees. On APFS, the size of a file and the space you get back can differ: Finder copies share blocks, backup apps keep snapshots, and hard links point at the same data. Lock a selection and Sizewise asks APFS how much deleting it would free, and shows what still holds the rest. A file with several hard links counts once.
- Where the space went. Scan a folder again and Sizewise names up to three places that grew, and Show Changes colors what grew, what shrank and what's new. On a developer machine that's usually a simulator runtime, a Docker image, or a worktree's build folder.
- Speed. It maps a startup disk with 17.5 million items in about a minute and a half. Reopen that scan and the map is back in about half a second while changes fill in behind it.
- It moves things only to the Trash, and asks before every move.

You can also let Claude or another assistant read your saved scans and ask it what's filling your disk. It can read them, not move or delete anything.

Scanning is free with no account. A license is $12.99 once and adds Move to Trash, Show Changes and Compare with Saved Scan, on up to 5 Macs. It collects no data about your files. It needs macOS 15 or later.

The guides I wrote while building it are free and cite their sources: what's in System Data, Xcode storage, why Docker.raw looks so big, and package caches. If Sizewise gets something wrong on your machine, I'd like to know.

## First reply to have ready (post it yourself only if someone asks how it differs from DaisyDisk or GrandPerspective)

DaisyDisk is $9.99, draws a sunburst, and deletes files permanently with a five-second cancel; since 4.34 it also counts APFS clones once. GrandPerspective is a free treemap. Sizewise is a treemap too; what it adds is the "what deleting frees" check, Show Changes between scans, and Trash-only deletes. The comparison page lists sources for each: https://getsizewise.app/compare

## Likely objections and honest answers

- "Paid disk apps hoard knowledge." The guides are free and sourced, and the scan is free. The license pays for Move to Trash and the change views.
- "Why not `du`/ncdu/Mole?" They're good. `du` counts a cloned or hard-linked file at full size in every place; Sizewise asks APFS what deleting would return, and shows changes between scans on a map.
- "Does it phone home?" Per the privacy page: it goes online for two things only, to check for updates and to activate a license once. Activation sends Polar the key and the Mac's model identifier, once; after that the license is checked on the Mac and Polar is never contacted again. Scanning without a license sends nothing. https://getsizewise.app/privacy
  (This answers the objection raised on DiskFox's Show HN, where a commenter called periodic Polar license checks "a paid tracking cookie": https://news.ycombinator.com/item?id=49998987)
- "Can my assistant use it?" Yes, if you turn on Let AI assistants read scan results in Settings; the assistant can read names and sizes in saved scans, and nothing else.
