# Changes

## Runtime Configuration and Discovery

- Added shared connector path helper:
  - `gemini_sync_bridge/utils/paths.py`
  - `configured_connectors_dir()` resolves connector discovery from `CONNECTORS_DIR` with fallback `connectors`.
- Added settings contract:
  - `gemini_sync_bridge/settings.py` now includes `CONNECTORS_DIR` via `connectors_dir`.
- Replaced hardcoded connector directory resolution in:
  - `gemini_sync_bridge/api.py`
  - `gemini_sync_bridge/services/ops.py`
  - `gemini_sync_bridge/services/studio.py`

## Connector Commit Guardrail

- Added connector examples allowlist file:
  - `connectors/examples-allowlist.txt`
- Added CI/local guard script:
  - `scripts/check_connector_examples_only.py`
  - Fails when non-allowlisted files under `connectors/` are changed.
- Added CI step:
  - `.github/workflows/ci.yaml`
- Added contributing command:
  - `CONTRIBUTING.md`

## Tests and Evals

- Added connector discovery regression tests:
  - `tests/test_connector_directory_support.py`
  - Covers API/Ops/Studio env-driven discovery, default fallback behavior, and Studio proposal path contract.
- Added guard script tests:
  - `tests/test_connector_examples_only_guard.py`
- Added scenario eval:
  - `evals/scenarios/external-connector-directory-support.yaml`
- Registered scenario:
  - `evals/eval_registry.yaml`

## Documentation

- Updated env/config and workflow guidance:
  - `.env.example`
  - `README.md`
  - `docs/operations-runbook.md`
  - `docs/connector-authoring.md`
  - `docs/connector-studio.md`
  - `docs/getting-started-local.mdx`
  - `docs/migration-custom-connectors.md`
  - `docs/roadmap.md`
  - `website/sidebars.ts`
- Clarified:
  - `CONNECTORS_DIR` controls API/Ops/Studio discovery path.
  - `GITHUB_REPO` is the connector-config repository target for Studio proposals.
  - This repo’s `connectors/` directory is for curated examples.
  - Existing staging users can migrate with a step-by-step cutover playbook.
