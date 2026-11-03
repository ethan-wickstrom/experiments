# Now

Updated 2026-11-03, end of the first session: the owner granted $100 and added the API key; every hypothesis H1–H6 has both arms and every experiment is pre-registered; the review findings that touch frond's default configuration are fixed.

## In flight

Nothing runs. The next session starts the program's first model calls:

1. `frond/scripts/dev-env.sh` (Docker with the umask-022 runtime, the mirror, the CA).
2. The key: the owner stored it as `CLAUDE_API_KEY` (REQ-1). Never print it; `echo ${#CLAUDE_API_KEY}` shows that it is there. The runner passes it to Harbor as `ANTHROPIC_API_KEY`.
3. A free check that it works from the VM and from inside a task container: `GET https://api.anthropic.com/v1/models` with the key, from the VM and through `docker run` with the egress CA mounted.
4. `uv run python -m bench.matrix bench/experiments/smoke.toml` (one task, every flag), then check that the key's value appears in no file under `jobs/` (`grep -rlF "$CLAUDE_API_KEY" jobs | wc -l` must print 0) before anything is committed.
5. E0: `uv run python -m bench.matrix bench/experiments/e0-pilot.toml`, about $45–75; the runner stops before any job that could pass $100 (D43).

E0a is done: 53 of the 55 tasks that start pass under the reference solutions, and the three that fail here are excluded (`bench/results/2026-11-03-e0a-oracle/`).

## Next, in order (research-first, D16)

1. E0, as above.
2. The rest of the review findings (ledger, F-rows still open), before the experiment whose arm they touch: FORK and the forkable REPL (F22–F31) before E2, the tools arm (F32–F37, F48) before E1, scopes (F38–F40) before E5, the startup check (F41–F44) and F49 any time. Closed: F1–F21 and F45–F47 (fixed, verified or declined).
3. From E0: the screening model (record it in `decisions.md`, then amend E1–E5 before their first trial), sample sizes from the variance, and the program's budget (a new REQ).
4. E1–E6 and E11 in the order in `research.md`.
5. B13 (a TUI world view of branches and scopes), B17 (stop latency).

## Waiting on the owner

- REQ-1: the key is in the environment as `CLAUDE_API_KEY`, for sessions started after it was added; it closes with the smoke run.
- REQ-3: Devin's unposted security findings (three on PR #2, three on #11, one on #12, one on #23), visible only in the owner's Devin account. Low priority.

## Facts a fresh session needs

- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP. It also makes Docker's default runtime runc behind a wrapper that sets umask 022, because dockerd 29 runs with umask 0 and `docker exec` inherits it (G26, D39). Start dockerd only through the script; the matrix runner refuses a daemon whose `docker exec` umask is not 0022.
- TLS: this VM re-terminates outbound TLS. Every Harbor run here needs `--extra-docker-compose bench/compose/egress-ca.yaml` with `FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt`, or tasks that reach the internet fail for every agent (D27).
- Disk: task images reach 15 GB and Harbor keeps pulled ones. The matrix runner prunes safely; never run `docker image prune` during a sweep (G8).
- Tasks: every TB 4.0 task allows its agent 8 hours. frond's `--max-steps` (40) bounds its cost per task.
- Harbor: `uvx --from harbor==0.25.0 harbor …`. The oracle agent passes TB 4.0.0 tasks in this VM.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
