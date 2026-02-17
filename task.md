# Task

- Task ID: outbound-proxy-env-support
- Title: Enforce env-driven proxy support for all outbound HTTP egress
- Owner Role: planner
- Risk Tier: tier_2

## Intent

Make outbound HTTP routing explicitly honor standard environment variables for proxy and CA trust across runtime and studio egress paths, without changing connector schema or public API.

## Acceptance Criteria

1. REST pull + OAuth token requests use an explicitly env-trusting HTTP client factory.
2. Splunk and Teams webhook delivery use the same env-trusting HTTP client factory.
3. GitHub PR proposal API calls use the same env-trusting HTTP client factory.
4. Gemini ingestion `AuthorizedSession` explicitly enables `trust_env`.
5. Proxy contract is documented via `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`.
6. Connector/API schema remains unchanged.
7. New proxy regression tests and scenario eval are added and passing.

## Specialist Role Mapping

1. Planner Agent
   - Finalized scope, constraints, acceptance criteria, and risk tier.
2. Implementer Agent
   - Added shared HTTP client helper and wired outbound call sites.
3. Test/Eval Agent
   - Added failing-first proxy regression tests and eval scenario registration.
4. Docs Agent
   - Updated env sample, README, operations runbook, provider HTTP doc, and troubleshooting.
5. Security Agent
   - Validated standard CA/proxy env contract and policy/audit gates.
6. Release Agent
   - Captured rollout/rollback guidance and gate outcomes in risk artifact.

## Scope

- In scope:
  - Env-driven proxy support for outbound HTTP egress.
  - Custom CA env documentation (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`).
- Out of scope:
  - Per-connector proxy overrides.
  - Advanced proxy auth (NTLM/Kerberos/PAC/mTLS proxy handshake).
