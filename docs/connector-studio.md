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
- Manage schedule state via Helm `scheduleJobs.enabled`.

## Required Configuration

Set these for GitHub PR automation:

- `GITHUB_TOKEN`
- `GITHUB_REPO` (for example `org/repo`)
- `GITHUB_BASE_BRANCH` (default `main`)

Set this for managed secrets:

- `MANAGED_SECRET_ENCRYPTION_KEY`

## Recommended Workflow

1. Open `/studio/connectors/new`.
2. Complete the wizard (source, mapping, target, schedule).
3. Run `Validate` and `Preview`.
4. Click `Create PR Proposal`.
5. Review and merge the PR.
6. Trigger run now from Studio or run via CLI/orchestrator.

## Notes

- v1 write paths intentionally have no auth; deploy in a trusted private network segment.
- Existing manual YAML workflows remain supported.
