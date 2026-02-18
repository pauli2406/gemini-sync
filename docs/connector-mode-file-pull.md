# File Pull Connector Mode

## When to use this mode

Use `file_pull` when source data is delivered as local files and should be polled on a schedule.

Best fit:

- Source exports CSV files to a mounted directory.
- You want YAML-based mapping without building an API layer.
- You want full snapshot reconciliation each run.

## Minimal YAML (copy/paste)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: hr-file-csv
spec:
  mode: file_pull
  schedule: "0 */2 * * *"
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
  mapping:
    idField: employee_id
    titleField: full_name
    contentTemplate: "{{ full_name }}"
  output:
    bucket: file://./local-bucket
    prefix: hr-file-csv
    format: ndjson
  gemini:
    projectId: my-project
    location: global
    dataStoreId: hr-file-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Source behavior

- `path` + `glob` are used for deterministic non-recursive file discovery.
- All matched files are processed each run (snapshot pull semantics).
- `format` is currently fixed to `csv` (future parser hook point).

## CSV document modes

| Mode | Output shape |
|---|---|
| `row` | One extracted record per CSV row. |
| `file` | One extracted record per CSV file. |

### Synthetic file fields available in mapping templates

- `file_path`
- `file_name`
- `file_mtime`
- `file_size_bytes`
- `file_content_raw` (file mode)
- `file_rows_json` (file mode)

## Checkpoint behavior

`file_pull` stores a compact structured checkpoint in `connector_checkpoints.watermark`:

```json
{"v":1,"rw":"2026-02-16T10:00:00+00:00","fc":2,"lm":"2026-02-16T10:00:00+00:00","fh":"sha256:..."}
```

- `rw`: max row watermark from `watermarkField` when present
- `fc`: matched file count
- `lm`: latest file mtime
- `fh`: hash of matched file manifest metadata

Legacy plain string checkpoints are still accepted as `rw` fallback.

## Validation checklist

1. `spec.schedule` is set.
2. `spec.source.path` exists and is readable by the runtime.
3. `spec.source.glob` is non-recursive (do not use `**` patterns).
4. `spec.source.csv.delimiter` is exactly one character.
5. Mapping fields (`idField`, `titleField`, templates) align with row columns or synthetic fields.
6. Run `python scripts/validate_connectors.py`.

## Common failures and fixes

- `source.path does not exist`
  - Fix mount path or connector `source.path`.
- `source.glob must be non-recursive for file_pull mode`
  - Replace `**/*.csv` with a non-recursive pattern like `*.csv`.
- `Duplicate document IDs detected in file_pull extraction`
  - Adjust `idField` or source data so IDs are unique across matched files.
- `source.csv.delimiter must be a single character`
  - Use one-character delimiters only (for example `,` or `;`).

## Provider notes and links

- File provider details: `docs/connector-provider-file.md`
- Full field table: `docs/connector-field-reference.md`
