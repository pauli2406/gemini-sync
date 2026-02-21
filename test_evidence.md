# Test Evidence

## Red Phase Evidence

- Tests were switched to `ingest_relay` imports before the package directory rename.
- Failing-first command:

```bash
./.venv/bin/pytest -q tests/test_project_identity.py tests/test_quality_gate_tdd.py tests/test_quality_gate_docs.py
```

- Expected failure observed:
  - `ModuleNotFoundError: No module named 'ingest_relay'` while loading `tests/conftest.py`.

## Green Phase Evidence

- After `git mv gemini_sync_bridge ingest_relay` and full import/path updates:

```bash
./.venv/bin/pytest -q tests/test_project_identity.py tests/test_quality_gate_tdd.py tests/test_quality_gate_docs.py
```

- Result: `11 passed`

- Full coverage run:

```bash
./.venv/bin/pytest --cov=ingest_relay --cov-report=xml --cov-fail-under=60
```

- Result: `194 passed`, total coverage `87.20%`

- Diff coverage:

```bash
./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
```

- Result: pass (`98%` diff coverage)

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
./.venv/bin/pytest --cov=ingest_relay --cov-report=xml --cov-fail-under=60
./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
npm --prefix website ci
npm --prefix website run build
```

## Key Outcomes

- Security policy: pass
- Dependency audit: `No known vulnerabilities found`
- Scenario eval registry: `22/22 passed`, critical pass rate `100%`
- Docs site build: pass
- Active-file `gemini_sync_bridge` refs: `0` (excluding intentional `.agent/tasks/*` history)
