# Discovery Engine CLI Playbook

Use this runbook to onboard any new connector/data store pair end-to-end using CLI only.

## Scope

- Source systems: SQL (`sql_pull`), REST (`rest_pull`/`rest_push`), or local files (`file_pull`).
- Cloud handoff: GCS.
- Ingestion target: Discovery Engine data store in Gemini Enterprise.

## 1) Prerequisites

1. Local dependencies:
   - Docker (for local Postgres if needed)
   - gcloud CLI
   - Project venv (`.venv`) with bridge installed
2. Enabled API in target project:
   - `discoveryengine.googleapis.com`
3. Auth:
   - Application Default Credentials configured
   - Quota project set on ADC

## 2) Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export LOCATION="eu"                       # or global/us
export DATA_STORE_ID="your-datastore-id"   # letters/numbers/-/_
export BUCKET="your-bucket-name"           # no gs:// prefix here
export CONNECTOR_ID="hr-employees"

if [ "${LOCATION}" = "global" ]; then
  export API_HOST="discoveryengine.googleapis.com"
else
  export API_HOST="${LOCATION}-discoveryengine.googleapis.com"
fi
```

## 3) Configure gcloud + ADC Correctly

```bash
gcloud config set project "${PROJECT_ID}"
gcloud auth application-default login
gcloud auth application-default set-quota-project "${PROJECT_ID}"
```

## 4) Create a Data Store (CLI/API)

Create a search datastore in the target location/collection:

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  -H "Content-Type: application/json" \
  "https://${API_HOST}/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores?dataStoreId=${DATA_STORE_ID}" \
  -d '{
    "displayName": "HR Data Store",
    "industryVertical": "GENERIC",
    "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
    "contentConfig": "CONTENT_REQUIRED"
  }'
```

Verify it exists:

```bash
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://${API_HOST}/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${DATA_STORE_ID}"
```

Expected:

- `name` points to your data store
- `location` matches `LOCATION`
- `contentConfig` is present (typically `CONTENT_REQUIRED`)

## 5) Grant Data Store Service Agent Read Access to GCS

Get project number:

```bash
PROJECT_NUMBER="$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')"
echo "${PROJECT_NUMBER}"
```

Grant bucket read access:

```bash
gcloud storage buckets add-iam-policy-binding gs://${BUCKET} \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

## 6) Configure Connector YAML

Update connector file:

- `spec.output.bucket: gs://${BUCKET}`
- `spec.gemini.projectId: ${PROJECT_ID}`
- `spec.gemini.location: ${LOCATION}`
- `spec.gemini.dataStoreId: ${DATA_STORE_ID}`

For `auto_delete_missing`, use snapshot SQL (no watermark filter in query):

```yaml
spec:
  source:
    query: >
      SELECT employee_id, full_name, department, role, bio, allowed_users, allowed_groups, updated_at
      FROM employees
  reconciliation:
    deletePolicy: auto_delete_missing
```

If you need incremental SQL (`WHERE updated_at > :watermark`), do not use full-delete reconciliation.

For file-based CSV connectors, configure local file source fields:

```yaml
spec:
  mode: file_pull
  source:
    type: file
    path: ./runtime/sources/hr
    glob: "*.csv"
    format: csv
    csv:
      documentMode: row
      delimiter: ","
      hasHeader: true
      encoding: utf-8
```

## 7) Configure Runtime DB vs Source DB Separately

Bridge runtime state DB:

```bash
export DATABASE_URL='postgresql+psycopg2://postgres:postgres@localhost:5432/gemini_sync_bridge'
```

Source connection secret (example for SQL source):

```bash
export SECRET_HR_DB_CREDENTIALS='postgresql+psycopg2://postgres:postgres@localhost:5432/gemini_sync_bridge'
```

Initialize runtime tables:

```bash
.venv/bin/gemini-sync-bridge init-db
```

## 8) Force a Clean First Import (Optional but Recommended)

```bash
docker compose exec -T postgres psql -U postgres -d gemini_sync_bridge -c \
"DELETE FROM record_state WHERE connector_id='${CONNECTOR_ID}';
 DELETE FROM connector_checkpoints WHERE connector_id='${CONNECTOR_ID}';"
```

## 9) Run Connector

```bash
.venv/bin/gemini-sync-bridge run --connector connectors/${CONNECTOR_ID}.yaml
```

Expected first successful run:

- `upserts > 0`
- `deletes = 0` (unless source already removed prior docs)

Expected second run with unchanged source:

- `upserts = 0`
- `deletes = 0`

## 10) Verify Artifacts and Import Content

Use the run id from CLI output:

```bash
RUN_ID="<run-id>"
gcloud storage cat gs://${BUCKET}/connectors/${CONNECTOR_ID}/runs/${RUN_ID}/manifest.json
gcloud storage cat gs://${BUCKET}/connectors/${CONNECTOR_ID}/runs/${RUN_ID}/upserts.discovery.ndjson | head -n 2
```

`upserts.discovery.ndjson` should include Discovery `Document` payload shape (`id`, `content`, `structData`).

## 11) Common Errors and Fixes

1. `SERVICE_DISABLED` / Discovery API disabled:
   - Enable `discoveryengine.googleapis.com` in the same `PROJECT_ID`.
2. Endpoint region mismatch:
   - Use `${LOCATION}-discoveryengine.googleapis.com` for non-global regions.
3. Data store not found:
   - `projectId`, `location`, and `dataStoreId` in connector must exactly match the created store.
4. ADC quota project error:
   - Run `gcloud auth application-default set-quota-project ${PROJECT_ID}`.
5. `Missing secret for ... SECRET_<...>`:
   - Export expected env var or add managed secret.
6. `relation "run_state" does not exist`:
   - Run `.venv/bin/gemini-sync-bridge init-db` against current `DATABASE_URL`.
7. `upserts=0,deletes>0` with source rows still present:
   - You likely used incremental query with `auto_delete_missing`.
   - Switch to snapshot query for full-delete reconciliation.
8. `upserts=0,deletes=0` when expecting import:
   - Existing state already matches source; clear connector state and rerun.

## 12) Repeat for Additional Data Stores

For each new connector/data store pair:

1. New `DATA_STORE_ID`
2. Connector `spec.gemini.*` and `spec.output.bucket`
3. Secret env var for source
4. `init-db` once per runtime DB
5. First run + artifact verification

## 13) Delete a Test Data Store

Use this for cleanup in lower environments:

```bash
DELETE_RESPONSE="$(curl -s -X DELETE \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://${API_HOST}/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${DATA_STORE_ID}")"
echo "${DELETE_RESPONSE}"
```

Poll until done:

```bash
OP_NAME="$(echo "${DELETE_RESPONSE}" | jq -r '.name')"
curl -s \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: ${PROJECT_ID}" \
  "https://${API_HOST}/v1/${OP_NAME}"
```
