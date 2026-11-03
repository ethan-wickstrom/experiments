# Now

Updated 2026-11-03, second session: the program's first model calls. The key works (REQ-1 closed by the paid smoke). The first call ended frond's run on a reply off the field protocol; frond now recovers such replies or turns them into error steps (G34, D46). E0 runs from a frozen worktree (D47). Every review finding is closed (F1–F68), including FORK's (F22–F31, F60–F67) before E2, the tools arm's (F32–F37, F48) before E1 and scopes' (F38–F40) before E5; E11's reference agents are bounded (G33, D50).

## In flight

E0, the pilot: `uv run python -m bench.matrix bench/experiments/e0-pilot.toml`, run from a worktree of `main` at the merge of the G36 fix (`/home/user/run-e0`, D47), whose `frond/jobs` links to this checkout's `frond/jobs`. One trial per model on 10 tasks, Haiku, then Sonnet, then Opus (D48): $76.50 on the guesses; the runner stops before any job that could pass $100 (D43). Its log is `frond/jobs/E0/run.log`. The first start was stopped in its Haiku job by G36 (DSPy's 64 KiB SSE line limit); its jobs are `frond/jobs/E0-aborted-1`. If the session ended with E0 unfinished, its trials are lost with the VM: rerun it.

E0a is done: 53 of the 55 tasks that start pass under the reference solutions, and the three that fail here are excluded (`bench/results/2026-11-03-e0a-oracle/`).

## Next, in order (research-first, D16)

1. E0: analyse with `uv run python -m bench.analyze bench/experiments/e0-pilot.toml --out bench/results/<date>-e0`; the report's protocol table gives adherence per step (D46). On the first 8 Haiku trials: pass 0/8, $0.04 a trial, 88% of input from cache, 32% of replies off protocol (21% recovered, 11% cost a step). Record the run's spending in `bench/budget.toml` (D49).
2. Review findings: all closed (F1–F68: fixed, verified or declined). New ones go into the ledger as they arrive; REQ-3 holds Devin's unposted security findings.
3. From E0: the screening model (record it in `decisions.md`, then amend E1–E5 before their first trial), E0b's spec (2 more trials per task on that model, for the variance that sizes E1–E6), and the program's budget, as a new REQ from E0's measured costs: E1 alone, at 56 tasks × 3 trials × 2 arms, is several hundred dollars on Sonnet.
4. E1–E6 and E11 in the order in `research.md`, once the budget allows; G39 (how often E11's bounds bind) before E11's analysis.
5. B13 (a TUI world view of branches and scopes), B17 (stop latency).

## Waiting on the owner

- REQ-3: Devin's unposted security findings (three on PR #2, three on #11, one on #12, one on #23, one on #33), visible only in the owner's Devin account. Low priority.

## Facts a fresh session needs

- The key: `CLAUDE_API_KEY` in the environment (REQ-1). Never print it; `echo ${#CLAUDE_API_KEY}` shows that it is there. The runner passes it to Harbor as `ANTHROPIC_API_KEY`. After any paid run, `grep -rlF "$CLAUDE_API_KEY" frond/jobs | wc -l` must print 0.
- Spending: after every paid run, and for every trial killed before it wrote its cost, add a `[[spent]]` entry to `bench/budget.toml` and commit it, or the next VM's guard will not know about the money (G37, D49). 2026-11-03's second session spent $2.36 before E0's restart.
- Paid runs: the paid smoke is `smoke.toml --arms frond` (D45). An experiment runs from a frozen worktree whose `frond/jobs` links here (D47); the runner also stops if frond's source changes between jobs (G35).
- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP. It also makes Docker's default runtime runc behind a wrapper that sets umask 022, because dockerd 29 runs with umask 0 and `docker exec` inherits it (G26, D39). Start dockerd only through the script; the matrix runner refuses a daemon whose `docker exec` umask is not 0022.
- TLS: this VM re-terminates outbound TLS. Every Harbor run here needs `--extra-docker-compose bench/compose/egress-ca.yaml` with `FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt`, or tasks that reach the internet fail for every agent (D27).
- Disk: task images reach 15 GB and Harbor keeps pulled ones. The matrix runner prunes safely; never run `docker image prune` during a sweep (G8).
- Tasks: every TB 4.0 task allows its agent 8 hours. frond's `--max-steps` (40) bounds its cost per task.
- Harbor: `uvx --from harbor[dspy]==0.25.0 --with 'dspy>=3.1.3,<3.3' harbor …`; the runner warms it with retries, since a first install can stall (G32). The oracle agent passes TB 4.0.0 tasks in this VM.
- Opus 5.5 at high effort opens most replies with a line of narration and often skips the field markers (G34); measured, and recovered where unambiguous.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
