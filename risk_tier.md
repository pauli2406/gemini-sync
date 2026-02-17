# Risk Tier

- Assigned Tier: `tier_2`
- Rationale:
  - Runtime outbound HTTP behavior changed in `gemini_sync_bridge/**`.
  - No infra/release workflow changes (`tier_3` not triggered).

## Required Approvals

- Reviewer bot: required
- Human reviewers: 1 required

## Gate Outcomes

- Connector validation: pass
- Ruff lint: pass
- TDD guardrail: pass
- Docs drift (explicit changed-file invocation): pass
- OpenAPI drift gate: pass
- Connector reference drift gate: pass
- Security policy conformance: pass
- Dependency audit: pass
- Scenario eval suite: pass (`100%`, critical `100%`)

## Rollout Plan

1. Enable proxy env vars in staging.
2. Verify one `rest_pull` static bearer run and one OAuth run.
3. Verify one Gemini ingestion run (`GEMINI_INGESTION_DRY_RUN=false` in staging).
4. Verify webhook delivery (Splunk/Teams) and one Studio GitHub PR proposal.

## Rollback Plan

1. Remove proxy/CA env vars from deployment if regressions are observed.
2. Re-run a canary connector to confirm recovery.
3. Revert commit if behavior remains unstable.
