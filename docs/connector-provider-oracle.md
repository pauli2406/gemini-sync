# Provider: Oracle Database

## Supported status

Supported in current runtime.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: oracle
```

## Secret DSN format

Use SQLAlchemy DSN format with `python-oracledb` thin mode.

Service name form:

```text
oracle+oracledb://<user>:<password>@<host>:<port>/?service_name=<service_name>
```

SID form:

```text
oracle+oracledb://<user>:<password>@<host>:<port>/?sid=<sid>
```

## Environment variable mapping

If connector has:

```yaml
secretRef: oracle-hr-credentials
```

Set:

```bash
export SECRET_ORACLE_HR_CREDENTIALS='oracle+oracledb://hr_user:secret@oracle.internal:1521/?service_name=ORCLPDB1'
```

## YAML snippets

```yaml
source:
  type: oracle
  secretRef: oracle-hr-credentials
  query: >
    SELECT employee_id, full_name, updated_at
    FROM hr.employees
  watermarkField: updated_at
```

## Mode compatibility

- `sql_pull`: supported and primary use case.
- `rest_pull`: not applicable.
- `rest_push`: not applicable.
- `file_pull`: not applicable.

## Common connection errors and fixes

- `DPY-6005` or connection timeout errors
  - Verify host/port/service name (or SID) and network routing from runtime.
- `ORA-01017: invalid username/password`
  - Verify credentials in DSN secret.
- `ORA-00942: table or view does not exist`
  - Use correct schema-qualified table names (for example `hr.employees`) and grants.
