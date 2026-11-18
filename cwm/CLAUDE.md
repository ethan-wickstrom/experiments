# Working on CWM

Keep the oracle (what happened), the predictor (what might happen), and the edit history distinct. The implementation lives in one importable TypeScript module so the full library is portable as a single code block. Public behavior and supported programs are in [README.md](README.md); see [decisions](DECISIONS.md) and [ledger](LEDGER.md) before extending it.

For the interactive coding loop, read [PROMPTING.md](PROMPTING.md). The CLI uses the structured predictor for self-fed rollouts and the [MiniCPM5 adapter](bench/minicpm/README.md) for direct next-pause prompts and code proposals. Keep expected behavior outside the forecast and preserve partial forecasts on abstention.

Project chat uses [the shared protocol](project/protocol.ts) and [isolated Bun runner](project/sandbox.ts). Read the [development experiment](bench/development/README.md) and [independent evaluation](bench/development/evaluation.md) before changing the model, action availability, tool observations or held tasks. Use `CWM_TEST_DOCKER=1 bun test project/sandbox.test.ts` to exercise actual cancellation and time limits with the sandbox image installed.

From this directory with Bun 1.4+ and Node 24.11+ on PATH:

```sh
bun install --frozen-lockfile
bun check
bun run lint
bun run format
bun test
```

Oxlint uses tsrs for type-aware lint and type checking. The native TypeScript compiler is pinned for an independent check with `bun x tsc --noEmit`. Use the list insertion, failed repair, and held-out rollout tests to distinguish trace fidelity from predictive accuracy.
