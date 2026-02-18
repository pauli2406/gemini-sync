# Test Evidence

## Red/Green Coverage for New Gate

- Added dedicated tests for allowlist drift behavior:
  - `tests/test_connector_examples_allowlist_drift.py`
- Test coverage includes:
  - matching inventory pass
  - missing allowlist entry fail
  - stale allowlist entry fail
  - invalid and duplicate allowlist entry fail

## Targeted Validation

- `./.venv/bin/pytest -q tests/test_connector_examples_allowlist_drift.py tests/test_connector_examples_only_guard.py tests/test_connector_samples.py`
  - Result: `11 passed`

## Full Validation

- `./.venv/bin/python scripts/validate_connectors.py` -> pass
- `./.venv/bin/python scripts/check_connector_examples_allowlist_drift.py` -> pass
- `./.venv/bin/python scripts/check_connector_examples_only.py` -> pass
- `./.venv/bin/ruff check .` -> pass
- `./.venv/bin/python scripts/check_tdd_guardrails.py` -> pass
- `./.venv/bin/python scripts/check_docs_drift.py --changed-file ...` -> pass
- `./.venv/bin/python scripts/check_openapi_drift.py` -> pass
- `./.venv/bin/python scripts/check_connector_reference_drift.py` -> pass
- `./.venv/bin/python scripts/check_security_policy.py` -> pass
- `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_dependency_audit.py` -> pass (`No known vulnerabilities found`)
- `./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60`
  - Result: `169 passed`, coverage `85.32%`
- `./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92`
  - Result: pass (`No lines with coverage information in this diff.`)
- `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`
  - Result: `pass_rate_percent=100.0`, `critical_pass_rate_percent=100.0`
  - New scenario `connector-examples-allowlist-drift-gate`: passed
- `npm --prefix website run build` -> pass
