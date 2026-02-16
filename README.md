# Gemini Sync Bridge

Gemini Sync Bridge is an open-source, GitOps-managed integration layer for syncing on-prem SQL/REST data into Google Cloud Storage (single cloud handoff) and ingesting it into Gemini Enterprise data stores.

## What v1 Includes

- Connector definitions in Git (`connectors/*.yaml`) validated by JSON Schema.
- Python runtime with three connector modes:
  - `sql_pull`
  - `rest_pull`
  - `rest_push`
- Canonical NDJSON document envelope with deterministic checksums.
- Reconciliation engine that computes upserts and deletes (`auto_delete_missing`).
- Artifact publishing to GCS (`gs://`) or local filesystem (`file://`) for development.
- Gemini ingestion worker using Discovery Engine APIs (or dry-run mode).
- Push API with idempotency semantics:
  - `POST /v1/connectors/{connector_id}/events`
  - Required header: `Idempotency-Key`
  - Push events are treated as delta operations (`op=UPSERT` or `op=DELETE`)
- Postgres-backed state store:
  - checkpoints
  - run status
  - document state
  - push event batches
- Observability hooks:
  - Teams webhook alerts on failures
  - Splunk HEC event publishing
- Kestra flow examples and Kubernetes/Helm deployment scaffolding.

## Repository Layout

- `gemini_sync_bridge/`: runtime, API, and pipeline code.
- `connectors/`: sample connector definitions.
- `flows/`: Kestra flow examples.
- `schemas/`: connector JSON schema.
- `infra/`: Helm chart and Kubernetes manifests.
- `tests/`: unit and API tests.
- `docs/`: architecture, operations, and connector authoring docs.

## Quickstart (Local)

### 1) Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2) Start local dependencies

```bash
docker compose up -d postgres
```

### 3) Configure env

```bash
cp .env.example .env
```

For local-only testing without GCS, set connector bucket to `file://./local-bucket`.

### 4) Initialize DB tables

```bash
gemini-sync-bridge init-db
```

### 5) Validate connector definitions

```bash
python scripts/validate_connectors.py
```

### 6) Run a connector pipeline manually

```bash
gemini-sync-bridge run --connector connectors/hr-employees.yaml
```

### 7) Start push API

```bash
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
```

Submit events:

```bash
curl -X POST "http://localhost:8080/v1/connectors/support-push/events" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: run-001" \
  -d '[
    {
      "doc_id":"support-push:123",
      "title":"VPN issue",
      "content":"Cannot connect from home",
      "uri":"https://support.internal/tickets/123",
      "mime_type":"text/plain",
      "updated_at":"2026-02-16T08:30:00Z",
      "acl_users":[],
      "acl_groups":["it-support"],
      "metadata":{"connector_id":"support-push"},
      "checksum":"sha256:test",
      "op":"UPSERT"
    }
  ]'
```

Process queued push events:

```bash
gemini-sync-bridge run --connector connectors/support-push.yaml
```

## CI Checks

- Connector schema validation
- Pytest suite
- Ruff linting

## Production Notes

- Keep `GEMINI_INGESTION_DRY_RUN=false` only in environments with valid Google credentials and quota controls.
- Use Kubernetes Secrets to provide `SECRET_<SECRETREF>` values.
- Run this service in a private network segment with access to on-prem systems and controlled egress to GCP.

## License

Apache-2.0
