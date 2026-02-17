# Docs Evidence

## Updated Documentation

- `README.md`
- `docs/architecture.md`
- `docs/connector-mode-rest-pull.md`
- `docs/connector-provider-http.md`
- `docs/troubleshooting.md`
- `schemas/connector.docs-meta.yaml`
- `docs/connector-field-reference.md` (generated)

## Why Docs Were Required

- `gemini_sync_bridge/**` and `schemas/**` changed (`runtime_and_api` + `connector_contract` rules in `docs/doc_sync_map.yaml`).
- `evals/scenarios/**` changed (`governance_and_quality` rule).
- Updated docs now cover:
  - OAuth client-credentials contract for `rest_pull`.
  - Studio OAuth configuration behavior.
  - Token refresh and 401 retry behavior.
  - Troubleshooting for OAuth token endpoint and payload errors.

## Generation Step

- Ran: `./.venv/bin/python scripts/export_connector_reference.py`
- Output updated: `docs/connector-field-reference.md`
