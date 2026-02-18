# Gemini Sync Bridge

Gemini Sync Bridge is an open-source ingestion bridge for syncing enterprise source systems into Google Cloud Storage and Discovery Engine data stores used by Gemini Enterprise.

It combines connector execution, reconciliation, artifact publishing, ingestion, and operator visibility in one GitOps-friendly runtime.

## Two-Minute Pitch

- Build connectors once, run them in a repeatable contract-driven runtime.
- Support four connector modes: `sql_pull`, `rest_pull`, `rest_push`, `file_pull`.
- Preserve deterministic upsert/delete behavior through canonical NDJSON artifacts.
- Operate with clear visibility in Ops UI and guided authoring in Connector Studio.
- Enforce governance gates (tests, docs drift, security, evals) before merge.

## Minimal Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
docker compose up -d postgres
gemini-sync-bridge init-db
python scripts/validate_connectors.py
gemini-sync-bridge run --connector connectors/hr-employees-local.yaml
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
```

Open:

- Ops: `http://localhost:8080/ops`
- Studio: `http://localhost:8080/studio/connectors`

## Audience Paths

### Operators

- Start hub: `docs/start-here.mdx`
- Local tutorial: `docs/tutorials/getting-started-local.mdx`
- Runbook: `docs/how-to/operate-runs.mdx`
- Troubleshooting: `docs/how-to/troubleshooting.mdx`

### Contributors

- Architecture: `docs/concepts/architecture.mdx`
- Authoring: `docs/how-to/connector-authoring.mdx`
- CI gates: `docs/contributing/testing-ci.mdx`
- Agent contract: `AGENTS.md` and `llm.txt`

## Docusaurus Docs Site

- Docs source: `docs/`
- Site app: `website/`
- Main categories: Tutorials, How-to, Concepts, Reference, Contributing

Local docs workflow:

```bash
python scripts/export_openapi.py
python scripts/export_connector_reference.py
npm --prefix website ci
npm --prefix website run build
npm --prefix website run start
```

## Connector Storage Model

- Keep this runtime repository focused on code, docs, tests, and curated connector examples.
- Keep environment-specific connectors in a separate connector-config repository.
- Set `CONNECTORS_DIR` so API/Ops/Studio discover external connector files.

Example:

```bash
export CONNECTORS_DIR=/opt/gemini-sync/connectors
gemini-sync-bridge serve --host 0.0.0.0 --port 8080
gemini-sync-bridge run --connector /opt/gemini-sync/connectors/hr-employees.yaml
```

## Governance Gates Summary

Run these gates before PR:

```bash
python scripts/validate_connectors.py
python scripts/check_connector_examples_allowlist_drift.py
python scripts/check_connector_examples_only.py
ruff check .
python scripts/check_tdd_guardrails.py
python scripts/check_docs_drift.py
python scripts/check_openapi_drift.py
python scripts/check_connector_reference_drift.py
python scripts/check_security_policy.py
python scripts/run_dependency_audit.py
pytest --cov=gemini_sync_bridge --cov-report=xml --cov-fail-under=60
diff-cover coverage.xml --compare-branch=origin/main --fail-under=92
python scripts/run_scenario_evals.py --registry evals/eval_registry.yaml --baseline evals/baseline.json
npm --prefix website run build
```

## Repository Layout

- `gemini_sync_bridge/`: runtime, API, and services
- `connectors/`: curated sample connectors
- `schemas/`: connector schema and docs metadata
- `scripts/`: quality gates, exports, and tooling
- `evals/`: scenario registry and eval definitions
- `docs/`: Diataxis documentation content
- `website/`: Docusaurus application

## License

Apache-2.0
