# Operations Runbook

## Health Checks

- API: `GET /healthz`
- Database: verify connectivity and row growth in `run_state`
- Scheduler: verify Kestra trigger executions

## Failure Handling

When a run fails:

1. Inspect run in Kestra UI.
2. Locate matching `run_id` in Splunk events.
3. Verify connector source reachability and secret validity.
4. Re-run job manually after fix.

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
