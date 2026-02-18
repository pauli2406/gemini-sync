# Risk Tier

- Assigned Tier: `tier_2`
- Rationale:
  - Runtime extraction, pipeline dispatch, and Studio authoring logic changed under `gemini_sync_bridge/**`.
  - Connector/schema/eval/docs updates are substantial but do not modify critical infra/release workflows.
- Required Gates:
  - connector validation
  - lint
  - TDD/EDD guardrail
  - docs drift + docs consistency
  - security policy conformance
  - dependency vulnerability audit
  - pytest + coverage + diff coverage
  - scenario eval suite
- Merge Constraints:
  - reviewer bot required
  - at least one human reviewer required
  - no auto-merge without tier policy requirements satisfied

## Gate Outcomes

- `python scripts/validate_connectors.py` -> pass
- `ruff check .` -> pass
- `python scripts/check_tdd_guardrails.py` -> pass
- `python scripts/check_docs_drift.py` -> pass
- `python scripts/check_security_policy.py` -> pass
- `python scripts/run_dependency_audit.py` -> pass (`No known vulnerabilities found`)
- `pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60` -> pass
- `diff-cover coverage.xml --compare-branch=origin/main --fail-under=92` -> pass (`100%`)
- `python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json` -> pass (`100%`, critical `100%`)

## Rollout Plan

1. Deploy to staging with file source paths mounted.
2. Run one `file_pull` connector in `row` mode and verify checkpoint + artifacts.
3. Run one `file_pull` connector in `file` mode and verify synthetic template fields.
4. Verify existing `sql_pull`, `rest_pull`, and `rest_push` canary connectors remain healthy.

## Rollback Plan

1. Disable or pause new `file_pull` schedules.
2. Revert runtime/schema/studio changes in one rollback PR.
3. Re-run canary connectors and scenario evals to confirm baseline behavior.
