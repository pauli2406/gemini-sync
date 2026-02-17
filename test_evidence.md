# Test Evidence

## Red Phase (Failing First)

- Command:
  - `.venv/bin/pytest -q tests/test_outbound_proxy_support.py`
- Result before implementation:
  - collection error: `ModuleNotFoundError: No module named 'gemini_sync_bridge.utils.http_clients'`
- Failure intent:
  - Enforce creation of shared outbound HTTP client helper before runtime wiring.

## Green Phase

- New proxy suite:
  - `.venv/bin/pytest -q tests/test_outbound_proxy_support.py`
  - Result: `7 passed`
- Impacted runtime suites:
  - `.venv/bin/pytest -q tests/test_extractors_rest_pull.py tests/test_extractors_rest_pull_oauth.py tests/test_gemini_ingestion.py tests/test_github_pr_service.py`
  - Result: `19 passed`

## Scenario Eval

- Command:
  - `PATH=.venv/bin:$PATH .venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`
- Result:
  - `pass_rate_percent=100.0`
  - `critical_pass_rate_percent=100.0`
  - New scenario `outbound-proxy-env-support`: passed

## Gate Commands

- `.venv/bin/ruff check .` -> pass
- `.venv/bin/python scripts/check_tdd_guardrails.py` -> pass
- `.venv/bin/python scripts/check_docs_drift.py --changed-file ...` -> pass
- `.venv/bin/python scripts/check_openapi_drift.py` -> pass
- `.venv/bin/python scripts/check_connector_reference_drift.py` -> pass
- `PATH=.venv/bin:$PATH .venv/bin/python scripts/check_security_policy.py` -> pass
- `PATH=.venv/bin:$PATH .venv/bin/python scripts/run_dependency_audit.py` -> pass (`No known vulnerabilities found`)
- `.venv/bin/python scripts/validate_connectors.py` -> pass
