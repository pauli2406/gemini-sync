# Provider: MySQL

## Supported status

Supported in current runtime.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: mysql
```

## Secret DSN format

Use SQLAlchemy DSN format:

```text
mysql+pymysql://<user>:<password>@<host>:<port>/<database>
```

## Environment variable mapping

If connector has:

```yaml
secretRef: erp-mysql-credentials
```

Set:

```bash
export SECRET_ERP_MYSQL_CREDENTIALS='mysql+pymysql://user:pass@mysql.internal:3306/erp'
```

## YAML snippets

```yaml
source:
  type: mysql
  secretRef: erp-mysql-credentials
  query: >
    SELECT id, title, updated_at
    FROM knowledge_articles
  watermarkField: updated_at
```

## Mode compatibility

- `sql_pull`: supported and primary use case.
- `rest_pull`: not applicable.
- `rest_push`: not applicable.

## Common connection errors and fixes

- `Unknown MySQL server host`
  - Validate DNS/network routing from runtime.
- `Access denied for user`
  - Verify grants for host/user/database.
- SQL syntax issues
  - Validate query compatibility for your MySQL version.
