## Summary

## Changes

- 

## TDD / EDD Evidence

- [ ] Failing test evidence before implementation is included.
- [ ] Failing scenario eval evidence before implementation is included.
- [ ] New or updated tests were added for behavior changes.
- [ ] New or updated scenario evals were added for behavior changes.

## Validation

- [ ] `python scripts/validate_connectors.py`
- [ ] `ruff check .`
- [ ] `python scripts/check_tdd_guardrails.py`
- [ ] `python scripts/check_docs_drift.py`
- [ ] `python scripts/check_security_policy.py`
- [ ] `python scripts/run_dependency_audit.py`
- [ ] `pytest --cov=ingest_relay --cov-report=xml --cov-fail-under=60`
- [ ] `diff-cover coverage.xml --compare-branch=origin/main --fail-under=92`
- [ ] `python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json`

## Docs Evidence

- [ ] `README.md` updated when public behavior or commands changed.
- [ ] Mapped docs updated per `docs/doc_sync_map.yaml`.
- [ ] `docs/roadmap.md` evaluated/updated for Tier 1+ changes.

## Operational Impact

- [ ] Requires connector schema change
- [ ] Requires new env vars/secrets
- [ ] Requires migration/backfill
- [ ] Risk tier documented (`tier_0`/`tier_1`/`tier_2`/`tier_3`)
