# Provider: Local File Storage

## Supported status

Supported in current runtime for `file_pull` mode.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: file
```

## File source requirements

- `spec.source.path`: local directory path.
- `spec.source.glob`: non-recursive glob pattern under `path`.
- `spec.source.format`: `csv`.
- `spec.source.csv`: parser controls.

## YAML snippets

### CSV row mode

```yaml
source:
  type: file
  path: ./runtime/sources/hr
  glob: "*.csv"
  format: csv
  watermarkField: updated_at
  csv:
    documentMode: row
    delimiter: ","
    hasHeader: true
    encoding: utf-8
```

### CSV file mode

```yaml
source:
  type: file
  path: ./runtime/sources/hr
  glob: "*.csv"
  format: csv
  csv:
    documentMode: file
    delimiter: ","
    hasHeader: true
    encoding: utf-8
```

## Secret handling

- `source.secretRef` is optional for `file_pull`.
- Keep using managed/env secrets for downstream systems (for example Gemini target creds) as usual.

## Mode compatibility

- `file_pull`: supported and primary file extraction mode.
- `sql_pull`: not applicable.
- `rest_pull`: not applicable.
- `rest_push`: not applicable.

## Common errors and fixes

- Directory missing or not mounted:
  - Ensure `source.path` exists in runtime container/host.
- Unexpected files selected:
  - Tighten `source.glob` pattern.
- Recursive glob rejected:
  - Use non-recursive patterns only in v1.
- CSV parse/mapping mismatch:
  - Verify delimiter/header settings and mapping field names.
