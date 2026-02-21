# Changes

## Files Changed

- Package/module hard cutover:
  - renamed `gemini_sync_bridge/` -> `ingest_relay/`
  - updated imports and dotted runtime references across runtime, scripts, and tests
- Packaging/runtime entrypoints:
  - `pyproject.toml` (`ingest_relay.cli:app`, wheel package/include paths)
  - `ingest_relay/cli.py` (`uvicorn.run("ingest_relay.api:app", ...)`)
  - `Dockerfile` (`COPY ingest_relay /app/ingest_relay`)
- Governance/gate mappings:
  - `ingest_relay/quality_gates.py`
  - `.agent/risk_policy.yaml`
  - `docs/doc_sync_map.yaml`
- CI/docs workflow and coverage references:
  - `.github/workflows/ci.yaml`
  - `.github/workflows/release-canary.yaml`
  - `.github/workflows/docs-deploy-vercel.yaml`
  - `.github/pull_request_template.md`
  - `README.md`, `CONTRIBUTING.md`, `llm.txt`, `docs/contributing/testing-ci.mdx`, `test_evidence.md`
- Active documentation/code path updates:
  - `docs/reference/api-reference.mdx`
  - `runtime/README.md`
  - `docs_evidence.md`, `task.md`, `changes.md`

## Behavior Changes

- Python import namespace is now `ingest_relay` (hard cutover).
- CLI package entrypoint now resolves to `ingest_relay.cli:app`.
- CI coverage target now measures `ingest_relay`.
- Docs deploy workflow now tracks `ingest_relay/api.py` for OpenAPI/docs-triggered deploys.

## Non-Functional Changes

- Historical records under `.agent/tasks/*` intentionally left unchanged.
- Existing stage-1 product branding (`IngestRelay`, `ingest-relay`) preserved.
- OpenAPI artifact regenerated and connector reference drift revalidated post-cutover.
