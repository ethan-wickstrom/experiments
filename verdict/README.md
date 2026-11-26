# Verdict

Building software got cheap. Finding out whether anyone needs what was built did not. Verdict is the work of making that answer arrive sooner for people who have lived with a problem for years: an afternoon to learn whether the problem deserves a week, a week to learn whether a fix works in daily use, six weeks to learn whether it deserves the next year.

It holds three things:

- [`PLAN.md`](PLAN.md): the shortest schedule the world allows, and who has to do each part.
- [`PROTOCOL.md`](PROTOCOL.md): how one afternoon is run, and what counts as an answer.
- [`bets.jsonl`](bets.jsonl) and [`verdict.py`](verdict.py): every guess, written down before the world answers, and how good the guesses have been.

## Run it

Python 3.12, no dependencies. From this directory:

```sh
python3 verdict.py bet ID 0.3 2026-12-10 "The claim." --decided-by "The real event that settles it."
python3 verdict.py verdict ID yes --evidence "What happened, and where to see it."
python3 verdict.py score
python3 -m unittest
```

A run of the protocol is recorded by copying [`runs/TEMPLATE.md`](runs/TEMPLATE.md).
