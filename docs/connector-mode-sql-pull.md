# SQL Pull Connector Mode

## When to use this mode

Use `sql_pull` when your source is a relational database and you want the bridge to run SQL on a schedule.

Best fit:

- Source is PostgreSQL/MySQL/MSSQL.
- You want centralized scheduling and retries.
- You need deterministic reconciliation behavior.

## Minimal YAML (copy/paste)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: hr-employees
spec:
  mode: sql_pull
  schedule: "0 */3 * * *"
  source:
    type: postgres
    secretRef: hr-db-credentials
    query: >
      SELECT employee_id, full_name, updated_at
      FROM employees
    watermarkField: updated_at
  mapping:
    idField: employee_id
    titleField: full_name
    contentTemplate: "{{ full_name }}"
  output:
    bucket: gs://company-gemini-sync
    prefix: hr-employees
    format: ndjson
  gemini:
    projectId: my-project
    location: eu
    dataStoreId: hr-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Full YAML (annotated)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: hr-employees
spec:
  mode: sql_pull
  schedule: "0 */3 * * *" # required for pull modes
  source:
    type: postgres # postgres | mysql | mssql
    secretRef: hr-db-credentials # SECRET_HR_DB_CREDENTIALS
    query: >
      SELECT employee_id, full_name, department, role, bio, allowed_users, allowed_groups, updated_at
      FROM employees
    watermarkField: updated_at # max value is stored as checkpoint
  mapping:
    idField: employee_id
    titleField: full_name
    contentTemplate: "{{ department }} {{ role }} {{ bio }}"
    uriTemplate: "https://hr.internal/employees/{{ employee_id }}"
    mimeType: text/plain
    aclUsersField: allowed_users
    aclGroupsField: allowed_groups
    metadataFields:
      - department
      - role
  output:
    bucket: gs://company-gemini-sync # or file://./local-bucket for local dev
    prefix: hr-employees
    format: ndjson
  gemini:
    projectId: my-project
    location: eu
    dataStoreId: hr-ds
  reconciliation:
    deletePolicy: auto_delete_missing # auto_delete_missing | soft_delete_only | never_delete
```

## Field-by-field explanation

| Field | Meaning | Options |
|---|---|---|
| `spec.schedule` | Cron schedule for extraction. | Any valid cron string. |
| `spec.source.type` | SQL provider adapter. | `postgres`, `mysql`, `mssql` |
| `spec.source.secretRef` | Database DSN secret reference. | Any non-empty string; runtime resolves `SECRET_<SECRETREF>`. |
| `spec.source.query` | SQL executed each run. | Any SQL valid for your DB. |
| `spec.source.watermarkField` | Field used to compute checkpoint watermark from result rows. | Typically timestamp field like `updated_at`. |
| `spec.mapping.*` | Maps source rows into canonical documents. | Required: `idField`, `titleField`, `contentTemplate`; optional URI/ACL/metadata fields. |
| `spec.reconciliation.deletePolicy` | Delete handling strategy. | `auto_delete_missing`, `soft_delete_only`, `never_delete` |

## Mode-specific decision matrix

| Query style | `deletePolicy` | Use? | Why |
|---|---|---|---|
| Snapshot query (full dataset each run) | `auto_delete_missing` | Yes (recommended) | Bridge can safely detect stale records and delete them. |
| Incremental query (`WHERE updated_at > :watermark`) | `auto_delete_missing` | No | Missing rows are interpreted as deletes and can cause data loss. |
| Incremental query | `soft_delete_only` | Yes | No hard delete of missing records. |
| Incremental query | `never_delete` | Yes | Pure upsert behavior. |

## Validation checklist

1. `spec.schedule` is set.
2. `spec.source.query` returns `idField`, `titleField`, and `watermarkField` (if set).
3. `spec.source.secretRef` is configured as environment variable or managed secret.
4. `deletePolicy` is aligned to query strategy (snapshot vs incremental).
5. Run `python scripts/validate_connectors.py`.

## Common failures and fixes

- `Missing secret for '...'. Expected environment variable SECRET_...`
  - Set `SECRET_<SECRETREF>` or add a managed secret.
- `relation "..." does not exist`
  - Fix table/schema name in `source.query`.
- `Missing id/title field ... in source record`
  - Ensure query selects mapping fields.
- `upserts=0,deletes>0` unexpectedly
  - You likely used incremental query with `auto_delete_missing`; switch to snapshot query or non-destructive delete policy.

## Provider notes and links

- Postgres: `docs/connector-provider-postgres.md`
- MySQL: `docs/connector-provider-mysql.md`
- MSSQL: `docs/connector-provider-mssql.md`
- Full field table: `docs/connector-field-reference.md`
