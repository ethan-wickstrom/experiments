# Now

Updated 2026-11-03, first session: every hypothesis H1–H6 has both arms, every experiment is pre-registered, and E0a is finishing.

## In flight

E0a, the oracle sweep, has scored 52 of the 56 TB 4.0 tasks that start in this VM (G20); the oracle failed three (`bench/results/2026-11-03-e0a-oracle/oracle-failures.txt`, provisional until it finishes). Resume or rerun it with `uv run python -m bench.matrix bench/experiments/e0a-oracle.toml`; then write its report with `uv run python -m bench.analyze bench/experiments/e0a-oracle.toml --out bench/results/2026-11-03-e0a-oracle` and the final list with `--failing oracle`.

## Next, in order (research-first, D16)

1. E0, as soon as REQ-1 arrives: `bench/experiments/e0-pilot.toml`. First run `smoke.toml` with the real key's environment (free: it stops at the first call only with a bad key; with a real one it is one short run).
2. From E0: the screening model (record it in `decisions.md`, then amend E1–E5 before their first trial), sample sizes from the variance, and the program's budget (a new REQ).
3. E1–E6 and E11 in the order in `research.md`.
4. B13 (a TUI world view of branches and scopes), B14 (narrowing hints in truncation notes), B17 (stop latency).

## Waiting on the owner

- REQ-1: an Anthropic API key with a $100 cap. It unblocks E0, estimated at $45–75.
- REQ-3: Devin's unposted findings on PR #2. Low priority.

## Facts a fresh session needs

- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP.
- TLS: this VM re-terminates outbound TLS. Every Harbor run here needs `--extra-docker-compose bench/compose/egress-ca.yaml` with `FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt`, or tasks that reach the internet fail for every agent (D27).
- Disk: task images reach 15 GB and Harbor keeps pulled ones. The matrix runner prunes safely; never run `docker image prune` during a sweep (G8).
- Tasks: every TB 4.0 task allows its agent 8 hours. frond's `--max-steps` (40) bounds its cost per task.
- Harbor: `uvx --from harbor==0.25.0 harbor …`. The oracle agent passes TB 4.0.0 tasks in this VM.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
