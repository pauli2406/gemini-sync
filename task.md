# Task

- Task ID: rename-ingestrelay-hard-cutover
- Title: Hard-cutover rename from gemini-sync to IngestRelay
- Owner Role: planner
- Risk Tier: tier_3

## Intent

Execute a full hard-cutover rename to `IngestRelay` across runtime branding, package/CLI identity, infra chart pathing, docs/site references, and operational defaults while keeping Python module path `gemini_sync_bridge` unchanged.

## Acceptance Criteria

1. Package and CLI identity are renamed to `ingest-relay` in `pyproject.toml`.
2. User-facing runtime/API/docs/UI branding is renamed to `IngestRelay`.
3. Helm chart path and template identifiers move from `infra/helm/gemini-sync-bridge` to `infra/helm/ingest-relay` and runtime references are updated.
4. Operational defaults/examples use `ingest_relay`/`ingest-relay` (DB names, namespaces, image repo, sample buckets).
5. Docs/site/github links/command examples are updated to `ingest-relay` and `pauli2406/ingest-relay`.
6. New rename eval scenario is registered and passing.
7. Required local gates pass and required handoff artifacts are updated.

## Specialist Role Mapping

1. Planner Agent
   - Defined cutover scope, canonical rename map, and acceptance criteria.
2. Implementer Agent
   - Applied code/config/infra/docs/site renames and moved Helm chart directory.
3. Test/Eval Agent
   - Performed failing-first test updates, added `tests/test_project_identity.py`, added `evals/scenarios/ingest-relay-branding-contract.yaml`, and validated green gates.
4. Docs Agent
   - Updated README/docs/website content and docs consistency tokens.
5. Security Agent
   - Ran security policy checks and dependency audit; fixed audit transition exclusion.
6. Release Agent
   - Classified as Tier 3, validated full gate outcomes, and documented merge/rollback constraints.
