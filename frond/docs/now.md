# Now

Updated 2026-11-03, second session: the program's first model calls. E0 is done on the json protocol (D53), where 1 reply in Haiku's 325 was off it, against about a third under DSPy's field markers (G48). The screening model is Opus 5.5 (D56): 3 of 7 scored trials passed, at $1.33 a trial. Tasks its cyber classifier refuses are excluded (D57). The tools arm acts by native tool calls (D55). E1–E6 need money: REQ-4.

## In flight

E0b, variance on the screening model, runs next: `bench/experiments/e0b-variance.toml`, two Opus trials on each of E0's 8 tasks that D57 keeps, in one job, from a frozen worktree of `main` (`/home/user/run-e0b`, D47) whose `frond/jobs` links to this checkout's: `uv run python -m bench.matrix bench/experiments/e0b-variance.toml`, log `frond/jobs/E0b/run.log`. About $21 expected; the guard allows it (D43). A VM restart kills the run and Docker: run `scripts/dev-env.sh`, then rerun from the same worktree, which resumes.

E0 is done (`bench/results/2026-11-03-e0/`): Haiku 0 of 10, Sonnet 1 of 7 scored, Opus 3 of 7 scored, at $0.04, $0.91 and $1.33 a trial; 89–92% of input read from cache. Its earlier starts are kept for the guard: `jobs/E0-aborted-1` (G36), `jobs/E0-protocol-v1` (G41), `jobs/E0-protocol-v2` (G45), `jobs/E0-markers` (G48, `bench/results/2026-11-03-e0-markers/`). E0a is done: 53 of the 55 tasks that start pass under the reference solutions (`bench/results/2026-11-03-e0a-oracle/`).

## Next, in order (research-first, D16)

1. E0b: analyse with `uv run python -m bench.analyze bench/experiments/e0b-variance.toml --out bench/results/<date>-e0b`, together with E0's Opus trials for three per task; record its spending (D49). From its within- and between-task variance, set E1–E6's sample sizes in `research.md`, and amend REQ-4's estimate. Check whether `biped-contact-dynamics` is still refused after a cut-off (G47).
2. E1–E6 and E11 in the order in `research.md`, once REQ-4 is granted; a partial grant starts E1 first.
3. G50 (thinking cut off at the 32k output limit), measured on E0b's trials before E1: a larger `max_tokens`, a task budget, or nothing.
4. Review findings as they arrive (F1–F71 closed); REQ-3 holds Devin's unposted security findings.
5. B13 (a TUI world view of branches and scopes), B17 (stop latency).

## Waiting on the owner

- REQ-4: money for E1–E6 on Opus 5.5, about $2,400 at E0's measured cost; E1 alone about $500. Spent so far $39.82 of the $100 grant.
- REQ-3: Devin's unposted security findings (three on PR #2, three on #11, one on #12, one on #23, one on #33), visible only in the owner's Devin account. Low priority.

## Facts a fresh session needs

- The key: `CLAUDE_API_KEY` in the environment (REQ-1). Never print it; `echo ${#CLAUDE_API_KEY}` shows that it is there. The runner passes it to Harbor as `ANTHROPIC_API_KEY`. After any paid run, `grep -rlF "$CLAUDE_API_KEY" frond/jobs | wc -l` must print 0.
- Spending: after every paid run, and for every trial killed before it wrote its cost, add a `[[spent]]` entry to `bench/budget.toml` and commit it, or the next VM's guard will not know about the money (G37, D49). Every 2026-11-03 run is recorded there: $39.82 by E0's end.
- Paid runs: the paid smoke is `smoke.toml --arms frond` (D45). An experiment runs from a frozen worktree whose `frond/jobs` links here (D47); the runner also stops if frond's source changes between jobs (G35).
- A run lasts only while the session is active: the container is suspended about a minute after a turn ends, killing detached processes, unless a background task of the session is still running (G44). Wait on a paid run with a background task that ends when the run does; after a restart, run `scripts/dev-env.sh` and rerun the spec, which resumes.
- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP. It also makes Docker's default runtime runc behind a wrapper that sets umask 022, because dockerd 29 runs with umask 0 and `docker exec` inherits it (G26, D39). Start dockerd only through the script; the matrix runner refuses a daemon whose `docker exec` umask is not 0022.
- TLS: this VM re-terminates outbound TLS. Every Harbor run here needs `--extra-docker-compose bench/compose/egress-ca.yaml` with `FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt`, or tasks that reach the internet fail for every agent (D27).
- Disk: task images reach 15 GB and Harbor keeps pulled ones. The matrix runner prunes safely; never run `docker image prune` during a sweep (G8).
- Tasks: every TB 4.0 task allows its agent 8 hours. frond's `--max-steps` (40) bounds its cost per task.
- Harbor: `uvx --from harbor[dspy]==0.25.0 --with 'dspy>=3.1.3,<3.3' harbor …`; the runner warms it with retries, since a first install can stall (G32). The oracle agent passes TB 4.0.0 tasks in this VM.
- Opus 5.5 at high effort opens most replies with a line of narration and often skips the field markers (G34); measured, and recovered where unambiguous.
- Never ask a model to put its reasoning in its reply: Anthropic's classifiers refuse that as reasoning extraction (Sonnet 5.5 did, G41). Each step's reply has a `note` field instead (D51); a refusal ends the turn as a provider failure (G43).
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
