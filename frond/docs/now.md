# Now

Updated 2026-11-03, first session, after B9 (scopes): every hypothesis H1–H6 now has both arms.

## In flight

E0a, the oracle sweep, runs through the matrix runner on the 56 TB 4.0 tasks that can start in this VM (G20): `uv run python -m bench.matrix bench/experiments/e0a-oracle.toml`, jobs in `frond/jobs/E0a/`. Running the same command again resumes it. When it finishes:
- `python -m bench.analyze bench/experiments/e0a-oracle.toml --out bench/results/2026-11-03-e0a-oracle`, plus `--failing oracle > bench/results/2026-11-03-e0a-oracle/oracle-failures.txt`, which later specs exclude;
- write `bench/experiments/e0-pilot.toml` (10 sampled tasks × 3 trials on Opus 5.5; 10 × 1 on Sonnet 5.5 and Haiku 5.5).

## Next, in order (research-first, D16)

1. When E0a finishes: its summary in `bench/results/`, the oracle-failure exclusion list, and the E0 spec.
2. Specs for E1–E6 and E11 in `bench/experiments/`, pre-registered before any key arrives.
3. E0, as soon as REQ-1 arrives. Then E1–E6 in the order in `research.md`.
4. B13 (a TUI world view of branches and scopes), B11 (pin DSPy), G21 (world store GC).

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
