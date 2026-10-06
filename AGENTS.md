# Provider repository map

Read `README.md` for usage and runtime boundaries. Dependency versions and package entry points belong to `package.json`; CI prerequisite pins belong to `.github/workflows/acceptance.yml`.

## Owners

- `src/index.ts`: Pi provider registration, model discovery and provider lifetime.
- `src/bridge.ts` + `runtime/bridge.py`: JSONL protocol and process lifecycle.
- `src/transcript.ts`: Pi transcript projection and persisted native replay.
- `src/stream.ts`: assistant events, tool publication and accounting provenance.
- `vendor/source.json`: upstream revisions, original hashes and bundled-helper provenance. Read `vendor/PATCHES.md` before changing imported transport or its build inputs; retain the upstream license notices.

## Build and verification

Run commands from this repository root; `pnpm-workspace.yaml` isolates it from ancestor workspaces.

- `pnpm check`: TypeScript checks.
- `pnpm acceptance`: build and deterministic Pi/CLI consumer checks without Anthropic inference.
- `pnpm acceptance:live`: explicit real subscription inference; obtain authorization before running it.

The Pi manifest loads generated `dist/index.js`, not `src/index.ts`. Run `pnpm build` before local package use or after source edits. `scripts/build.mjs` owns the bundle and its allowed dependency inputs.

`acceptance/provider.py` owns fixtures, resource cleanup and candidate-bound receipts under ignored `.artifacts/`. A model-list exit code or sign-in status alone does not prove that the extension loads or inference works; use the consumer acceptance path. Keep local transcripts and receipts outside publication.
