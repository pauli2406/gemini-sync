# Provider: Microsoft SQL Server

## Supported status

Supported in current runtime.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: mssql
```

## Secret DSN format

Use SQLAlchemy DSN format:

```text
mssql+pymssql://<user>:<password>@<host>:<port>/<database>
```

## Environment variable mapping

If connector has:

```yaml
secretRef: finance-mssql-credentials
```

Set:

```bash
export SECRET_FINANCE_MSSQL_CREDENTIALS='mssql+pymssql://user:pass@sql.internal:1433/finance'
```

## YAML snippets

```yaml
source:
  type: mssql
  secretRef: finance-mssql-credentials
  query: >
    SELECT document_id, title, updated_at
    FROM dbo.documents
  watermarkField: updated_at
```

## Mode compatibility

- `sql_pull`: supported and primary use case.
- `rest_pull`: not applicable.
- `rest_push`: not applicable.
- `file_pull`: not applicable.

## Common connection errors and fixes

- Login timeout or network error
  - Check firewall rules and SQL Server TCP listener.
- `Login failed for user`
  - Confirm SQL auth mode and credentials.
- Schema/table resolution errors
  - Use fully-qualified names like `dbo.table_name`.
