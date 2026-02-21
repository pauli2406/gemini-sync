# Changes

## Files Changed

- Identity and runtime branding:
  - `pyproject.toml`
  - `gemini_sync_bridge/cli.py`
  - `gemini_sync_bridge/__init__.py`
  - `gemini_sync_bridge/api.py`
  - `gemini_sync_bridge/services/pipeline.py`
  - `gemini_sync_bridge/services/observability.py`
  - `gemini_sync_bridge/templates/ops/dashboard.html`
- Helm/infra migration:
  - moved `infra/helm/gemini-sync-bridge/**` -> `infra/helm/ingest-relay/**`
  - `gemini_sync_bridge/services/studio.py`
  - `infra/k8s/kestra-postgres.yaml`
  - `docker-compose.yml`
  - `.env.example`
  - `gemini_sync_bridge/settings.py`
- Docs/site/repo references:
  - `README.md`, `AGENTS.md`, `llm.txt`, `CONTRIBUTING.md`
  - `docs/**` (commands, branding, examples, links)
  - `website/docusaurus.config.ts`, `website/src/pages/index.tsx`
  - `schemas/connector.schema.json`, `schemas/agent-task.schema.json`
  - regenerated `website/static/openapi.json`
  - regenerated `docs/reference/connector-fields.md`
- Connector examples and tests:
  - `connectors/*.yaml`, `schemas/connector.docs-meta.yaml`
  - `tests/test_openapi_scripts.py`
  - `tests/test_github_pr_service.py`
  - `tests/test_outbound_proxy_support.py`
  - `tests/test_studio_proposal_generation.py`
  - `tests/test_publisher.py`
  - added `tests/test_project_identity.py`
  - updated `tests/test_connector_reference_scripts.py`
- Eval and gate updates:
  - added `evals/scenarios/ingest-relay-branding-contract.yaml`
  - updated `evals/eval_registry.yaml`
  - updated `scripts/run_dependency_audit.py`
  - updated `scripts/export_connector_reference.py` (MDX-safe escaping)

## Behavior Changes

- CLI command name changes from `gemini-sync-bridge` to `ingest-relay`.
- Python distribution name changes from `gemini-sync-bridge` to `ingest-relay`.
- API/OpenAPI title changes to `IngestRelay`.
- Splunk source tag changes to `ingest-relay`.
- Studio proposal changes target `infra/helm/ingest-relay/values.yaml`.
- Operational defaults use `ingest_relay` DB identifiers and `ingest-relay` namespaces/slugs.

## Non-Functional Changes

- Full docs/site hard-cutover to `IngestRelay` naming and new GitHub slug `pauli2406/ingest-relay`.
- Added regression test coverage for project identity and connector-reference escaping.
- Preserved module/import path `gemini_sync_bridge` as an intentional compatibility boundary.
