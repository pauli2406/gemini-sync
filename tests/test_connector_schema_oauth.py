from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _schema() -> dict:
    return json.loads(Path("schemas/connector.schema.json").read_text(encoding="utf-8"))


def _valid_connector_with_oauth() -> dict:
    return {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "kb-rest-oauth"},
        "spec": {
            "mode": "rest_pull",
            "schedule": "*/30 * * * *",
            "source": {
                "type": "http",
                "secretRef": "kb-api-token",
                "url": "https://kb.local/articles",
                "method": "GET",
                "watermarkField": "updated_at",
                "oauth": {
                    "grantType": "client_credentials",
                    "tokenUrl": "https://auth.local/realms/acme/protocol/openid-connect/token",
                    "clientId": "bridge-client",
                    "clientSecretRef": "oauth-client-secret",
                    "scopes": ["api.read"],
                    "audience": "knowledge-api",
                    "clientAuthMethod": "client_secret_post",
                },
            },
            "mapping": {
                "idField": "article_id",
                "titleField": "title",
                "contentTemplate": "{{ title }} {{ body }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": "kb-rest-oauth",
                "format": "ndjson",
            },
            "gemini": {
                "projectId": "my-project",
                "location": "global",
                "dataStoreId": "kb-ds",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }


def test_connector_schema_accepts_rest_pull_oauth_client_credentials() -> None:
    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(_valid_connector_with_oauth()))
    assert errors == []


def test_connector_schema_rejects_invalid_oauth_grant_type() -> None:
    payload = _valid_connector_with_oauth()
    payload["spec"]["source"]["oauth"]["grantType"] = "password"

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("client_credentials" in err.message for err in errors)
