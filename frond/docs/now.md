# Now

Updated 2026-11-03, at the end of the first session, after the owner's standing orders.

## In flight

Nothing is half done. B1 (effort, and the native route behind a public `ANTHROPIC_BASE_URL`) is on `main`.

## Next, in order (research-first, D16)

1. B2: per-call usage, protocol violations, failed edits and stale actions in `--export`.
2. B3: arm flags, the matrix runner (`bench/matrix.py`) and the analysis script (`bench/analyze.py`).
3. B12: redaction, before any results are committed.
4. B4: worlds. A content-addressed store with snapshot, checkout and diff, and merge3; undo becomes a revert by merge, which closes R2, R3 and P2.
5. B5, B6 and B7: freshness, the forkable REPL, then fork, select and merge.
6. E0, as soon as REQ-1 arrives. Then E1–E6 in the order in `research.md`.

## Waiting on the owner

- REQ-1: an Anthropic API key with a $100 cap. It unblocks E0, estimated at $45–75.
- REQ-3: Devin's unposted findings on PR #2. Low priority.

## Facts a fresh session needs

- Docker: `frond/scripts/dev-env.sh` starts dockerd and serves Docker Hub pulls from mirror.gcr.io, because Docker Hub rate-limits this VM's IP.
- Harbor: `uvx --from harbor harbor …` (0.25.0). The oracle agent passes a TB 4.0.0 task in this VM.
- In default Docker, frond's sandbox runs under Landlock: user namespaces are refused there.
- VM limits: 4 CPUs, 15 GB RAM, 29 GB of disk.
