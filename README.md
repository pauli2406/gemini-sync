# Gemini Sync Bridge

Gemini Sync Bridge is an open-source, GitOps-managed integration layer for syncing on-prem SQL/REST data into Google Cloud Storage (single cloud handoff) and ingesting it into Gemini Enterprise data stores.

Agentic development is governed by `AGENTS.md` and roadmap outcomes are tracked in `docs/roadmap.md`.

## What v1 Includes

- Connector definitions in Git (`connectors/*.yaml`) validated by JSON Schema.
- Python runtime with three connector modes:
  - `sql_pull`
  - `rest_pull`
  - `rest_push`
- `rest_pull` authentication supports:
  - static bearer token from `spec.source.secretRef`
  - OAuth client credentials (`spec.source.oauth`) with token refresh and 401 retry
- Canonical NDJSON document envelope with deterministic checksums.
- Reconciliation engine that computes upserts and deletes (`auto_delete_missing`).
- Artifact publishing to GCS (`gs://`) or local filesystem (`file://`) for development.
- Discovery import artifact generation (`upserts.discovery.ndjson`) for
  `CONTENT_REQUIRED` data stores.
- Gemini ingestion worker using Discovery Engine APIs (or dry-run mode).
- Push API with idempotency semantics:
  - `POST /v1/connectors/{connector_id}/events`
  - Required header: `Idempotency-Key`
  - Push events are treated as delta operations (`op=UPSERT` or `op=DELETE`)
- Read-only operations UI for run visibility:
  - `GET /ops`
  - `GET /ops/connectors/{connector_id}`
  - `GET /ops/runs/{run_id}`
  - JSON polling endpoints under `/v1/ops/*` with run filters and pagination
  - Optional run log deep links to Splunk and Kestra (`SPLUNK_RUN_URL_TEMPLATE`, `KESTRA_RUN_URL_TEMPLATE`)
- Connector Studio (guided authoring and lifecycle management):
  - `GET /studio/connectors`
  - `GET /studio/connectors/new`
  - `GET /v1/studio/*` JSON APIs for validate/preview/propose/secrets/run-now
  - `POST /v1/studio/connectors/propose` creates a GitHub branch + PR when
    `GITHUB_TOKEN` and `GITHUB_REPO` are configured; otherwise it returns a
    local proposal URL for offline workflows
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

## Getting Started Guides

- Full local setup (Docker Postgres + sample source data + first successful run):
  `docs/getting-started-local.mdx`
- Full end-to-end GCP onboarding (datastore + IAM + import verification):
  `docs/discovery-engine-cli-playbook.md`

## Connector Setup Docs

- Hub: `docs/connector-authoring.md`
- SQL Pull: `docs/connector-mode-sql-pull.md`
- REST Pull: `docs/connector-mode-rest-pull.md`
- REST Push: `docs/connector-mode-rest-push.md`
- Field reference (generated): `docs/connector-field-reference.md`
- Providers:
  - `docs/connector-provider-postgres.md`
  - `docs/connector-provider-mysql.md`
  - `docs/connector-provider-mssql.md`
  - `docs/connector-provider-oracle.md`
  - `docs/connector-provider-http.md`
  - `docs/connector-provider-future.md`

## Hosted Documentation

- Production docs URL (Vercel): `https://gemini-sync-bridge-docs.vercel.app`
- Docs source: `docs/`
- Docs app: `website/`
- Homepage styling is tuned for both light and dark mode readability.

Local docs workflow:

```bash
python scripts/export_openapi.py
python scripts/export_connector_reference.py
npm --prefix website ci
npm --prefix website run build
npm --prefix website run start
```

Automated deploy workflow:

- `.github/workflows/docs-deploy-vercel.yaml`
- Required repo secrets:
  - `VERCEL_TOKEN`
  - `VERCEL_ORG_ID`
  - `VERCEL_PROJECT_ID`

## Quickstart (Local)

Use the full onboarding guide for first-time setup:

- `docs/getting-started-local.mdx`

Fast path (after first-time setup):

```bash
source .venv/bin/activate
docker compose up -d postgres
cp .env.example .env
gemini-sync-bridge init-db
python scripts/validate_connectors.py
gemini-sync-bridge run --connector connectors/hr-employees-local.yaml
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
```

Open the UIs:

- Ops dashboard: `http://localhost:8080/ops`
- Connector detail: `http://localhost:8080/ops/connectors/hr-employees-local`
- Connector Studio: `http://localhost:8080/studio/connectors`

Optional local governance gates:

```bash
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
python scripts/check_openapi_drift.py
python scripts/check_connector_reference_drift.py
python scripts/check_security_policy.py
python scripts/run_dependency_audit.py
python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
python scripts/performance_smoke.py --records 1000 --max-seconds 2.0
```

Reliability-phase commands:

```bash
python scripts/replay_run_artifacts.py --upserts file://./local-bucket/connectors/hr-employees-local/runs/<run_id>/upserts.ndjson --deletes file://./local-bucket/connectors/hr-employees-local/runs/<run_id>/deletes.ndjson
python scripts/generate_slo_report.py --database-url \"$DATABASE_URL\" --output slo-metrics.json
python scripts/check_slo_gate.py --metrics slo-metrics.json
```

## CI Checks

- Connector schema validation
- Pytest suite
- Ruff linting
- TDD/EDD changed-files guardrails
- Docs drift and docs consistency checks
- Connector field reference drift check
- Diff coverage enforcement
- Security policy validation, secret scanning, and dependency audit

## Production Notes

- Keep `GEMINI_INGESTION_DRY_RUN=false` only in environments with valid Google credentials and quota controls.
- Use Kubernetes Secrets to provide `SECRET_<SECRETREF>` values.
- Run this service in a private network segment with access to on-prem systems and controlled egress to GCP.
- Canonical runtime command: `gemini-sync-bridge run --connector connectors/hr-employees.yaml`
- Canonical API command: `gemini-sync-bridge serve --host 0.0.0.0 --port 8080`
- Governance gate commands: `python scripts/check_tdd_guardrails.py` and `python scripts/check_docs_drift.py`
- OpenAPI drift gate command: `python scripts/check_openapi_drift.py`

## License

Apache-2.0
