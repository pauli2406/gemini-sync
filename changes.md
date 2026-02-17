# Changes

## Runtime and Contract

- Added OAuth config model for `rest_pull` source in `gemini_sync_bridge/schemas.py`:
  - `grantType`, `tokenUrl`, `clientId`, `clientSecretRef`, `scopes`, `audience`, `clientAuthMethod`.
- Extended connector JSON schema in `schemas/connector.schema.json` with optional `spec.source.oauth` contract.
- Implemented OAuth client-credentials token provider in `gemini_sync_bridge/adapters/extractors.py`:
  - `client_secret_post` and `client_secret_basic`
  - token caching per run
  - proactive refresh within 30s expiry window
  - one forced refresh retry on 401
  - fallback secret resolution from `source.oauth.clientSecretRef` to `source.secretRef`
  - explicit extraction errors for invalid token endpoint responses.
- Preserved static bearer mode behavior for connectors without `source.oauth`.
- Enforced OAuth precedence: runtime OAuth `Authorization` header overrides static `source.headers.Authorization`.

## Studio

- Added REST pull auth controls to `gemini_sync_bridge/templates/studio/wizard.html`:
  - auth mode selector (`static_bearer`, `oauth_client_credentials`)
  - token URL, client ID, optional client secret ref, auth method, scopes, audience.
- Updated `gemini_sync_bridge/static/studio.js` to:
  - render mode/auth-mode visibility
  - parse/serialize `source.oauth`
  - validate required OAuth fields in wizard.
- Updated `gemini_sync_bridge/services/studio.py` mode-pruning:
  - remove `source.oauth` when mode is `sql_pull` or `rest_push`
  - preserve for `rest_pull`.

## Tests and Evals

- Added OAuth extractor test suite: `tests/test_extractors_rest_pull_oauth.py`.
- Added connector schema OAuth tests: `tests/test_connector_schema_oauth.py`.
- Extended Studio tests:
  - `tests/test_studio_ui.py`
  - `tests/test_studio_draft_validation.py`
  - `tests/test_studio_proposal_generation.py`
- Added scenario: `evals/scenarios/rest-pull-oauth-client-credentials.yaml`.
- Registered scenario in `evals/eval_registry.yaml`.

## Docs

- Updated:
  - `README.md`
  - `docs/architecture.md`
  - `docs/connector-mode-rest-pull.md`
  - `docs/connector-provider-http.md`
  - `docs/troubleshooting.md`
  - `schemas/connector.docs-meta.yaml`
- Regenerated:
  - `docs/connector-field-reference.md` via `python scripts/export_connector_reference.py`.

## Security Notes

- No secrets or tokens are logged or persisted in new runtime error messages.
- Existing secret resolution path is reused (`resolve_secret`).
