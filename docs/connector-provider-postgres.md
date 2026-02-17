# Provider: PostgreSQL

## Supported status

Supported in current runtime.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: postgres
```

## Secret DSN format

Use SQLAlchemy DSN format:

```text
postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
```

## Environment variable mapping

If connector has:

```yaml
secretRef: hr-db-credentials
```

Set:

```bash
export SECRET_HR_DB_CREDENTIALS='postgresql+psycopg2://postgres:postgres@localhost:5432/gemini_sync_bridge'
```

## YAML snippets

```yaml
source:
  type: postgres
  secretRef: hr-db-credentials
  query: >
    SELECT employee_id, full_name, updated_at
    FROM employees
  watermarkField: updated_at
```

## Mode compatibility

- `sql_pull`: supported and primary use case.
- `rest_pull`: not applicable.
- `rest_push`: not applicable.

## Common connection errors and fixes

- `connection refused`
  - Verify host/port and DB service availability.
- `password authentication failed`
  - Verify username/password in DSN secret.
- `relation "..." does not exist`
  - Use fully-qualified table names or correct schema search path.
