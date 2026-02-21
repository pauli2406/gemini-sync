# Test Evidence

## Red Phase Evidence

- Failing-first subset executed before production renames:

```bash
./.venv/bin/pytest -q tests/test_openapi_scripts.py::test_export_openapi_writes_expected_file tests/test_github_pr_service.py::test_create_proposal_result_uses_repo_when_present tests/test_studio_proposal_generation.py::test_build_proposed_file_changes_for_create_and_pause_resume tests/test_project_identity.py
```

- Result: expected failures proving missing implementation:
  - OpenAPI title mismatch (`Gemini Sync Bridge` vs `IngestRelay`)
  - Studio Helm values path mismatch (`infra/helm/gemini-sync-bridge/values.yaml`)
  - Pyproject package/script identity mismatch
  - Splunk source mismatch (`gemini-sync-bridge` vs `ingest-relay`)

## Green Phase Evidence

- Focused rename subset:

```bash
./.venv/bin/pytest -q tests/test_openapi_scripts.py::test_export_openapi_writes_expected_file tests/test_github_pr_service.py::test_create_proposal_result_uses_repo_when_present tests/test_studio_proposal_generation.py::test_build_proposed_file_changes_for_create_and_pause_resume tests/test_project_identity.py
```

- Result: `5 passed`

- Connector reference regression coverage:

```bash
./.venv/bin/pytest -q tests/test_connector_reference_scripts.py
```

- Result: `5 passed`

- Full test + coverage gate:

```bash
./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
```

- Result: `194 passed`, coverage `87.20%`

- Diff coverage gate:

```bash
./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
```

- Result: pass (`100%` diff coverage)

## Commands

```bash
./.venv/bin/python scripts/validate_connectors.py
./.venv/bin/python scripts/check_connector_examples_allowlist_drift.py
./.venv/bin/python scripts/check_connector_examples_only.py
./.venv/bin/ruff check .
./.venv/bin/python scripts/check_openapi_drift.py
./.venv/bin/python scripts/check_connector_reference_drift.py
./.venv/bin/python scripts/check_security_policy.py
PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_dependency_audit.py

# Local working-tree mode for drift guards (explicit changed-file args)
./.venv/bin/python scripts/check_tdd_guardrails.py --changed-file <...>
./.venv/bin/python scripts/check_docs_drift.py --changed-file <...>

./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
./.venv/bin/diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
npm --prefix website ci
npm --prefix website run build
```

## Key Outcomes

- Security policy: pass
- Dependency audit: `No known vulnerabilities found`
- Scenario eval registry: `22/22 passed`, critical pass rate `100%`
- Docs build: pass
