# Risk Tier

- Assigned Tier: `tier_3`
- Rationale:
  - `.agent/risk_policy.yaml` was modified (Tier 3 pattern includes `.agent/**`).
  - Full package namespace hard-cutover impacted runtime imports, scripts, tests, CI workflows, and policy mappings.
  - Existing branch already includes infrastructure/release-sensitive changes from stage 1.

## Required Gates

- Connector schema validation
- Connector examples allowlist + examples-only guards
- Lint (`ruff check .`)
- TDD/EDD guardrails
- Docs drift + consistency
- OpenAPI drift check
- Connector reference drift check
- Security policy check
- Dependency vulnerability audit
- Pytest coverage gate
- Diff coverage gate
- Scenario eval thresholds
- Docs site build

## Merge Constraints

- Tier 3 is never auto-merge.
- Requires reviewer bot + one human reviewer minimum.
- Release/canary checks must remain green.

## Rollout / Rollback

1. Merge only after full gate suite remains green.
2. Validate canary and SLO gates before wider rollout.
3. Roll back via revert if namespace/path regressions appear in runtime, workflows, or docs deployment.
