# Docs Evidence

## Updated Docs

- New:
  - `docs/connector-mode-file-pull.md`
  - `docs/connector-provider-file.md`
- Updated:
  - `README.md`
  - `docs/connector-authoring.md`
  - `docs/connector-studio.md`
  - `docs/architecture.md`
  - `docs/discovery-engine-cli-playbook.md`
  - `docs/connector-provider-http.md`
  - `docs/connector-provider-postgres.md`
  - `docs/connector-provider-mysql.md`
  - `docs/connector-provider-mssql.md`
  - `docs/connector-provider-oracle.md`
  - `docs/connector-provider-future.md`
  - `docs/roadmap.md`
  - `website/sidebars.ts`
  - `schemas/connector.docs-meta.yaml`
  - `docs/connector-field-reference.md` (regenerated)

## Why These Docs Were Required

- Runtime contract changed under `gemini_sync_bridge/**` and `schemas/**`:
  - required `runtime_and_api` and `connector_contract` docs coverage.
- Connector/eval updates changed `connectors/**` and `evals/**`:
  - required contract/governance docs coverage.
- Website sidebar changed under `website/**`:
  - required docs-site navigation sync.

## Key Documentation Outcomes

- Added complete authoring guidance for `file_pull` mode and `file` provider.
- Documented CSV `documentMode=row|file` behavior and synthetic mapping fields.
- Documented compact checkpoint format (`v/rw/fc/lm/fh`) and compatibility behavior.
- Updated connector hub/navigation to include new mode/provider pages.
- Kept generated connector field reference aligned with schema/docs-meta changes.
