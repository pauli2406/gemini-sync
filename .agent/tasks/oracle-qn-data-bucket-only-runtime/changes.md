# Changes

## Runtime

- `gemini_sync_bridge/schemas.py`
  - Added `spec.ingestion.enabled` contract.
  - Made `spec.gemini` conditionally required only when ingestion is enabled.
  - Added `spec.output.publishLatestAlias`.
  - Added `spec.output.format: csv` support for raw sql_pull exports.
  - Made `spec.mapping` optional for csv output mode.

- `gemini_sync_bridge/services/pipeline.py`
  - Skip Gemini ingestion when `spec.ingestion.enabled` is false.
  - Added sql_pull csv branch that bypasses normalization/diffing and publishes raw rows.

- `gemini_sync_bridge/services/publisher.py`
  - Added optional stable latest aliases under `connectors/<prefix>/latest/`.
  - `state/latest_success.json` points to latest alias manifest when enabled.
  - Added CSV artifact publishing (`rows.csv`) with full-row field coverage.

## Contracts / Schema / Docs

- `schemas/connector.schema.json`
  - Added `spec.ingestion.enabled` and `spec.output.publishLatestAlias`.
  - Added conditional requirement for `spec.gemini`.
  - Added output format enum (`ndjson`, `csv`) and csv-mode validation constraints.
- `schemas/connector.docs-meta.yaml`
  - Added docs metadata for the new fields.
- `docs/reference/connector-fields.md`
  - Regenerated from schema + docs meta.
- `README.md`, `docs/how-to/connector-authoring.mdx`, `docs/how-to/connectors/sql-pull.mdx`
  - Added usage guidance for bucket-only and latest alias behavior.

## Tests / Evals

- Added `tests/test_pipeline_bucket_only.py`.
- Updated `tests/test_schemas_file_pull_validation.py`.
- Updated `tests/test_connector_schema_file_pull.py`.
- Updated `tests/test_publisher.py`.
- Added `evals/scenarios/bucket-only-sql-pull-contract.yaml`.
- Updated `evals/eval_registry.yaml`.
