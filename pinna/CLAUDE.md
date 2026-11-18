# Pinna

A browser workbench for designing struck instruments. Read the [README](README.md)
for what it does, [DECISIONS.md](DECISIONS.md) for why it is built this way and
[LEDGER.md](LEDGER.md) for what is open.

## Layout

- `src/core/`: the numerics, with no DOM dependency. `mesh.ts` (outline to
  triangles), `linalg.ts` (skyline Cholesky, dense eigen solver), `plate.ts`
  (the plate element, modal solve, thickness sensitivities), `design.ts` (shapes,
  presets, the undercut profile), `tune.ts` (the tuner), `materials.ts`.
- `src/app/`: the interface. `worker.ts` runs the solver off the main thread;
  `state.ts` holds the signals and the worker queue; `view.ts` is the three.js
  scene; `audio.ts` is the modal synthesis.
- `test/`: reference checks against published plate and beam frequencies, a
  finite-difference check of the sensitivities, and tuning of three presets.

## Checks

Run from `pinna/`: `bun test`, `bun run check`, `bun run lint`, `bun run format`,
`bun run build`. The tuning tests take about 20 seconds.

## Rules

- Lengths are metres and frequencies hertz inside `src/core/`; the interface converts.
- A change to the element or the solver must keep the reference tests passing
  without loosening their tolerances.
- The app is deployed as the Devin App `pinna` from a production build
  (`bunx vite preview`). Redeploy after a change users should see.
