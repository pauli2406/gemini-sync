# Start Here

Use this page to pick the right onboarding path quickly.

## Path 1: First-Time Local Setup

Use this if you are evaluating Gemini Sync Bridge or developing locally.

1. Follow `docs/getting-started-local.mdx`.
2. Validate local connector run success.
3. Open Ops and Studio UIs.

## Path 2: Migrate Existing Staging Deployment

Use this if your staging setup previously stored custom connectors in this runtime repo.

1. Follow `docs/migration-custom-connectors.md`.
2. Move custom connectors to external config repo/directory.
3. Set `CONNECTORS_DIR` and verify Studio/Ops/manual run behavior.

## Path 3: Build or Update Connectors

Use this when authoring connector definitions and PR proposals.

1. Start with `docs/connector-authoring.md`.
2. Choose a mode guide:
   - `docs/connector-mode-sql-pull.md`
   - `docs/connector-mode-rest-pull.md`
   - `docs/connector-mode-rest-push.md`
   - `docs/connector-mode-file-pull.md`
3. Use `docs/connector-studio.md` for guided authoring and PR workflows.

## Path 4: Operate and Troubleshoot

Use this for production operations, incident triage, and reliability checks.

1. `docs/operations-runbook.md`
2. `docs/troubleshooting.md`
3. `docs/reliability-phase.md`

## Minimum Pre-PR Gate Commands

```bash
python scripts/validate_connectors.py
python scripts/check_connector_examples_allowlist_drift.py
python scripts/check_connector_examples_only.py
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
ruff check .
pytest
```
