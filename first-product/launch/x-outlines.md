# X post outlines (not drafts yet)

These are facts, images and links for each post, in order. They become drafts in Ethan's voice once I've read 5 to 10 of his real posts. Until then nothing here should be posted as written.

## 1. Launch day: the macOS map (same day as the Show HN)

- Image: screenshot of https://getsizewise.app/macos with "What changed since 26.5.1" on (take it in light and dark; the dark one reads better on X).
- Facts to use, all from the page: macOS 27.0.1 is 4.37 GB bigger than 26.5.1 (24.4 GB against 20 GB, signed volume plus cryptexes); a new 7.3 GB Rosetta cryptex; on Apple silicon, 3.09 GB of Intel copies of system libraries plus 4.14 GB of Rosetta translations, against 2.49 GB for the native copy; Apple Intelligence models sit in AssetsV2 folders macOS protects even from administrators (Apple says up to 14 GB).
- Link: https://getsizewise.app/macos
- No ask to upvote the HN post. If it does well, a reply in the thread can link it.

## 2. Day 1 or 2: a week of coding agents (developer angle)

- Image: launch/dev-week/screenshots/map-dark.png (or a screenshot of the live page once it ships).
- Facts, from the sample page: a sample developer home folder grew 63.7 GB from Monday to Friday; Rust target +22.9 GB; one model download +16.4 GB; Docker.raw +9 GB; six agent worktrees with their own node_modules and .next, 7.22 GB (Monday's one was 918 MB); simulators and Xcode +5.54 GB. Say plainly it's a sample with typical sizes.
- Real complaints to quote or reply under (with permission of the platform's norms): "each worktree can easily contain 200GiB of build artifacts" (https://news.ycombinator.com/item?id=49110131); "it's just the 200+ GB codex-rs target folder" (https://news.ycombinator.com/item?id=49927304).
- Link: https://getsizewise.app/dev-week once deployed, else https://getsizewise.app

## 3. Day 3 to 5: one precise thing most disk tools get wrong

- Fact: on APFS, deleting a file can free less than its size, because Finder copies share blocks, Time Machine keeps local snapshots, and hard links point at the same data. Sizewise asks APFS how much deleting would free and shows what still holds the rest. A file with several hard links counts once.
- Fact for developers, from Ethan's own guide (https://getsizewise.app/developer-caches): pnpm and uv share files between projects, so deleting one project's folder frees less than its size.
- Image: a Sizewise window with a selection locked and the status bar showing "frees X of Y" (Ethan takes this on his Mac).

## 4. After the r/MacApps post: price and terms in one line

- Free to scan, no account; $12.99 once for Move to Trash, Show Changes, Compare with Saved Scan; 5 Macs; every 1.x update; 14-day refunds; collects no data about your files.
