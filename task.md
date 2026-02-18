# Task

- Task ID: release-readiness-examples-and-docs-ux
- Title: Optimize core examples, guardrails, and docs UX for external users
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Make Gemini Sync Bridge ready for broader external usage by eliminating example/allowlist drift risk, tightening CI guardrails, and improving docs onboarding/navigation for local setup, migration, and operations.

## Acceptance Criteria

1. All core `connectors/*.yaml` samples are correctly represented in `connectors/examples-allowlist.txt`.
2. CI enforces allowlist drift prevention and examples-only change policy.
3. Tests cover allowlist drift gate pass/fail paths (missing, stale, invalid, duplicate).
4. Scenario eval coverage includes the allowlist drift gate.
5. Migration doc is command-driven with explicit preflight/verification/rollback checks.
6. Docs navigation provides a clear `Start Here` path and improved information architecture.
7. Docs mapping (`docs/doc_sync_map.yaml`) includes file mode/provider + migration/start-here pages where relevant.

## Specialist Role Mapping

1. Planner Agent
   - Locked release-readiness scope and success criteria.
2. Implementer Agent
   - Updated allowlist inventory and added strict drift-check script.
   - Wired CI and local command docs for the new gate.
3. Test/Eval Agent
   - Added allowlist drift unit tests and scenario eval registration.
4. Docs Agent
   - Added `docs/start-here.md`, improved docs IA/navigation, and tightened migration checklist.
5. Security Agent
   - Verified no secret handling regressions and passed security/dependency gates.
6. Release Agent
   - Captured gate outcomes and rollout/rollback plan in risk artifact.

## Scope

- In scope:
  - examples allowlist synchronization and enforcement
  - CI + test/eval hardening for examples policy
  - targeted docs UX overhaul and migration checklist quality
- Out of scope:
  - runtime API/schema behavior changes
  - connector contract changes
  - infra/workflow redesign beyond docs/CI quality gates
