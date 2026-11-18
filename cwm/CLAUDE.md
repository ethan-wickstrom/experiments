# Working on CWM

Keep the oracle (what happened), the predictor (what might happen), and the edit history distinct. The implementation lives in one importable TypeScript module so the full library is portable as a single code block. Public behavior and supported programs are in [README.md](README.md); see [decisions](DECISIONS.md) and [ledger](LEDGER.md) before extending it.

From this directory with Bun 1.4+ and Node 24.11+ on PATH:

```sh
bun install --frozen-lockfile
bun check
bun run lint
bun run format
bun test
```

Oxlint uses tsrs for type-aware lint and type checking. The native TypeScript compiler is pinned for an independent check with `bun x tsc --noEmit`. Use the list insertion, failed repair, and held-out rollout tests to distinguish trace fidelity from predictive accuracy.
