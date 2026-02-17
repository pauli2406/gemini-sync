# Connector Authoring Guide

This page is the entry point for creating and operating connector profiles.

## Start Here

Choose your mode first:

- SQL Pull: `docs/connector-mode-sql-pull.md`
- REST Pull: `docs/connector-mode-rest-pull.md`
- REST Push: `docs/connector-mode-rest-push.md`

Then select provider specifics:

- Postgres: `docs/connector-provider-postgres.md`
- MySQL: `docs/connector-provider-mysql.md`
- MSSQL: `docs/connector-provider-mssql.md`
- Oracle: `docs/connector-provider-oracle.md`
- HTTP: `docs/connector-provider-http.md`
- Future placeholders: `docs/connector-provider-future.md`

Complete schema-level field details:

- Generated field reference: `docs/connector-field-reference.md`

## Required Baseline Structure

Every connector in `connectors/*.yaml` must include:

- `apiVersion: sync.gemini.io/v1alpha1`
- `kind: Connector`
- `metadata.name`
- `spec.mode`
- `spec.source`
- `spec.mapping`
- `spec.output`
- `spec.gemini`
- `spec.reconciliation`

## Mode quick decision

| Need | Recommended mode |
|---|---|
| Poll relational DB with SQL | `sql_pull` |
| Poll HTTP API on schedule | `rest_pull` |
| Receive pushed canonical docs | `rest_push` |

## Reconciliation safety rule

- Snapshot extraction + `auto_delete_missing`: use when you want stale docs deleted.
- Incremental extraction + `auto_delete_missing`: avoid (can cause false deletes).
- Incremental extraction + `soft_delete_only` or `never_delete`: safer baseline.

## Secret resolution model

`spec.source.secretRef` maps to:

- Environment variable: `SECRET_<UPPERCASED_SECRETREF>`
- Managed secret store (if configured)

Example:

- `secretRef: hr-db-credentials`
- `SECRET_HR_DB_CREDENTIALS=...`

## Validation and quality gates

Run before commit:

```bash
python scripts/validate_connectors.py
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
python scripts/check_connector_reference_drift.py
```

## Working examples in repo

- `connectors/hr-employees.yaml` (`sql_pull`)
- `connectors/kb-rest.yaml` (`rest_pull`)
- `connectors/support-push.yaml` (`rest_push`)
