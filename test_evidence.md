# Test Evidence

## Red Phase Evidence

- Baseline schema on `origin/main` rejects new file connector contract:
  - Command:
    - `PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/python - <<'PY' ... git show origin/main:schemas/connector.schema.json ... PY`
  - Result:
    - `errors=4`
    - `spec.mode: 'file_pull' is not one of ['sql_pull', 'rest_pull', 'rest_push']`
    - `spec.source: 'secretRef' is a required property`
    - `spec.source: Additional properties are not allowed ('csv', 'format', 'glob', 'path' were unexpected)`
    - `spec.source.type: 'file' is not one of ['postgres', 'mssql', 'mysql', 'oracle', 'http']`

## Green Phase Evidence

- Focused new/updated suites:
  - `.venv/bin/pytest tests/test_connector_schema_file_pull.py tests/test_extractors_file_pull.py tests/test_pipeline_file_pull.py tests/test_schemas_file_pull_validation.py -q`
  - Result: pass
- Full test suite with coverage:
  - `PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60`
  - Result: `156 passed`, coverage `85.22%`
- Diff coverage:
  - `PATH="$(pwd)/.venv/bin:$PATH" diff-cover coverage.xml --compare-branch=origin/main --fail-under=92`
  - Result: pass (`100%` diff coverage)

## Scenario Eval Evidence

- Command:
  - `PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`
- Result:
  - `pass_rate_percent=100.0`
  - `critical_pass_rate_percent=100.0`
  - New scenarios passed:
    - `file-pull-csv-contract`
    - `studio-file-pull-mode-switch-configurability`

## Gate Commands

```bash
PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/python scripts/validate_connectors.py
.venv/bin/ruff check .
.venv/bin/python scripts/check_tdd_guardrails.py
.venv/bin/python scripts/check_docs_drift.py
.venv/bin/python scripts/check_security_policy.py
PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/python scripts/run_dependency_audit.py
PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
PATH="$(pwd)/.venv/bin:$PATH" diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
PATH="$(pwd)/.venv/bin:$PATH" .venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
```

All commands above completed successfully.
