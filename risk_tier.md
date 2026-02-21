# Risk Tier

- Assigned Tier: `tier_0`
- Rationale:
  - Change scope is documentation only (remove one how-to page and clean links/index entries).
  - No runtime code, API, deployment config, or security policy behavior changed.
  - Validation focused on docs consistency and successful docs site build.

## Required Gates

- Docs link/reference cleanup check
- Docs drift check
- Docs site build

## Merge Constraints

- Tier 0 may be auto-merged after required docs gates pass.

## Rollout / Rollback

1. Merge after docs checks pass.
2. If any doc route regression appears, restore by reverting this commit or re-adding the removed page and links.
