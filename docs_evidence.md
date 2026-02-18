# Docs Evidence

## Updated Documentation

- `README.md`
- `CONTRIBUTING.md`
- `docs/start-here.md`
- `docs/connector-authoring.md`
- `docs/connector-studio.md`
- `docs/operations-runbook.md`
- `docs/migration-custom-connectors.md`
- `docs/doc_sync_map.yaml`
- `website/sidebars.ts`
- `website/src/pages/index.tsx`

## Why Docs Were Required

- `connectors/**` changed (`connector_contract` rule).
- `scripts/check_*.py` and `evals/**` changed (`governance_and_quality` rule).
- `website/**` changed (`docs_site` rule).

## Docs UX Outcomes

- Added a clear onboarding hub (`docs/start-here.md`) with role/path-based entry points.
- Improved IA in sidebar for build/migrate/operate journeys.
- Upgraded migration documentation to command-first checklist with explicit expected outputs.
- Ensured connector example policy is discoverable in README/contributing/runbook.
- Expanded docs drift mapping to include new mode/provider and migration/start pages.
