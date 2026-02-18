# Connector Studio

Connector Studio is the guided UI for creating and managing connection profiles without hand-editing YAML.

## Access

- UI list: `/studio/connectors`
- New profile wizard: `/studio/connectors/new`
- APIs: `/v1/studio/*`

## What It Does

- Create, edit, clone, pause, resume, delete, and run connectors.
- Validate drafts against connector schema before proposing.
- Preview mapped document output from sample records.
- Propose GitHub pull requests instead of writing directly to `main`.
- Keep proposed connector file paths under `connectors/<connector-id>.yaml` for config repo consistency.
- Manage schedule state via Helm `scheduleJobs.enabled`.

## Required Configuration

Set these for GitHub PR automation:

- `GITHUB_TOKEN`
- `GITHUB_REPO` (target connector-config repo, for example `org/connector-config-repo`)
- `GITHUB_BASE_BRANCH` (default `main`)

Set this to discover connectors outside this repo:

- `CONNECTORS_DIR` (for example `/srv/gemini-sync/connectors`)

Set this for managed secrets:

- `MANAGED_SECRET_ENCRYPTION_KEY`

## Recommended Workflow

1. Open `/studio/connectors/new`.
2. Complete the wizard (source, mapping, target, schedule).
   - `sql_pull` exposes SQL query + watermark controls.
   - `rest_pull` exposes URL/method/payload/pagination/headers controls.
   - `rest_push` narrows source controls to push-compatible settings.
   - `file_pull` exposes local path/glob + CSV parser controls (`row`/`file` document mode).
   - For SQL connectors, ensure selected query columns line up with mapping fields/templates (`idField`, `titleField`, `contentTemplate`, optional URI/ACL/metadata fields).
3. Run `Validate` and `Preview`.
4. Click `Create PR Proposal`.
5. Review and merge the PR.
6. Trigger run now from Studio or run via CLI/orchestrator.

## Mode and Provider Guides

Use these pages while filling wizard fields:

- SQL Pull mode: `docs/connector-mode-sql-pull.md`
- REST Pull mode: `docs/connector-mode-rest-pull.md`
- REST Push mode: `docs/connector-mode-rest-push.md`
- Postgres provider: `docs/connector-provider-postgres.md`
- MySQL provider: `docs/connector-provider-mysql.md`
- MSSQL provider: `docs/connector-provider-mssql.md`
- Oracle provider: `docs/connector-provider-oracle.md`
- HTTP provider: `docs/connector-provider-http.md`
- File provider: `docs/connector-provider-file.md`
- Full field reference: `docs/connector-field-reference.md`

## Notes

- v1 write paths intentionally have no auth; deploy in a trusted private network segment.
- Existing manual YAML workflows remain supported.
- Migration path for legacy staging setups is documented in `docs/migration-custom-connectors.md`.
