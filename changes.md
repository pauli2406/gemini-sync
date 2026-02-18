# Changes

## Docs Hard-Cutover

- Replaced legacy flat docs with Diataxis structure:
  - `docs/tutorials/**`
  - `docs/how-to/**`
  - `docs/concepts/**`
  - `docs/reference/**`
  - `docs/contributing/**`
  - `docs/start-here.mdx`, `docs/roadmap.mdx`, `docs/changelog.mdx`
- Removed legacy docs files under `docs/*.md(x)` after migration.

## Docusaurus

- Updated `website/sidebars.ts` to Diataxis categories.
- Updated `website/docusaurus.config.ts` navbar/footer links.
- Rewrote `website/src/pages/index.tsx` and `website/src/pages/index.module.css` for new IA entry points.

## Tooling and Gates

- Updated connector reference script defaults:
  - `scripts/export_connector_reference.py` default output -> `docs/reference/connector-fields.md`
  - `scripts/check_connector_reference_drift.py` default target -> `docs/reference/connector-fields.md`
- Regenerated `docs/reference/connector-fields.md`.
- Rewrote `docs/doc_sync_map.yaml` for new paths and consistency files/tokens.

## Readme and Agent Guide

- Fully rewrote `README.md` for 2-minute pitch + quickstart + audience split + gate summary.
- Fully rewrote `llm.txt` as contributor/agent contract aligned to the new docs map.

## Tests and Evals

- Expanded `tests/test_connector_reference_scripts.py` with default-path behavior tests.
- Updated `evals/scenarios/connector-reference-drift-gate.yaml` for new default target path.
- Updated docs/tdd gate tests to use new architecture doc path.
