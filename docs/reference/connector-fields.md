# Connector Field Reference

> Generated from `schemas/connector.schema.json` and `schemas/connector.docs-meta.yaml`.
> Do not edit manually. Run `python scripts/export_connector_reference.py`.

| Field Path | Type | Required | Default | Allowed Values / Pattern | Modes | Description | Example | Operational Notes |
|---|---|---|---|---|---|---|---|---|
| `apiVersion` | `string` | Yes | `sync.gemini.io/v1alpha1` | const: `sync.gemini.io/v1alpha1` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Connector API version. | `sync.gemini.io/v1alpha1` | Must remain unchanged for v1 compatibility. |
| `kind` | `string` | Yes | `Connector` | const: `Connector` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Top-level resource kind. | `Connector` | Must be Connector. |
| `metadata` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Connector metadata container. | `{name: hr-employees}` | - |
| `metadata.name` | `string` | Yes | - | pattern: `^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Stable connector identifier used in runs, paths, and UI. | `hr-employees` | Must match ^\[a-z0-9\](\[a-z0-9-\]{0,62}\[a-z0-9\])?$. |
| `spec` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Connector runtime specification. | `{mode: sql_pull, ...}` | - |
| `spec.mode` | `string` | Yes | - | enum: `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Connector execution mode. | `sql_pull` | Select sql_pull, rest_pull, rest_push, or file_pull only. |
| `spec.schedule` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `file_pull` | Cron schedule for pull connectors. | `0 */3 * * *` | Required for sql_pull, rest_pull, and file_pull; omitted for rest_push. |
| `spec.source` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source extraction configuration. | `{type: postgres, secretRef: hr-db-credentials, ...}` | - |
| `spec.source.type` | `string` | Yes | - | enum: `postgres`, `mssql`, `mysql`, `oracle`, `http`, `file` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source provider type. | `postgres` | Use postgres/mssql/mysql/oracle for sql_pull; use http for rest_pull and rest_push; use file for file_pull. |
| `spec.source.secretRef` | `string` | No | - | - | `sql_pull`, `rest_pull`, `rest_push` | Secret reference resolved by runtime. | `hr-db-credentials` | Required for sql_pull/rest_pull/rest_push. Maps to environment variable SECRET_HR_DB_CREDENTIALS or managed secret; also used as OAuth client secret fallback when oauth.clientSecretRef is omitted. |
| `spec.source.query` | `string | null` | No | - | - | `sql_pull` | SQL statement executed for extraction. | `SELECT employee_id, full_name FROM employees` | Required for sql_pull. Use snapshot query for auto_delete_missing. |
| `spec.source.watermarkField` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `file_pull` | Field used to compute max checkpoint watermark. | `updated_at` | Must exist in extracted rows to advance checkpoint. |
| `spec.source.url` | `string | null` | No | - | - | `rest_pull` | REST endpoint URL to pull data from. | `https://kb.internal/api/v1/articles` | Required for rest_pull. |
| `spec.source.path` | `string | null` | No | - | - | `file_pull` | Local source directory path for file discovery. | `./data` | Must exist at runtime and be readable by the connector process. |
| `spec.source.glob` | `string | null` | No | - | - | `file_pull` | Non-recursive file glob pattern under source.path. | `*.csv` | v1 file_pull rejects recursive patterns (for example **/*.csv). |
| `spec.source.format` | `string | null` | No | - | enum: `csv`, `null` | `file_pull` | File parser format selector. | `csv` | v1 supports only csv. |
| `spec.source.csv` | `object | null` | No | - | - | `file_pull` | CSV parser configuration block. | `{documentMode: row, delimiter: ',', hasHeader: true, encoding: utf-8}` | - |
| `spec.source.csv.documentMode` | `string` | No | `row` | enum: `row`, `file` | `file_pull` | Controls whether records are emitted per CSV row or per file. | `row` | Supported values are row and file. |
| `spec.source.csv.delimiter` | `string` | No | `,` | - | `file_pull` | CSV delimiter character. | `,` | Must be exactly one character. |
| `spec.source.csv.hasHeader` | `boolean` | No | `true` | - | `file_pull` | Whether first CSV row is treated as header. | `true` | - |
| `spec.source.csv.encoding` | `string` | No | `utf-8` | - | `file_pull` | Text encoding used to decode CSV files. | `utf-8` | - |
| `spec.source.csv.normalizeHeaders` | `boolean` | No | `false` | - | `file_pull` | Normalize CSV headers to safe snake_case identifiers (strips accents, replaces special characters). | `true` | Enable when CSV headers contain spaces, slashes, parentheses, or non-ASCII characters that are incompatible with Jinja template variable syntax. |
| `spec.source.csv.cleanErrors` | `boolean` | No | `false` | - | `file_pull` | Replace cell values starting with #ERROR with empty strings. | `true` | Useful for cleaning export artifacts from tools like Signavio or Excel that emit #ERROR values on formula failures. |
| `spec.source.method` | `string` | No | - | - | `rest_pull` | HTTP method used for REST pull requests. | `GET` | GET is default; POST can be used for query APIs. |
| `spec.source.payload` | `object | null` | No | - | - | `rest_pull` | Optional JSON body for REST requests. | `{includeArchived: false}` | Sent as request JSON. |
| `spec.source.paginationCursorField` | `string | null` | No | - | - | `rest_pull` | Query parameter key used for cursor pagination requests. | `cursor` | - |
| `spec.source.paginationNextCursorJsonPath` | `string | null` | No | - | - | `rest_pull` | Dotted JSON path to next cursor value in response body. | `paging.next_cursor` | If empty or missing at runtime, pagination stops. |
| `spec.source.headers` | `object` | No | - | - | `rest_pull` | Static request headers map. | `{X-Tenant: internal}` | Authorization header is auto-added for static bearer mode unless already provided; OAuth mode overrides Authorization with runtime-issued token. |
| `spec.source.oauth` | `object` | No | - | - | `rest_pull` | Optional OAuth client-credentials configuration for service-to-service token acquisition. | `{grantType: client_credentials, tokenUrl: https://auth.local/realms/acme/protocol/openid-connect/token, clientId: bridge-client}` | When set, runtime fetches and refreshes bearer tokens automatically. |
| `spec.source.oauth.grantType` | `string` | No | `client_credentials` | const: `client_credentials` | `rest_pull` | OAuth grant type for token acquisition. | `client_credentials` | v1 supports only client_credentials. |
| `spec.source.oauth.tokenUrl` | `string` | Yes | - | - | `rest_pull` | OAuth token endpoint URL. | `https://auth.local/realms/acme/protocol/openid-connect/token` | Required when oauth block is configured. |
| `spec.source.oauth.clientId` | `string` | Yes | - | - | `rest_pull` | OAuth client identifier. | `bridge-client` | Required when oauth block is configured. |
| `spec.source.oauth.clientSecretRef` | `string | null` | No | - | - | `rest_pull` | Optional secret reference for OAuth client secret. | `kb-oauth-client-secret` | Falls back to spec.source.secretRef when omitted. |
| `spec.source.oauth.scopes` | `array` | No | - | - | `rest_pull` | OAuth scopes sent to token endpoint as space-delimited scope value. | `\[api.read, api.write\]` | - |
| `spec.source.oauth.audience` | `string | null` | No | - | - | `rest_pull` | Optional OAuth audience parameter. | `knowledge-api` | - |
| `spec.source.oauth.clientAuthMethod` | `string` | No | `client_secret_post` | enum: `client_secret_post`, `client_secret_basic` | `rest_pull` | OAuth client authentication method for token endpoint. | `client_secret_post` | Supported values are client_secret_post and client_secret_basic. |
| `spec.mapping` | `object` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Mapping from source row fields to canonical document. | `{idField: employee_id, titleField: full_name, ...}` | Required when spec.output.format is ndjson. Optional for sql_pull CSV exports. |
| `spec.mapping.idField` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source field used for unique record key. | `employee_id` | Combined with connector name to create canonical doc_id. |
| `spec.mapping.titleField` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source field used for document title. | `full_name` | - |
| `spec.mapping.contentTemplate` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Jinja template rendered into document content. | `{{ department }} {{ role }} {{ bio }}` | Missing template variables cause run failure. |
| `spec.mapping.uriTemplate` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Optional Jinja template for source document URI. | `https://hr.internal/employees/{{ employee_id }}` | - |
| `spec.mapping.mimeType` | `string` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | MIME type for generated document content. | `text/plain` | - |
| `spec.mapping.aclUsersField` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source field that maps to acl_users. | `allowed_users` | - |
| `spec.mapping.aclGroupsField` | `string | null` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Source field that maps to acl_groups. | `allowed_groups` | - |
| `spec.mapping.metadataFields` | `array` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Additional source fields copied into metadata. | `\[department, role\]` | - |
| `spec.output` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Artifact publishing destination settings. | `{bucket: gs://company-ingest-relay, prefix: hr-employees, format: ndjson, publishLatestAlias: false}` | - |
| `spec.output.bucket` | `string` | Yes | - | pattern: `^(gs|file)://` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Object store URI prefix for artifacts. | `gs://company-ingest-relay` | Supports gs:// for cloud and file:// for local development. |
| `spec.output.prefix` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Connector-specific output path segment under connectors/. | `hr-employees` | - |
| `spec.output.format` | `string` | Yes | - | enum: `ndjson`, `csv` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Output serialization format. | `csv` | Use ndjson for canonical document ingestion flows; use csv for raw sql_pull exports to object storage. |
| `spec.output.publishLatestAlias` | `boolean` | No | `false` | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Overwrites stable latest alias artifacts under connectors/&lt;prefix&gt;/latest/. | `true` | Enable when downstream consumers should always read a fixed latest path while historical run artifacts stay preserved. |
| `spec.gemini` | `object` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Gemini/Discovery Engine target data store configuration. | `{projectId: my-project, location: eu, dataStoreId: hr-ds}` | Required unless spec.ingestion.enabled is false. |
| `spec.gemini.projectId` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | GCP project ID containing target data store. | `gemini-enterprise-test-487620` | - |
| `spec.gemini.location` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Data store location and API routing region. | `eu` | Must match the actual data store location. |
| `spec.gemini.dataStoreId` | `string` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Target Discovery Engine data store ID. | `hr-ds` | - |
| `spec.ingestion` | `object` | No | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Controls whether artifacts are ingested into Discovery Engine after publishing. | `{enabled: false}` | - |
| `spec.ingestion.enabled` | `boolean` | No | `true` | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Enables or disables Discovery Engine ingestion for this connector. | `false` | When false, spec.gemini can be omitted and the run is bucket-only. Must be false when spec.output.format is csv. |
| `spec.reconciliation` | `object` | Yes | - | - | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Reconciliation and delete strategy settings. | `{deletePolicy: auto_delete_missing}` | - |
| `spec.reconciliation.deletePolicy` | `string` | Yes | - | enum: `auto_delete_missing`, `soft_delete_only`, `never_delete` | `sql_pull`, `rest_pull`, `rest_push`, `file_pull` | Controls how missing/removed records are handled. | `auto_delete_missing` | For auto_delete_missing, use snapshot extraction queries. |
