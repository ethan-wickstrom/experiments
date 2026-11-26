# Decisions

**V1. The record is an append-only file of events, scored by a script with no dependencies.**
A guess is only worth scoring if it was made before the answer. Lines are only added, so the file's order and the commits that added the lines show that. Rejected: a spreadsheet or database, where an edit leaves no trace; a hosted forecasting site, which adds an account for something 100 lines do.

**V2. Python standard library, not TypeScript with Effect.**
The script reads a file, appends a line and prints a table. It has no concurrency, services or failures worth modelling. Rejected: Effect v4, the repository's choice for TypeScript, because nothing here needs it. If this grows a server or a payment flow, that part is TypeScript with Effect.

**V3. Steps are gates with evidence, not dates.**
Two waits belong to the world (a person deciding, and the six-week outcome); the rest is agent time. A dated twelve-month ladder hides which is which. Rejected: the dated ladder in the vision page, which put ten people, a trade and a hundred trades one after another.

**V4. The agent sends no cold messages.**
The thesis is that buyers answer when they asked first, and that pitches at volume are what closed the channel. An agent that pitches to get its first ten answers disproves the thing it is testing. Rejected: outbound email or posts to forums by the agent. The owner names people, or the work is finding where people already state the problem.

**V5. A yes from a friend is recorded and not counted.**
An answer the asker caused says nothing about the problem. Rejected: counting every stake equally, which rewards whoever has the most friends.

**V6. The first bets in the record are about this project.**
The claim is that people corrected often become well calibrated. The agent doing the work is the first thing that claim can be tested on. Rejected: waiting for the first real run to start the record.

**V7. Six-week outcomes count everyone who put up the stake, and require unprompted use in week six (days 36 to 42).**
Dropping out during week one is a failure of the fix, not a reason to remove someone from the denominator. Counting an earlier commit would pass a tool that was tried once and abandoned. Half of the cohort is the initial bar before any run has been scored; adjust after Gate C if calibration shows a better bar. Rejected: counting only week-one completers, or counting any commit before day 42.

**V8. Run 001 goes before Run 002.**
Run 001 already has seven verified builders and a ready draft message, so it can start today; Run 002 still needs an active-builder ask list. Experiment priority belongs to the agent (`../CLAUDE.md`). Rejected: waiting on the owner to pick the order.
