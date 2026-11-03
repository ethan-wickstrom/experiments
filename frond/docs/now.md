# Now

Updated 2026-11-03, at the end of the first session, after the owner's standing orders.

## In flight

E0a, the oracle sweep over all 66 TB 4.0 tasks, is running in the session VM. Its results go to `bench/results/` when it finishes; a fresh session reruns it with `harbor run -d terminal-bench/terminal-bench@4.0.0 -a oracle -e docker -n 2 --delete`.

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
- Harbor: `uvx --from harbor harbor …` (0.25.0). The oracle agent passes a TB 4.0.0 task in this VM.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
