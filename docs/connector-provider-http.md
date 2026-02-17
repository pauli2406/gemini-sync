# Provider: HTTP APIs

## Supported status

Supported in current runtime.

## `source.type` value

Use:

```yaml
spec:
  source:
    type: http
```

## Secret token format

Use raw token value in secret storage:

```text
<api-token>
```

Runtime behavior:

- Resolves token from `secretRef`.
- Adds `Authorization: Bearer <token>` by default for `rest_pull`.

## Environment variable mapping

If connector has:

```yaml
secretRef: kb-api-token
```

Set:

```bash
export SECRET_KB_API_TOKEN='replace-me'
```

## YAML snippets

### REST pull

```yaml
source:
  type: http
  secretRef: kb-api-token
  url: https://kb.internal/api/v1/articles
  method: GET
  payload: null
  paginationCursorField: cursor
  paginationNextCursorJsonPath: paging.next_cursor
  headers:
    X-Tenant: internal
```

### REST push

```yaml
source:
  type: http
  secretRef: support-push-token
```

## Mode compatibility

- `rest_pull`: supported and primary pull API use case.
- `rest_push`: supported for push queue connectors.
- `sql_pull`: not applicable.

## Common connection errors and fixes

- 401/403 responses
  - Verify token and required headers.
- 429 responses
  - Increase schedule interval or coordinate API rate limits.
- Unsupported payload shape
  - Ensure API returns list or object with `items` list for `rest_pull`.
- Confusion in `rest_push` auth
  - v1 ingress does not enforce auth from `secretRef`; secure network boundary externally.
