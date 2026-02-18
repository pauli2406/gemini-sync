# Troubleshooting

This page covers the most common failures when running connector ingestion end-to-end.

## Discovery Engine API Disabled

Error pattern:

- `SERVICE_DISABLED`
- `Discovery Engine API has not been used in project ...`

Fix:

```bash
gcloud services enable discoveryengine.googleapis.com --project "${PROJECT_ID}"
```

## Region Endpoint Mismatch

Error pattern:

- `Incorrect API endpoint used ... can only serve traffic from "global" region`

Fix:

- Use `discoveryengine.googleapis.com` only for `global`.
- Use `${LOCATION}-discoveryengine.googleapis.com` for non-global locations.

## Datastore Not Found

Error pattern:

- `dataStores/<id> not found`

Fix:

- Verify connector `projectId`, `location`, and `dataStoreId` exactly match the created datastore.

## ADC Quota Project Missing

Error pattern:

- `API requires a quota project`

Fix:

```bash
gcloud auth application-default set-quota-project "${PROJECT_ID}"
```

## Missing Source Secret

Error pattern:

- `Missing secret for '<ref>'. Expected environment variable SECRET_<...>`

Fix:

- Export the expected secret env var, for example:
  - `SECRET_HR_DB_CREDENTIALS=postgresql+psycopg2://...`

## REST Pull OAuth Token Request Fails

Error pattern:

- `OAuth token request failed with status 400`
- `OAuth token request failed with status 401`
- `OAuth token request failed with status 403`

Fix:

- Verify `spec.source.oauth.tokenUrl` and `spec.source.oauth.clientId`.
- Verify OAuth client secret in `spec.source.oauth.clientSecretRef` or `spec.source.secretRef`.
- Verify `spec.source.oauth.clientAuthMethod` matches provider expectation:
  - `client_secret_post`
  - `client_secret_basic`
- Verify requested scopes/audience are allowed.

## REST Pull OAuth Token Payload Invalid

Error pattern:

- `OAuth token response missing required 'access_token' field`
- `OAuth token response was not valid JSON`

Fix:

- Verify token endpoint returns JSON object with `access_token`.
- Check upstream auth proxy/IdP response transformation.

## Proxy Authentication Required (407)

Error pattern:

- `407 Proxy Authentication Required`

Fix:

- Verify `HTTP_PROXY`/`HTTPS_PROXY` include valid proxy credentials (if required).
- URL-encode special characters in credential components.
- Confirm outbound destination is intended to route through proxy and not bypassed by `NO_PROXY`.

## TLS Verification Fails Behind Enterprise Proxy

Error pattern:

- `certificate verify failed`
- `unable to get local issuer certificate`

Fix:

- Set `SSL_CERT_FILE` to the enterprise CA bundle path.
- Set `REQUESTS_CA_BUNDLE` to the same CA bundle path.
- Ensure the CA bundle file is readable by the runtime process/container.

## NO_PROXY Misconfiguration

Error pattern:

- Internal host calls unexpectedly routed to proxy.
- Local services fail only when proxy env vars are enabled.

Fix:

- Add local/internal hosts to `NO_PROXY`, for example:
  - `localhost`
  - `127.0.0.1`
  - `postgres`
  - `.internal`
- Restart process/container after env updates.

## Runtime DB Not Initialized

Error pattern:

- `relation "run_state" does not exist`

Fix:

```bash
.venv/bin/gemini-sync-bridge init-db
```

Also verify the active runtime DB:

```bash
echo "${DATABASE_URL}"
.venv/bin/python -c "from gemini_sync_bridge.settings import get_settings; print(get_settings().database_url)"
```

## Reconciliation Semantics: Snapshot vs Incremental

Symptom:

- `upserts=0, deletes>0` while source still contains rows.

Cause:

- Incremental extraction query + `auto_delete_missing` delete policy.

Fix:

- Use snapshot query (no watermark filter) when `deletePolicy: auto_delete_missing`.
- Use non-destructive delete policy if query stays incremental.

## Deleting a Test Datastore

Set host based on location:

```bash
if [ "${LOCATION}" = "global" ]; then
  API_HOST="discoveryengine.googleapis.com"
else
  API_HOST="${LOCATION}-discoveryengine.googleapis.com"
fi
```

Delete datastore:

```bash
DELETE_RESPONSE="$(curl -s -X DELETE \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://${API_HOST}/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${DATA_STORE_ID}")"
echo "${DELETE_RESPONSE}"
```

Poll operation status:

```bash
OP_NAME="$(echo "${DELETE_RESPONSE}" | jq -r '.name')"
curl -s \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://${API_HOST}/v1/${OP_NAME}"
```
