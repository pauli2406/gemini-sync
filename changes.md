# Changes

## Examples and Guardrails

- Updated canonical sample allowlist:
  - `connectors/examples-allowlist.txt`
  - added missing core sample: `connectors/hr-file-csv.yaml`
- Added strict allowlist drift gate:
  - `scripts/check_connector_examples_allowlist_drift.py`
  - validates missing/stale entries, malformed lines, and duplicates.
- CI integration:
  - `.github/workflows/ci.yaml`
  - added `python scripts/check_connector_examples_allowlist_drift.py`.
- Local contributor workflow updates:
  - `CONTRIBUTING.md`
  - `README.md`
  - added allowlist drift gate command.

## Tests and Evals

- Added unit tests for allowlist drift gate:
  - `tests/test_connector_examples_allowlist_drift.py`
- Existing examples-only guard behavior remains covered:
  - `tests/test_connector_examples_only_guard.py`
- Added scenario eval:
  - `evals/scenarios/connector-examples-allowlist-drift-gate.yaml`
- Registered scenario:
  - `evals/eval_registry.yaml`

## Docs UX Overhaul (Targeted IA Revamp)

- Added onboarding hub:
  - `docs/start-here.md`
- Reorganized docs navigation IA:
  - `website/sidebars.ts`
  - categories now emphasize Start Here, Build Connectors, Migrate & Operate, API & Governance.
- Updated docs homepage entry points:
  - `website/src/pages/index.tsx`
  - added Start Here and Migration Checklist cards and primary CTA changes.
- Upgraded migration guide to strict checklist style:
  - `docs/migration-custom-connectors.md`
  - added preflight, expected outcomes, verification commands, and rollback checks.
- Added cross-links and command updates:
  - `README.md`
  - `docs/operations-runbook.md`
  - `docs/connector-studio.md`
  - `docs/connector-authoring.md`

## Docs Drift Mapping

- Updated `docs/doc_sync_map.yaml` to include:
  - `docs/start-here.md`
  - `docs/migration-custom-connectors.md`
  - `docs/connector-mode-file-pull.md`
  - `docs/connector-provider-file.md`
  in relevant rules (`runtime_and_api`, `connector_contract`, `governance_and_quality`, `docs_site`).
