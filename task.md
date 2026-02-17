# Task

- Task ID: rest-pull-oauth-s2s
- Title: Add OAuth client-credentials (Keycloak-style S2S) support to `rest_pull`
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Support internal APIs that require service-to-service OAuth token acquisition and refresh for `rest_pull`, while preserving existing static bearer-token behavior.

## Acceptance Criteria

1. Connector contract supports optional `spec.source.oauth` for `rest_pull` with:
   - `grantType=client_credentials`
   - `tokenUrl`
   - `clientId`
   - optional `clientSecretRef`, `scopes`, `audience`
   - `clientAuthMethod` in `client_secret_post|client_secret_basic`
2. Runtime `rest_pull` supports:
   - token acquisition via OAuth client credentials
   - proactive token refresh near expiry
   - single forced refresh retry on first 401
   - clear extraction errors for invalid token endpoint responses
3. OAuth mode overrides manual `Authorization` header with runtime token.
4. Existing static bearer `rest_pull` behavior remains backward compatible.
5. Studio wizard supports configuring static bearer vs OAuth client credentials.
6. Mode switch pruning removes `source.oauth` for `sql_pull` and `rest_push`.
7. Tests and scenario eval coverage are updated.
8. Mapped docs and generated connector field reference are updated.

## Specialist Role Mapping

1. Planner Agent
   - Locked contract, defaults, acceptance criteria, and risk tier.
2. Implementer Agent
   - Updated runtime extractor, schema model/schema JSON, and Studio UI/proposal pruning.
3. Test/Eval Agent
   - Added OAuth runtime tests, Studio/schema tests, and scenario eval entry.
4. Docs Agent
   - Updated README, architecture, REST pull mode/provider docs, troubleshooting, docs meta, and generated field reference.
5. Security Agent
   - Verified secret handling behavior and security policy/dependency checks.
6. Release Agent
   - Defined canary and rollback guidance in risk tier artifact.

## Scope

- In scope: `rest_pull` OAuth client credentials only.
- Out of scope: ingress endpoint auth hardening, non-client-credentials grants, connector-level proxy contract.
