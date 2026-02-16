# Operations Runbook

## Health Checks

- API: `GET /healthz`
- Ops UI: `GET /ops` (dashboard), `GET /ops/connectors/{connector_id}`, `GET /ops/runs/{run_id}`
- Ops API: `GET /v1/ops/snapshot`, `GET /v1/ops/connectors/{connector_id}`, `GET /v1/ops/runs/{run_id}`
- Snapshot API filters/pagination: `status`, `connector_id`, `window_hours`, `limit_runs`, `offset_runs`
- Database: verify connectivity and row growth in `run_state`
- Scheduler: verify Kestra trigger executions

## Failure Handling

When a run fails:

1. Inspect run in Ops UI (`/ops/runs/{run_id}`) and Kestra UI.
2. Locate matching `run_id` in Splunk events.
3. Verify connector source reachability and secret validity.
4. Re-run job manually after fix.

Configure optional deep links in `.env`:

- `SPLUNK_RUN_URL_TEMPLATE=https://splunk.example/search?q={run_id}`
- `KESTRA_RUN_URL_TEMPLATE=https://kestra.example/executions/{run_id}`

## Replay and Recovery

- Pull connectors: rerun connector; unchanged records are deduplicated by checksum.
- Push connectors: if API accepted events, pending batch can be replayed by rerunning the connector job.

## Alerting

- Teams alert is emitted when pipeline run status transitions to FAILED.
- Splunk HEC receives structured events for both success and failure.

## SLO Reporting (Suggested)

- Success rate over 7 days (`run_state.status`).
- Freshness lag (`now - connector_checkpoints.updated_at`).
- MTTR (`failure time` to next successful run).

## Canonical Commands

```bash
gemini-sync-bridge run --connector connectors/hr-employees.yaml
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
```

## Reliability Commands

```bash
python scripts/replay_run_artifacts.py --upserts <upserts-ndjson> --deletes <deletes-ndjson>
python scripts/generate_slo_report.py --database-url "$DATABASE_URL" --output slo-metrics.json
python scripts/check_slo_gate.py --metrics slo-metrics.json
```
