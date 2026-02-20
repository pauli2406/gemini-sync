# Test Evidence

## Red Phase

- New bucket-only runtime behavior and latest alias output had no prior tests.
- New schema options (`spec.ingestion.enabled`, `spec.output.publishLatestAlias`) had no prior validation tests.
- New sql_pull raw CSV export behavior had no prior tests.

## Green Phase

- Added runtime test:
  - `tests/test_pipeline_bucket_only.py::test_run_connector_bucket_only_skips_gemini_ingestion`
- Added/updated schema tests:
  - `tests/test_schemas_file_pull_validation.py`
  - `tests/test_connector_schema_file_pull.py`
- Added publisher alias tests:
  - `tests/test_publisher.py`
- Added eval scenario:
  - `evals/scenarios/bucket-only-sql-pull-contract.yaml`

## Commands

```bash
pytest tests/test_pipeline_bucket_only.py tests/test_publisher.py tests/test_schemas_file_pull_validation.py tests/test_connector_schema_file_pull.py -q
python scripts/validate_connectors.py
python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
```
