# Docs Evidence

## Updated Documentation

- `.env.example`
- `README.md`
- `docs/operations-runbook.md`
- `docs/connector-authoring.md`
- `docs/connector-studio.md`
- `docs/getting-started-local.mdx`
- `docs/migration-custom-connectors.md`
- `docs/roadmap.md`
- `website/sidebars.ts`
- `CONTRIBUTING.md`

## Why Docs Were Required

- `gemini_sync_bridge/**` changed (`runtime_and_api` rule).
- `connectors/**` changed (`connector_contract` rule).
- `scripts/check_*.py` and `evals/**` changed (`governance_and_quality` rule).
- `website/**` changed (`docs_site` rule).

## Coverage of User-Facing Changes

- Added `CONNECTORS_DIR` env contract and default behavior.
- Clarified repo separation model:
  - runtime/tooling + curated examples in this repo,
  - user-specific connectors in external directory/config repo.
- Clarified `GITHUB_REPO` as Connector Studio PR target repository.
- Documented examples-only connector guard command for local/CI checks.
- Added a migration playbook for legacy staging setups that currently store custom connectors in this runtime repo.
- Added docs sidebar navigation entry for the migration guide.
