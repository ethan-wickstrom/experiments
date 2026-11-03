# Now

Updated 2026-11-03, first session, after fixing the infrastructure faults E0a found (G7, G8).

## In flight

E0a, the oracle sweep over all 66 TB 4.0 tasks, is running again in the session VM, now with the egress-CA overlay, the safe pruner and retries for failed environment starts. Its summary goes to `bench/results/` when it finishes. A fresh session reruns it from `frond/` with the command in `research.md` ("Running"), using `-a oracle -n 2 --max-retries 2` and no model; `harbor job resume -p <job dir>` continues a stopped one.

## Next, in order (research-first, D16)

1. B3: arm flags, the matrix runner (`bench/matrix.py`) and the analysis script (`bench/analyze.py`).
2. B12: redaction, before any results are committed.
3. B4b: wire worlds into frond, with undo as a revert of the turn's steps, which closes R2, R3 and P2.
4. B5, B6 and B7: freshness (including stale-action counts), the forkable REPL, then fork, select and merge.
5. E0, as soon as REQ-1 arrives. Then E1–E6 in the order in `research.md`.

## Waiting on the owner

- REQ-1: an Anthropic API key with a $100 cap. It unblocks E0, estimated at $45–75.
- REQ-3: Devin's unposted findings on PR #2. Low priority.

## Facts a fresh session needs

- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP.
- TLS: this VM re-terminates outbound TLS. Every Harbor run here needs `--extra-docker-compose bench/compose/egress-ca.yaml` with `FROND_EGRESS_CA=/root/.ccr/ca-bundle.crt`, or tasks that reach the internet fail for every agent (D27).
- Disk: task images reach 15 GB and Harbor keeps pulled ones. Run `bench/prune.py --while-pid <harbor pid>` beside a sweep; never `docker image prune` during one (G8).
- Harbor: `uvx --from harbor==0.25.0 harbor …`. The oracle agent passes TB 4.0.0 tasks in this VM.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
