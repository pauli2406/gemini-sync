# Task

- Task ID: clean-connector-flow
- Title: Keep user-specific connectors out of runtime repo with env-driven discovery and CI guardrails
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Prevent user-specific connector profiles from being committed into this runtime/tooling repository while preserving backward compatibility for existing deployments.

## Acceptance Criteria

1. API/Ops/Studio connector discovery is env-driven via `CONNECTORS_DIR`.
2. Default behavior remains unchanged when `CONNECTORS_DIR` is unset (`connectors/`).
3. Studio proposal payload paths remain `connectors/<connector-id>.yaml`.
4. CI fails if non-allowlisted files under `connectors/` are changed.
5. Repo tracks an explicit connector example allowlist.
6. Docs clarify external connector storage and `GITHUB_REPO` usage as connector-config target.
7. Tests and eval coverage are updated.

## Specialist Role Mapping

1. Planner Agent
   - Locked scope, compatibility constraints, and acceptance criteria.
2. Implementer Agent
   - Added shared connector path helper and wired API/Ops/Studio discovery to env-driven config.
   - Added connector example guard script and CI integration.
3. Test/Eval Agent
   - Added failing-first tests for `CONNECTORS_DIR` discovery and connector guard script.
   - Added scenario eval for external connector directory support.
4. Docs Agent
   - Updated README, operations runbook, connector authoring/studio docs, local getting-started note, migration guide, and `.env.example`.
5. Security Agent
   - Verified no secret exposure changes and ran policy/audit checks.
6. Release Agent
   - Documented tier, gates, rollout/rollback posture in risk artifact.

## Scope

- In scope: API/Ops/Studio connector discovery, docs contract updates, CI guardrail.
- Out of scope: connector schema changes, per-connector storage overrides, runtime CLI interface changes.
