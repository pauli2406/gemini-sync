# Risk Tier

- Assigned Tier: `tier_2`
- Rationale:
  - `scripts/**` changed (new CI governance gate script).
  - CI policy behavior changed via `.github/workflows/ci.yaml`.
  - No runtime API/schema contract changes.

## Required Gates and Outcomes

- Connector schema validation: pass
- Connector examples allowlist drift gate: pass
- Connector examples-only guard: pass
- Lint (`ruff`): pass
- TDD/EDD guardrail: pass
- Docs drift: pass (explicit changed-file invocation)
- OpenAPI drift gate: pass
- Connector reference drift gate: pass
- Security policy check: pass
- Dependency audit: pass
- Tests + coverage: pass (`169 passed`, coverage `85.32%`)
- Diff coverage: pass
- Scenario eval suite: pass (`100%`, critical `100%`)
- Docs site build: pass

## Merge Policy

- Tier 2 requires reviewer bot + one human reviewer.

## Rollout Plan

1. Merge and monitor CI for allowlist drift gate behavior on connector sample updates.
2. Share `docs/start-here.md` + migration checklist with staging operators.
3. Use migration checklist for the next staging cutover touching connector storage.

## Rollback Plan

1. Revert the allowlist drift script + CI step if it blocks legitimate workflows unexpectedly.
2. Keep existing `check_connector_examples_only.py` guard as minimum baseline.
3. Restore previous docs/sidebar structure if needed (docs-only rollback).
