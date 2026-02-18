# Test Evidence

## Red Phase Evidence

- New default-path expectations for connector reference scripts were added in tests first:
  - `tests/test_connector_reference_scripts.py`
- During cutover, docs build initially failed due unquoted frontmatter titles (`Provider: ...`), proving route/content regressions were caught by docs build gate before final green.

## Green Phase Evidence

- `./.venv/bin/pytest -q tests/test_connector_reference_scripts.py tests/test_openapi_scripts.py tests/test_quality_gate_docs.py tests/test_quality_gate_tdd.py`
  - Result: `16 passed`
- `./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60`
  - Result: `171 passed`, total coverage `85.27%`
- `./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92`
  - Result: pass (`No lines with coverage information in this diff.`)

## Commands

```bash
./.venv/bin/python scripts/validate_connectors.py
./.venv/bin/python scripts/check_connector_examples_allowlist_drift.py
./.venv/bin/python scripts/check_connector_examples_only.py
./.venv/bin/ruff check .
./.venv/bin/python scripts/check_tdd_guardrails.py
./.venv/bin/python scripts/check_docs_drift.py
./.venv/bin/python scripts/check_openapi_drift.py
./.venv/bin/python scripts/check_connector_reference_drift.py
./.venv/bin/python scripts/check_security_policy.py
PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_dependency_audit.py
./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
npm --prefix website ci
npm --prefix website run build
```

## Key Outcomes

- Docs build: pass
- OpenAPI drift gate: pass
- Connector reference drift gate (new default path): pass
- Scenario eval pass rate: `100.0%` (critical `100.0%`)
- Dependency audit: `No known vulnerabilities found`
