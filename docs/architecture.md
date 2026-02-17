# Architecture

## Components

1. **Connector Runtime (Python)**
- Executes connector jobs in `sql_pull`, `rest_pull`, or `rest_push` mode.
- Produces canonical documents and reconciliation results.

2. **State Store (Postgres)**
- `connector_checkpoints`: per-connector watermark.
- `record_state`: doc checksum/index for diffing.
- `run_state`: run status/metrics/errors.
- `push_batches` + `push_events`: queued push ingestion with idempotency.

3. **Publisher**
- Writes canonical `upserts.ndjson`, Discovery import `upserts.discovery.ndjson`,
  `deletes.ndjson`, and `manifest.json` to object storage.
- Supports both `gs://` (prod) and `file://` (local dev).

4. **Gemini Ingestion Client**
- Imports upsert artifacts into Gemini data stores.
- Applies explicit document deletes.
- Supports dry-run mode.

5. **Push API**
- Receives canonical documents.
- Validates idempotency key and payload shape.
- Persists pending batches for pipeline processing.

6. **Orchestrator (Kestra)**
- Triggers scheduled runs.
- Provides built-in run visibility and retries.

7. **Observability**
- Splunk HEC events for run telemetry.
- Teams webhook alerts for failed runs.

8. **Ops UI (Read-Only)**
- FastAPI + Jinja pages for operator visibility.
- JSON APIs under `/v1/ops/*` for dashboard polling every 15 seconds.
- Supports run filtering (`status`, `connector_id`, `window_hours`) and pagination (`limit_runs`, `offset_runs`).
- Supports optional run deep links to Splunk and Kestra by `run_id`.
- Uses `run_state`, `connector_checkpoints`, and `push_batches` without mutating data.

9. **Connector Studio**
- FastAPI + Jinja guided UI for connection profile creation and lifecycle management.
- Proposes GitHub PR changes for create/edit/clone/delete/pause/resume actions.
- Uses GitHub API (PAT-based) to create branch commits and open pull requests
  when credentials are configured.
- Manages Helm `scheduleJobs` entries (including `enabled` pause/resume).
- Supports managed secrets with encrypted-at-rest storage plus env secret fallback.

10. **Hosted Documentation Site**
- Docusaurus app in `website/` with docs sourced from root `docs/`.
- OpenAPI schema exported to `website/static/openapi.json`.
- API docs rendered with Redoc in `/docs/api-reference`.
- CI docs build and OpenAPI drift checks gate merges.

## Data Lifecycle

1. Extract source records.
2. Normalize records to canonical NDJSON.
3. For pull connectors, compare against prior state to compute upserts/deletes.
4. For push connectors, process explicit delta operations from incoming events.
5. Publish artifacts to object storage.
6. Import upserts and apply deletes in Gemini.
7. Commit checkpoint + record state only on success.

This ordering guarantees that failed ingestion does not advance source checkpoints.

## Canonical Commands

Use these same commands across README, operations runbook, and automation:

```bash
gemini-sync-bridge run --connector connectors/hr-employees.yaml
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
```
