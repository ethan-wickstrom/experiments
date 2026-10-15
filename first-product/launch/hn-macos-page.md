# Hacker News draft: the /macos page

Status: draft for Ethan. Not posted.

Why this goes first: https://getsizewise.app/macos is already built, it is interesting on its own (every file macOS 27.0.1 puts on a Mac, mapped, with what changed since 26.5.1), and it reads as a finding, not an ad. HN rewards that. Sizewise gets its traffic from the "See your own Mac this way" block under the map. I found no HN or Reddit post of this page (searched 2026-10-15).

Post it as a Show HN (it is something you made that people can play with, with no signup). Then wait at least 5 days before the Sizewise Show HN, so the two don't compete, and post r/MacApps in between.

## Title (61 characters)

Show HN: Every file macOS 27 puts on your Mac, mapped

Alternate: Show HN: What changed on disk between macOS 26.5.1 and 27.0.1

## URL

https://getsizewise.app/macos

## First comment (post right after submitting)

I make a disk space app for the Mac, and pointed its scanner at the signed system volume, the cryptexes and AssetsV2 of macOS 27.0.1 and 26.5.1, then drew both as maps you can zoom into. Every rectangle is a file, sized by the space it takes on disk.

Some numbers from the two scans:

- On an Apple silicon Mac, macOS 27.0.1 keeps 3.09 GB of Intel copies of its system libraries and 4.14 GB of Rosetta's translations of them, in a cryptex of their own. The copy for its own chip is 2.49 GB.
- Counting the signed volume and the cryptexes, which are the same on every Mac with the same build, 27.0.1 takes 24.4 GB, against 20.1 GB for 26.5.1.
- Apple Intelligence keeps its models in AssetsV2 folders that macOS protects even from administrators, so no app can measure them. Apple says up to 14 GB.

The 27.0.1 scan ran on GitHub's macOS 27 virtual Mac. The page holds no one's own files. Click "What changed since 26.5.1" to color the map by what grew, shrank or is new.

[Optional, one line in your words on why you made the page.]

## Numbers check

The three figures above were computed on 2026-10-15 from the page's own data files (atlas/macos-27.0.1.json and atlas/macos-26.5.1.json) with the same rules the page uses: Intel = x86_64 dyld caches, Rosetta = aot_ caches, native = arm64e caches, scoped size = everything except System/Library/AssetsV2. Open the page and confirm each matches what it shows before posting.
