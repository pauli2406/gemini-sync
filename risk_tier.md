# Risk Tier

- Assigned Tier: tier_2
- Rationale:
  - Runtime behavior changed in `gemini_sync_bridge/adapters/extractors.py`.
  - Public connector contract changed in `schemas/connector.schema.json` and `gemini_sync_bridge/schemas.py`.
  - Studio authoring/proposal behavior changed for source auth.

## Required Gates and Outcomes

- Connector schema validation: pass
- Lint (`ruff`): pass
- Tests + coverage: pass (`106 passed`, coverage `80.87%`)
- TDD/EDD guardrail: pass
- Connector field reference drift gate: pass
- OpenAPI drift gate: pass
- Security policy check: pass
- Dependency audit: pass (after PATH correction)
- Scenario eval suite: pass (`100%`, critical `100%`)

## Docs Drift Gate Note

- Default `check_docs_drift.py` invocation failed in current local state because changed-file detection considered untracked eval files without matching tracked doc files from base-ref comparison.
- Verified rule compliance with explicit changed-file invocation including updated mapped docs.

## Release/Canary Plan

1. Canary one `rest_pull` connector with `source.oauth` enabled.
2. Monitor:
   - run failure rate
   - source API 401 rate
   - OAuth token endpoint 4xx/5xx errors
3. Keep all other connectors on static bearer mode during canary.

## Rollback Plan

1. Remove `spec.source.oauth` block from canary connector.
2. Revert to static bearer (`spec.source.secretRef` token).
3. Re-run connector validation and redeploy.
4. If needed, revert commit containing OAuth runtime changes.

## Merge Policy

- Tier 2 requires reviewer bot + one human reviewer.
- Tier 3 restrictions do not apply.
