# Docs Evidence

## Updated Documentation

- `.env.example`
- `README.md`
- `docs/operations-runbook.md`
- `docs/connector-provider-http.md`
- `docs/troubleshooting.md`

## Why Docs Were Required

- Runtime files changed under `gemini_sync_bridge/**` (`runtime_and_api` docs drift rule).
- Eval files changed under `evals/**` (`governance_and_quality` docs drift rule).
- Operators need explicit proxy and CA configuration guidance for enterprise deployments.

## Coverage Added

- Standard env proxy contract:
  - `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
- Custom CA env contract:
  - `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`
- Outbound egress coverage clarification:
  - REST pull/OAuth, Gemini ingestion, Splunk/Teams webhooks, GitHub PR API
- Troubleshooting for:
  - `407 Proxy Authentication Required`
  - TLS certificate verification failures behind enterprise proxy
  - `NO_PROXY` routing mistakes
