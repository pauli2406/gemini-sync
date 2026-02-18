# Test Evidence

## Red Phase (Failing First)

- Command:
  - `./.venv/bin/pytest -q tests/test_connector_directory_support.py tests/test_connector_examples_only_guard.py`
- Result before implementation:
  - `6 failed, 2 passed`
- Failure categories observed:
  - API/Ops/Studio ignored `CONNECTORS_DIR` and still read repo-local `connectors/`.
  - `scripts/check_connector_examples_only.py` did not exist.

## Green Phase

- Targeted new tests:
  - `./.venv/bin/pytest -q tests/test_connector_directory_support.py tests/test_connector_examples_only_guard.py`
  - Result: `8 passed`

- Impacted suites:
  - `./.venv/bin/pytest -q tests/test_api_manual_run.py tests/test_ops_api.py tests/test_studio_api.py tests/test_studio_proposal_generation.py`
  - Result: pass

- Full tests + coverage:
  - `./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60`
  - Result: pass

## Scenario Eval Evidence

- Command:
  - `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`
- Result:
  - `pass_rate_percent=100.0`
  - `critical_pass_rate_percent=100.0`
  - New scenario `external-connector-directory-support`: passed

## Gate Commands

- `./.venv/bin/python scripts/validate_connectors.py` -> pass
- `./.venv/bin/python scripts/check_connector_examples_only.py` -> pass
- `./.venv/bin/ruff check .` -> pass
- `./.venv/bin/python scripts/check_tdd_guardrails.py` -> pass
- `./.venv/bin/python scripts/check_docs_drift.py --changed-file ...` -> pass
- `./.venv/bin/python scripts/check_openapi_drift.py` -> pass
- `./.venv/bin/python scripts/check_connector_reference_drift.py` -> pass
- `./.venv/bin/python scripts/check_security_policy.py` -> pass
- `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_dependency_audit.py` -> pass
- `./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92` -> pass
- `npm --prefix website run build` -> pass
