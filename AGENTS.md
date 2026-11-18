# Working in experiments

Read the [repository rules](CLAUDE.md) and the current project's own `CLAUDE.md`.

## TypeScript and Effect

Use Effect v4 or newer for new Effect work. Before writing Effect code, read
[`repos/effect/LLMS.md`](repos/effect/LLMS.md). Check idioms and API signatures in
the local [source](repos/effect/packages/effect/src/) and [tests](repos/effect/packages/effect/test/)
instead of guessing or using examples for a different release.

Everything under `repos/` is read-only upstream reference material. Don't edit
or format it, install its workspace, or import from it. Install the matching
`effect` npm package in the consuming project and import from its public entry
points. Run each project's own checks, not the upstream test suites.

See [updating the reference](README.md#effect-source-reference) when upgrading.
