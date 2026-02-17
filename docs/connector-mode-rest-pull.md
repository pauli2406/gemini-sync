# REST Pull Connector Mode

## When to use this mode

Use `rest_pull` when an external/internal HTTP API should be polled on a schedule.

Best fit:

- Source publishes JSON APIs.
- You want cursor pagination handling.
- You need centralized retries/backoff and run visibility.

## Minimal YAML (copy/paste)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: kb-rest
spec:
  mode: rest_pull
  schedule: "*/30 * * * *"
  source:
    type: http
    secretRef: kb-api-token
    url: https://kb.internal/api/v1/articles
    method: GET
    watermarkField: updated_at
  mapping:
    idField: article_id
    titleField: title
    contentTemplate: "{{ title }}\n{{ body }}"
  output:
    bucket: gs://company-gemini-sync
    prefix: kb-rest
    format: ndjson
  gemini:
    projectId: my-project
    location: global
    dataStoreId: kb-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Full YAML (annotated)

```yaml
apiVersion: sync.gemini.io/v1alpha1
kind: Connector
metadata:
  name: kb-rest
spec:
  mode: rest_pull
  schedule: "*/30 * * * *" # required for pull modes
  source:
    type: http
    secretRef: kb-api-token # SECRET_KB_API_TOKEN
    url: https://kb.internal/api/v1/articles
    method: GET # GET default; POST also supported
    payload:
      includeArchived: false # optional request JSON
    watermarkField: updated_at
    paginationCursorField: cursor
    paginationNextCursorJsonPath: paging.next_cursor
    headers:
      X-Tenant: internal
  mapping:
    idField: article_id
    titleField: title
    contentTemplate: "{{ title }}\n{{ body }}"
    uriTemplate: "https://kb.internal/article/{{ article_id }}"
    mimeType: text/plain
    aclUsersField: allowed_users
    aclGroupsField: allowed_groups
    metadataFields:
      - category
      - owner
  output:
    bucket: gs://company-gemini-sync
    prefix: kb-rest
    format: ndjson
  gemini:
    projectId: my-project
    location: global
    dataStoreId: kb-ds
  reconciliation:
    deletePolicy: auto_delete_missing
```

## Field-by-field explanation

| Field | Meaning | Options |
|---|---|---|
| `spec.schedule` | Polling schedule. | Any valid cron string. |
| `spec.source.type` | Source adapter type. | Use `http` for `rest_pull`. |
| `spec.source.secretRef` | API token secret reference. | Any non-empty string; mapped to `SECRET_<SECRETREF>`. |
| `spec.source.url` | Endpoint URL. | HTTPS URL recommended. |
| `spec.source.method` | HTTP method. | `GET`, `POST`, `PUT`, `PATCH` |
| `spec.source.payload` | Request body for non-GET or query APIs. | JSON object or `null`. |
| `spec.source.headers` | Static headers to send with each request. | `key: value` map. |
| `spec.source.paginationCursorField` | Request query parameter key for cursor. | Example `cursor`. |
| `spec.source.paginationNextCursorJsonPath` | Path to next cursor in response JSON. | Example `paging.next_cursor`. |
| `spec.source.watermarkField` | Field used for checkpoint max-watermark. | Example `updated_at`. |

## Mode-specific decision matrix

| API response shape | Config | Use? | Why |
|---|---|---|---|
| JSON list (`[...]`) | No pagination fields required | Yes | Runtime accepts list directly. |
| JSON object with `items` list | No pagination fields required | Yes | Runtime reads `items`. |
| Cursor paginated object | Set both pagination fields | Yes (recommended) | Runtime loops until no next cursor. |
| JSON object without `items` and without list root | N/A | No | Runtime rejects unsupported payload shape. |

| Watermark strategy | Runtime behavior | Guidance |
|---|---|---|
| `watermarkField` set and present in rows | Checkpoint advances to max value | Recommended for incremental pulls. |
| `watermarkField` missing in rows | Checkpoint cannot advance | Fix source response or field mapping. |
| No watermark strategy but `auto_delete_missing` | Full snapshots required | Avoid partial/incremental pulls with hard delete policy. |

## Validation checklist

1. `spec.schedule` is set.
2. `spec.source.url` is set and reachable.
3. Secret token is available via `SECRET_<SECRETREF>` or managed secret.
4. API returns either list or object containing `items` list.
5. Pagination keys/json path align to API contract.
6. Run `python scripts/validate_connectors.py`.

## Common failures and fixes

- `source.url is required for rest_pull mode`
  - Add `spec.source.url`.
- `REST 'items' must be a list`
  - Update API endpoint or transformation so `items` is an array.
- Frequent 429/5xx responses
  - Reduce schedule frequency, tune source side limits, keep retries enabled.
- No checkpoint movement
  - Ensure `watermarkField` exists in every returned row.

## Provider notes and links

- HTTP provider details: `docs/connector-provider-http.md`
- Reconciliation behavior: `docs/connector-mode-sql-pull.md` decision matrix applies conceptually to snapshot vs incremental pulls.
- Full field table: `docs/connector-field-reference.md`
