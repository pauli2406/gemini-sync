# Docs Evidence

## Updated Docs

- `README.md`
- `AGENTS.md`
- `llm.txt`
- `CONTRIBUTING.md`
- `docs/doc_sync_map.yaml`
- `docs/concepts/architecture.mdx`
- `docs/concepts/connector-model.mdx`
- `docs/concepts/security-and-governance.mdx`
- `docs/contributing/contributing.mdx`
- `docs/contributing/dev-setup.mdx`
- `docs/how-to/connector-config-repo.mdx`
- `docs/how-to/connectors/rest-pull.mdx`
- `docs/how-to/connectors/rest-push.mdx`
- `docs/how-to/connectors/sql-pull.mdx`
- `docs/how-to/migrate-custom-connectors.mdx`
- `docs/how-to/operate-runs.mdx`
- `docs/reference/cli.mdx`
- `docs/reference/connector-fields.md`
- `docs/reference/splunk-dashboard-queries.mdx`
- `docs/roadmap.mdx`
- `docs/tutorials/gcp-onboarding.mdx`
- `docs/tutorials/getting-started-local.mdx`
- `website/docusaurus.config.ts`
- `website/src/pages/index.tsx`

## Why these docs were required

- `runtime_and_api` rule triggered (`gemini_sync_bridge/**`) and required mapped docs updates.
- `connector_contract` rule triggered (`connectors/**`, `schemas/**`) and required connector/how-to/reference docs updates.
- `orchestrator_and_deploy` rule triggered (`infra/**`, `Dockerfile`, `docker-compose.yml`) and required operations/tutorial docs updates.
- `governance_and_quality` rule triggered (`scripts/**`, `evals/**`, `AGENTS.md`) and required governance/contributing docs updates.
- `docs_site` rule triggered (`website/**`) and required docs consistency-aligned updates.
- Consistency tokens in `docs/doc_sync_map.yaml` were updated to `ingest-relay` CLI commands.
