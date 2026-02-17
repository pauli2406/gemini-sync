# Connector Field Reference

> Generated from `schemas/connector.schema.json` and `schemas/connector.docs-meta.yaml`.
> Do not edit manually. Run `python scripts/export_connector_reference.py`.

| Field Path | Type | Required | Default | Allowed Values / Pattern | Modes | Description | Example | Operational Notes |
|---|---|---|---|---|---|---|---|---|
| `apiVersion` | `string` | Yes | `sync.gemini.io/v1alpha1` | const: `sync.gemini.io/v1alpha1` | `sql_pull`, `rest_pull`, `rest_push` | Connector API version. | `sync.gemini.io/v1alpha1` | Must remain unchanged for v1 compatibility. |
| `kind` | `string` | Yes | `Connector` | const: `Connector` | `sql_pull`, `rest_pull`, `rest_push` | Top-level resource kind. | `Connector` | Must be Connector. |
| `metadata` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Connector metadata container. | `{name: hr-employees}` | - |
| `metadata.name` | `string` | Yes | - | pattern: `^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$` | `sql_pull`, `rest_pull`, `rest_push` | Stable connector identifier used in runs, paths, and UI. | `hr-employees` | Must match ^\[a-z0-9\](\[a-z0-9-\]{0,62}\[a-z0-9\])?$. |
| `spec` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Connector runtime specification. | `{mode: sql_pull, ...}` | - |
| `spec.mode` | `string` | Yes | - | enum: `sql_pull`, `rest_pull`, `rest_push` | `sql_pull`, `rest_pull`, `rest_push` | Connector execution mode. | `sql_pull` | Select sql_pull, rest_pull, or rest_push only. |
| `spec.schedule` | `string | null` | No | - | - | `sql_pull`, `rest_pull` | Cron schedule for pull connectors. | `0 */3 * * *` | Required for sql_pull and rest_pull; omitted for rest_push. |
| `spec.source` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Source extraction configuration. | `{type: postgres, secretRef: hr-db-credentials, ...}` | - |
| `spec.source.type` | `string` | Yes | - | enum: `postgres`, `mssql`, `mysql`, `http` | `sql_pull`, `rest_pull`, `rest_push` | Source provider type. | `postgres` | Use http for rest_pull and rest_push. |
| `spec.source.secretRef` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Secret reference resolved by runtime. | `hr-db-credentials` | Maps to environment variable SECRET_HR_DB_CREDENTIALS or managed secret. |
| `spec.source.query` | `string | null` | No | - | - | `sql_pull` | SQL statement executed for extraction. | `SELECT employee_id, full_name FROM employees` | Required for sql_pull. Use snapshot query for auto_delete_missing. |
| `spec.source.watermarkField` | `string | null` | No | - | - | `sql_pull`, `rest_pull` | Field used to compute max checkpoint watermark. | `updated_at` | Must exist in extracted rows to advance checkpoint. |
| `spec.source.url` | `string | null` | No | - | - | `rest_pull` | REST endpoint URL to pull data from. | `https://kb.internal/api/v1/articles` | Required for rest_pull. |
| `spec.source.method` | `string` | No | - | - | `rest_pull` | HTTP method used for REST pull requests. | `GET` | GET is default; POST can be used for query APIs. |
| `spec.source.payload` | `object | null` | No | - | - | `rest_pull` | Optional JSON body for REST requests. | `{includeArchived: false}` | Sent as request JSON. |
| `spec.source.paginationCursorField` | `string | null` | No | - | - | `rest_pull` | Query parameter key used for cursor pagination requests. | `cursor` | - |
| `spec.source.paginationNextCursorJsonPath` | `string | null` | No | - | - | `rest_pull` | Dotted JSON path to next cursor value in response body. | `paging.next_cursor` | If empty or missing at runtime, pagination stops. |
| `spec.source.headers` | `object` | No | - | - | `rest_pull` | Static request headers map. | `{X-Tenant: internal}` | Authorization header is auto-added unless already provided. |
| `spec.mapping` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Mapping from source row fields to canonical document. | `{idField: employee_id, titleField: full_name, ...}` | - |
| `spec.mapping.idField` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Source field used for unique record key. | `employee_id` | Combined with connector name to create canonical doc_id. |
| `spec.mapping.titleField` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Source field used for document title. | `full_name` | - |
| `spec.mapping.contentTemplate` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Jinja template rendered into document content. | `{{ department }} {{ role }} {{ bio }}` | Missing template variables cause run failure. |
| `spec.mapping.uriTemplate` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | Optional Jinja template for source document URI. | `https://hr.internal/employees/{{ employee_id }}` | - |
| `spec.mapping.mimeType` | `string` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | MIME type for generated document content. | `text/plain` | - |
| `spec.mapping.aclUsersField` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | Source field that maps to acl_users. | `allowed_users` | - |
| `spec.mapping.aclGroupsField` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | Source field that maps to acl_groups. | `allowed_groups` | - |
| `spec.mapping.metadataFields` | `array` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | Additional source fields copied into metadata. | `\[department, role\]` | - |
| `spec.output` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Artifact publishing destination settings. | `{bucket: gs://company-gemini-sync, prefix: hr-employees, format: ndjson}` | - |
| `spec.output.bucket` | `string` | Yes | - | pattern: `^(gs|file)://` | `sql_pull`, `rest_pull`, `rest_push` | Object store URI prefix for artifacts. | `gs://company-gemini-sync` | Supports gs:// for cloud and file:// for local development. |
| `spec.output.prefix` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Connector-specific output path segment under connectors/. | `hr-employees` | - |
| `spec.output.format` | `string` | Yes | `ndjson` | const: `ndjson` | `sql_pull`, `rest_pull`, `rest_push` | Output serialization format. | `ndjson` | Only ndjson is supported in v1. |
| `spec.gemini` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Gemini/Discovery Engine target data store configuration. | `{projectId: my-project, location: eu, dataStoreId: hr-ds}` | - |
| `spec.gemini.projectId` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | GCP project ID containing target data store. | `gemini-enterprise-test-487620` | - |
| `spec.gemini.location` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Data store location and API routing region. | `eu` | Must match the actual data store location. |
| `spec.gemini.dataStoreId` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Target Discovery Engine data store ID. | `hr-ds` | - |
| `spec.reconciliation` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push` | Reconciliation and delete strategy settings. | `{deletePolicy: auto_delete_missing}` | - |
| `spec.reconciliation.deletePolicy` | `string` | Yes | - | enum: `auto_delete_missing`, `soft_delete_only`, `never_delete` | `sql_pull`, `rest_pull`, `rest_push` | Controls how missing/removed records are handled. | `auto_delete_missing` | For auto_delete_missing, use snapshot extraction queries. |
