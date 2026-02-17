# Test Evidence

## Red Phase (Failing First)

- Command:
  - `./.venv/bin/pytest tests/test_extractors_rest_pull_oauth.py tests/test_studio_draft_validation.py tests/test_studio_ui.py tests/test_studio_proposal_generation.py -q`
- Result before implementation:
  - `11 failed, 13 passed`
- Failure categories observed:
  - OAuth token flow not implemented (`rest_pull` still static token only).
  - Studio wizard missing OAuth controls.
  - Draft/schema validation accepted invalid OAuth grant.
  - Mode-pruning did not handle `source.oauth`.

## Green Phase

- Targeted suite after implementation:
  - `./.venv/bin/pytest tests/test_extractors_rest_pull_oauth.py tests/test_connector_schema_oauth.py tests/test_studio_draft_validation.py tests/test_studio_ui.py tests/test_studio_proposal_generation.py -q`
  - Result: `26 passed`

- Full tests + coverage:
  - `./.venv/bin/pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60`
  - Result: `106 passed`, coverage `80.87%`

## Gate Commands

- `./.venv/bin/python scripts/validate_connectors.py`
  - pass (`All connector definitions are valid.`)
- `./.venv/bin/ruff check .`
  - pass
- `./.venv/bin/python scripts/check_tdd_guardrails.py`
  - pass
- `./.venv/bin/python scripts/check_docs_drift.py`
  - fail in current local branch state (script considered only untracked files from base-ref comparison and flagged missing docs for eval changes)
- `./.venv/bin/python scripts/check_docs_drift.py --changed-file evals/scenarios/rest-pull-oauth-client-credentials.yaml --changed-file README.md`
  - pass (rule trigger satisfied with mapped doc)
- `./.venv/bin/python scripts/check_connector_reference_drift.py`
  - pass
- `./.venv/bin/python scripts/check_openapi_drift.py`
  - pass
- `./.venv/bin/python scripts/check_security_policy.py`
  - pass
- `./.venv/bin/python scripts/run_dependency_audit.py`
  - initial fail (`pip` not found on PATH)
- `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_dependency_audit.py`
  - pass (`No known vulnerabilities found`)
- `PATH=.venv/bin:$PATH ./.venv/bin/python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`
  - pass (`pass_rate_percent=100`, `critical_pass_rate_percent=100`)
