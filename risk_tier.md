# Risk Tier

- Assigned Tier: `tier_3`
- Rationale:
  - Infrastructure-critical paths changed in `infra/**` (Helm chart directory rename, template identifier rename, values defaults, k8s namespace/db defaults).
  - Release-facing messaging changed in `.github/workflows/release-canary.yaml`.
  - Runtime/API/UI branding and operational defaults were changed repository-wide.

## Required Gates

- Connector schema validation
- Connector examples allowlist drift gate
- Examples-only connector change gate
- Lint (`ruff check .`)
- TDD/EDD guardrails
- Docs drift + consistency
- OpenAPI drift gate
- Connector reference drift gate
- Tests + coverage threshold
- Diff coverage threshold
- Security policy validation
- Dependency vulnerability audit
- Scenario eval thresholds
- Docs site build

## Merge Constraints

- Tier 3 is never auto-merge.
- Requires reviewer bot plus at least one human reviewer.
- Canary/release checks must be green before rollout.

## Rollout / Rollback

1. Merge only after all Tier 3 gates are green.
2. Validate canary signals and SLO gates before broad rollout.
3. Roll back by reverting this rename commit set if runtime, docs, or deployment naming regressions are detected.
