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

## Static bearer secret format

Use raw token value in secret storage:

```text
<api-token>
```

Runtime behavior:

- Resolves token from `secretRef`.
- Adds `Authorization: Bearer <token>` by default for `rest_pull`.

## OAuth client credentials secret format

When `source.oauth` is configured, the runtime resolves OAuth client secret from:

- `source.oauth.clientSecretRef`, or
- fallback `source.secretRef` when `clientSecretRef` is omitted.

Store the raw OAuth client secret value:

```text
<oauth-client-secret>
```

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

### REST pull with OAuth client credentials

```yaml
source:
  type: http
  secretRef: kb-api-token
  url: https://kb.internal/api/v1/articles
  method: GET
  oauth:
    grantType: client_credentials
    tokenUrl: https://auth.local/realms/acme/protocol/openid-connect/token
    clientId: bridge-client
    clientSecretRef: kb-oauth-client-secret
    scopes:
      - api.read
    audience: knowledge-api
    clientAuthMethod: client_secret_post # or client_secret_basic
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
- `file_pull`: not applicable.

## Common connection errors and fixes

- 401/403 responses
  - Static bearer mode: verify token and required headers.
  - OAuth mode: verify token endpoint URL, client ID, secret ref, and auth method.
- 429 responses
  - Increase schedule interval or coordinate API rate limits.
- Unsupported payload shape
  - Ensure API returns list or object with `items` list for `rest_pull`.
- Missing `access_token` in OAuth token response
  - Verify OAuth provider response contract and client credentials setup.
- Confusion in `rest_push` auth
  - v1 ingress does not enforce auth from `secretRef`; secure network boundary externally.
