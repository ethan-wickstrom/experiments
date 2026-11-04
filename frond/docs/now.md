# Now

Updated 2026-11-04, second session: E0 and E0b are done. Each code step replies with one JSON object held to its schema (D53), and the tools arm acts by native tool calls (D55). The screening model is Opus 5.5 (D56), on 51 TB 4.0 tasks (D57), at about $1.50 a trial. E0b's variance sets E1–E3 at 3 trials per task (`research.md`). The reasoning-extraction refusals come during long thinking, and more often the longer it runs (D60); whether thinking is the cause is a hypothesis E0c tests (G47). E1–E6 need money: REQ-4. $68.12 of the $100 grant is spent.

## In flight

Nothing runs. E0b is done (`bench/results/2026-11-04-e0b/`): 5 of 13 scored Opus trials passed, $24.17 for 16; within-task variance 0.083, between-task 0.194. E0 is done (`bench/results/2026-11-03-e0/`). Their jobs are under `frond/jobs/E0` and `frond/jobs/E0b`, and their spending is recorded in `bench/budget.toml`, so a new VM's guard knows it. The frozen worktrees `/home/user/run-e0` and `/home/user/run-e0b` can be removed.

## Next, in order (research-first, D16)

1. E0c (effort on the screening model, D60) and then E1–E6 and E11, once REQ-4 is granted; a partial grant starts E0c and E1.
2. G51: mitigated by D59 (an unfinished step is exported; a trial's agent gets 2 hours). Find the cause when an export next shows an unfinished step.
3. G50 (thinking cut off at the 32k output limit): Opus had 1 cut-off reply in E0b's 16 trials, against Sonnet's 5 in one E0 trial, so on the screening model it may need nothing; decide before E1.
4. Review findings as they arrive (F1–F77 closed); REQ-3 holds Devin's unposted security findings.
5. B13 (a TUI world view of branches and scopes), B17 (stop latency).

## Waiting on the owner

- REQ-4: money for E0c and E1–E6 on Opus 5.5, about $2,400 at E0's and E0b's measured cost; E0c about $40, E1 about $500. Spent so far $68.12 of the $100 grant.
- REQ-3: Devin's unposted security findings (three on PR #2, three on #11, one on #12, one on #23, one on #33), visible only in the owner's Devin account. Low priority.

## Facts a fresh session needs

- The key: `CLAUDE_API_KEY` in the environment (REQ-1). Never print it; `echo ${#CLAUDE_API_KEY}` shows that it is there. The runner passes it to Harbor as `ANTHROPIC_API_KEY`. After any paid run, `grep -rlF "$CLAUDE_API_KEY" frond/jobs | wc -l` must print 0.
- Spending: after every paid run, and for every trial killed before it wrote its cost, add a `[[spent]]` entry to `bench/budget.toml` and commit it, or the next VM's guard will not know about the money (G37, D49). Every run is recorded there: $68.12 by 2026-11-04.
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
