# Risk Tier

- Assigned Tier: `tier_2`
- Rationale:
  - Runtime/API operational behavior changed in `gemini_sync_bridge/**` via connector discovery path resolution.
  - New governance script in `scripts/**` enforced in CI.

## Gate Outcomes

- Connector schema validation: pass
- Connector examples-only guard: pass
- Lint (`ruff`): pass
- TDD/EDD guardrail: pass
- Docs drift: pass when evaluated with explicit changed files in current uncommitted local state
- OpenAPI drift gate: pass
- Connector reference drift gate: pass
- Security policy check: pass
- Dependency audit: pass
- Tests + coverage: pass
- Diff coverage: pass
- Scenario eval suite: pass (`100%`, critical `100%`)
- Docs site build: pass

## Merge Policy

- Tier 2 requires reviewer bot + one human reviewer.

## Rollout Plan

1. In staging, set `CONNECTORS_DIR` to external connector repo checkout path.
2. Validate:
   - one API/Ops/Studio connector discovery flow,
   - one manual run and one Studio proposal path.
3. Enable connector examples-only CI guard in standard PR checks.

## Rollback Plan

1. Unset `CONNECTORS_DIR` to return to default repo-local discovery.
2. Revert this commit if discovery or CI guard behavior causes regressions.
3. Re-run smoke tests for manual run, ops catalog, and studio propose endpoints.
