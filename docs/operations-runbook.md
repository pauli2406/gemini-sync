# Operations Runbook

## Health Checks

- API: `GET /healthz`
- Ops UI: `GET /ops` (dashboard), `GET /ops/connectors/{connector_id}`, `GET /ops/runs/{run_id}`
- Ops API: `GET /v1/ops/snapshot`, `GET /v1/ops/connectors/{connector_id}`, `GET /v1/ops/runs/{run_id}`
- Snapshot API filters/pagination: `status`, `connector_id`, `window_hours`, `limit_runs`, `offset_runs`
- Connector Studio UI: `GET /studio/connectors`
- Connector Studio APIs: `GET /v1/studio/catalog`, `POST /v1/studio/connectors/propose`, `POST /v1/studio/connectors/{connector_id}/run-now`
- Proposal endpoint behavior:
  - With `GITHUB_TOKEN` + `GITHUB_REPO`: creates branch commits and opens a PR in the connector-config repository.
  - Without GitHub credentials: returns a local proposal URL (`local://proposal/...`).
- Database: verify connectivity and row growth in `run_state`
- Scheduler: verify Kestra trigger executions

## Discovery Engine Onboarding

For the complete CLI workflow to onboard additional data stores/connectors, use:

- `docs/discovery-engine-cli-playbook.md`

For migrations from legacy staging setups where custom connectors were stored in
this runtime repo, use:

- `docs/migration-custom-connectors.md`

For deletion/cleanup of test data stores, use the same playbook section:

- `Delete a Test Data Store`

## Outbound Proxy Configuration

Bridge outbound HTTP clients use standard environment variables for proxy and CA trust:

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `NO_PROXY`
- `SSL_CERT_FILE`
- `REQUESTS_CA_BUNDLE`

Recommended deployment baseline:

1. Set `HTTP_PROXY` and `HTTPS_PROXY` to enterprise proxy endpoints.
2. Set `NO_PROXY` to include local/internal addresses (`localhost`, `127.0.0.1`, `postgres`, `.internal`).
3. Set `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` to the same enterprise CA bundle path when TLS interception/custom trust is required.
4. Restart bridge runtime after env updates.

Verification checklist:

1. Run one `rest_pull` connector with static bearer and confirm run success.
2. Run one `rest_pull` connector with OAuth client-credentials and confirm token acquisition + data pull.
3. Trigger one connector failure and verify Teams/Splunk webhook delivery.
4. Submit one Studio proposal with GitHub credentials enabled and verify PR creation.
5. Verify Gemini ingestion run success (`GEMINI_INGESTION_DRY_RUN=false` in staging/prod).

## Failure Handling

When a run fails:

1. Inspect run in Ops UI (`/ops/runs/{run_id}`) and Kestra UI.
2. Locate matching `run_id` in Splunk events.
3. Verify connector source reachability and secret validity.
4. Re-run job manually after fix.

Configure optional deep links in `.env`:

- `SPLUNK_RUN_URL_TEMPLATE=https://splunk.example/search?q={run_id}`
- `KESTRA_RUN_URL_TEMPLATE=https://kestra.example/executions/{run_id}`
- `MANAGED_SECRET_ENCRYPTION_KEY=<strong-random-key>`
- `GITHUB_TOKEN=<github-pat>`
- `GITHUB_REPO=org/connector-config-repo`
- `GITHUB_BASE_BRANCH=main`

Configure connector discovery for API/Ops/Studio:

- `CONNECTORS_DIR=/srv/gemini-sync/connectors`
- Default when unset: `connectors` (repo-local sample directory)
- Recommendation: keep user-specific connectors outside this runtime repo.

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
python scripts/check_connector_examples_only.py
```

## Reliability Commands

```bash
python scripts/replay_run_artifacts.py --upserts <upserts-ndjson> --deletes <deletes-ndjson>
python scripts/generate_slo_report.py --database-url "$DATABASE_URL" --output slo-metrics.json
python scripts/check_slo_gate.py --metrics slo-metrics.json
```

## Docs Site Commands

```bash
python scripts/export_openapi.py
python scripts/check_openapi_drift.py
npm --prefix website ci
npm --prefix website run build
```

Vercel deploy automation:

- Workflow: `.github/workflows/docs-deploy-vercel.yaml`
- Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
