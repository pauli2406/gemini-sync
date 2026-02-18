# Changes

## Runtime + Contract

- Added `file_pull` connector mode and `file` source type:
  - `schemas/connector.schema.json`
  - `gemini_sync_bridge/schemas.py`
- Added file-source fields:
  - `source.path`, `source.glob`, `source.format`, `source.csv.*`
- Added CSV extraction path with parser controls and synthetic file metadata fields:
  - `gemini_sync_bridge/adapters/extractors.py`
- Added compact checkpoint generation/compat parsing for file pulls:
  - `{"v":1,"rw":...,"fc":...,"lm":...,"fh":...}`
- Added duplicate normalized `doc_id` guard for `file_pull`:
  - `gemini_sync_bridge/services/pipeline.py`

## Studio

- Added `file_pull` mode controls in wizard UI:
  - `gemini_sync_bridge/templates/studio/wizard.html`
  - `gemini_sync_bridge/static/studio.js`
- Added Studio source pruning/default handling for file mode switches:
  - `gemini_sync_bridge/services/studio.py`

## Connectors + Evals

- Added sample file connector:
  - `connectors/hr-file-csv.yaml`
- Added scenario evals and registry updates:
  - `evals/scenarios/file-pull-csv-contract.yaml`
  - `evals/scenarios/studio-file-pull-mode-switch-configurability.yaml`
  - `evals/eval_registry.yaml`

## Tests

- Added schema contract tests:
  - `tests/test_connector_schema_file_pull.py`
- Added schema validator branch tests:
  - `tests/test_schemas_file_pull_validation.py`
- Added extractor coverage for row/file modes, parser controls, checkpoint fallback, and error paths:
  - `tests/test_extractors_file_pull.py`
- Added pipeline coverage for file_pull checkpoint persistence and duplicate ID failure:
  - `tests/test_pipeline_file_pull.py`
- Extended Studio and connector sample coverage:
  - `tests/test_studio_draft_validation.py`
  - `tests/test_studio_api.py`
  - `tests/test_studio_ui.py`
  - `tests/test_studio_proposal_generation.py`
  - `tests/test_connector_samples.py`
  - `tests/test_connector_reference_scripts.py`
- Security gate fix for pre-existing token-like literal in tests:
  - `tests/test_outbound_proxy_support.py`

## Documentation

- Added new docs:
  - `docs/connector-mode-file-pull.md`
  - `docs/connector-provider-file.md`
- Updated contract/architecture/authoring docs:
  - `README.md`
  - `docs/connector-authoring.md`
  - `docs/connector-studio.md`
  - `docs/architecture.md`
  - `docs/discovery-engine-cli-playbook.md`
  - `docs/connector-provider-http.md`
  - `docs/connector-provider-postgres.md`
  - `docs/connector-provider-mysql.md`
  - `docs/connector-provider-mssql.md`
  - `docs/connector-provider-oracle.md`
  - `docs/connector-provider-future.md`
  - `docs/roadmap.md`
- Updated docs nav:
  - `website/sidebars.ts`
- Updated docs metadata and regenerated field reference:
  - `schemas/connector.docs-meta.yaml`
  - `docs/connector-field-reference.md`
