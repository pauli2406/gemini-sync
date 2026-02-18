# Risk Tier

- Assigned Tier: `tier_2`
- Rationale:
  - `scripts/**` changed (reference export/check defaults).
  - `website/**` changed (navigation + docs homepage behavior).
  - No runtime API contract changes in `gemini_sync_bridge/**`.

## Required Gates

- Connector schema validation
- Connector example allowlist + examples-only guards
- Lint
- TDD/EDD guardrail
- Docs drift + consistency
- OpenAPI drift gate
- Connector reference drift gate
- Tests + coverage + diff coverage
- Security policy + secret scan + dependency audit
- Scenario eval thresholds
- Docs site build

## Merge Constraints

- Tier 2 requires reviewer bot + one human reviewer.

## Rollout / Rollback

1. Merge with full green gate set.
2. Verify docs build/deploy parity.
3. Roll back by reverting the docs-cutover commit if unexpected regressions are found.
