# Changes

## Runtime

- Added shared outbound HTTP client helper:
  - `gemini_sync_bridge/utils/http_clients.py`
  - `create_httpx_client(**kwargs)` forces `trust_env=True` while preserving caller kwargs.
- Updated outbound call sites to use shared helper:
  - `gemini_sync_bridge/adapters/extractors.py`
  - `gemini_sync_bridge/services/observability.py`
  - `gemini_sync_bridge/services/github_pr.py`
- Updated Gemini ingestion session construction:
  - `gemini_sync_bridge/services/gemini_ingestion.py`
  - Explicitly sets `AuthorizedSession.trust_env = True`.

## Tests and Evals

- Added proxy regression tests:
  - `tests/test_outbound_proxy_support.py`
- Added new scenario eval:
  - `evals/scenarios/outbound-proxy-env-support.yaml`
- Registered scenario:
  - `evals/eval_registry.yaml`

## Documentation

- Added optional proxy/CA contract in:
  - `.env.example`
- Added outbound proxy support section in:
  - `README.md`
- Added deployment + verification guidance in:
  - `docs/operations-runbook.md`
- Added provider-specific proxy notes in:
  - `docs/connector-provider-http.md`
- Added proxy troubleshooting sections in:
  - `docs/troubleshooting.md`

## Contract Compatibility

- No changes to connector YAML schema:
  - `schemas/connector.schema.json` unchanged.
- No new API endpoints or request/response changes.
