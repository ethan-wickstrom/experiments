# Verdict

The repository's rules are in `../CLAUDE.md`; this file adds what is specific to Verdict.

## Purpose

Make the truth about an idea arrive sooner for people who have lived with a problem for years, and keep a record that shows whether it does. Outcomes come first: no product is specified here until runs of the protocol say what is needed.

## Resuming

1. `PLAN.md` is the schedule and who does each part. `PROTOCOL.md` is how an afternoon is run. `LEDGER.md` says what is open and what is asked of the owner. `DECISIONS.md` (V-numbers) says what was decided and what was rejected.
2. `python3 verdict.py score` shows the bets and which are overdue. Give every overdue bet a verdict before other work.
3. In flight: Run 001 (`runs/001-compounding-creation.md`) is drafted and waiting on the owner to confirm the stake/rule, record the bet, and send the asks (V4). Run 002 (`runs/002-incidental-contact.md`) is also drafted and ready behind Run 001 (V8). L2 is closed in `precommitted.md`.

## Rules

- A bet is recorded before its answer and never edited. A wrong or badly worded bet gets a verdict and a new bet.
- No simulated buyers and no model's estimate of demand or price, anywhere.
- The agent contacts nobody the owner has not named (V4).
- A number quoted here was read in its primary source, or the ledger says it was not.
- Checks, from `verdict/`: `python3 -m unittest`.
