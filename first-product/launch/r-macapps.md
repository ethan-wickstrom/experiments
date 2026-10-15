# r/MacApps post draft (Sizewise)

Status: draft for Ethan. Not posted.

Rules this follows (moderator post 2026-03-19, read on a mirror): an app outside the Mac App Store posts under Tier 2, which needs a real identity, LinkedIn, real contact details, and a site with a Privacy Policy and Terms. Use the Problem / Comparison / Pricing format. One app post per developer per 30 days, counted even if removed. AI-style text, such as em dashes, triggers auto-removal, so this draft has none. Do not link a .dmg directly.

## Title

Sizewise: a disk space map for Mac that tells you what deleting something would actually free

## Body

**Problem.** "Disk almost full" and no idea why. Storage settings lumps most of it into System Data, Finder sizes don't add up, and on APFS deleting a file doesn't always give back its size: Finder copies share blocks, Time Machine keeps local snapshots, and hard links point at the same data.

Sizewise draws any folder or disk as a map where the bigger the file, the bigger its rectangle. Lock something and it asks APFS how much deleting it would free and what still holds the rest. Scan again later and it shows what grew, what shrank and what's new. It moves things only to the Trash and asks every time.

It mapped a startup disk with 17.5 million items in about a minute and a half, and reopening that scan shows the map in about half a second.

**Comparison.** DaisyDisk ($9.99) draws a sunburst and deletes permanently after a five second countdown. GrandPerspective (free) is a treemap without the "what deleting frees" check or change history. Side by side, with sources: https://getsizewise.app/compare

**Pricing.** Free to scan, no account. $12.99 once (plus tax where it applies) adds Move to Trash, Show Changes and Compare with Saved Scan, on up to 5 Macs, with every 1.x update. Refunds within 14 days for any reason. macOS 15 or later.

https://getsizewise.app

**About me.** I'm Ethan Wickstrom, an independent developer in St. Louis. LinkedIn: https://www.linkedin.com/in/ethan-wickstrom . Support: support@getsizewise.app . Privacy: https://getsizewise.app/privacy . Terms: https://getsizewise.app/terms . Sizewise collects no data about your files.

[One sentence in your words: why you built it.]
