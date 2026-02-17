from __future__ import annotations

from gemini_sync_bridge.services.studio import validate_connector_draft


def _valid_sql_draft() -> dict:
    return {
        "metadata": {"name": "studio-hr"},
        "spec": {
            "mode": "sql_pull",
            "source": {
                "type": "postgres",
                "secretRef": "hr-db-credentials",
                "query": (
                    "SELECT employee_id, full_name, updated_at FROM employees "
                    "WHERE updated_at > :watermark"
                ),
                "watermarkField": "updated_at",
            },
            "mapping": {
                "idField": "employee_id",
                "titleField": "full_name",
                "contentTemplate": "{{ full_name }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": "studio-hr",
                "format": "ndjson",
            },
            "gemini": {
                "projectId": "my-project",
                "location": "global",
                "dataStoreId": "hr-ds",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "0 */3 * * *", "enabled": True},
    }


def _valid_oracle_sql_draft() -> dict:
    draft = _valid_sql_draft()
    draft["metadata"]["name"] = "studio-oracle"
    draft["spec"]["source"]["type"] = "oracle"
    draft["spec"]["source"]["secretRef"] = "oracle-hr-credentials"
    return draft


def test_validate_connector_draft_success() -> None:
    response = validate_connector_draft(_valid_sql_draft())
    assert response.valid is True
    assert response.errors == []


def test_validate_connector_draft_failure_returns_errors() -> None:
    draft = _valid_sql_draft()
    draft["metadata"]["name"] = "Invalid Name"

    response = validate_connector_draft(draft)
    assert response.valid is False
    assert response.errors


def _valid_rest_oauth_draft() -> dict:
    return {
        "metadata": {"name": "studio-kb"},
        "spec": {
            "mode": "rest_pull",
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
                    "clientSecretRef": "kb-oauth-client-secret",
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
                "prefix": "studio-kb",
                "format": "ndjson",
            },
            "gemini": {
                "projectId": "my-project",
                "location": "global",
                "dataStoreId": "kb-ds",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "*/30 * * * *", "enabled": True},
    }


def test_validate_connector_draft_accepts_rest_pull_oauth_client_credentials() -> None:
    response = validate_connector_draft(_valid_rest_oauth_draft())
    assert response.valid is True
    assert response.errors == []


def test_validate_connector_draft_rejects_invalid_oauth_config() -> None:
    draft = _valid_rest_oauth_draft()
    draft["spec"]["source"]["oauth"]["grantType"] = "password"

    response = validate_connector_draft(draft)
    assert response.valid is False
    assert response.errors


def test_validate_connector_draft_accepts_oracle_sql_pull() -> None:
    response = validate_connector_draft(_valid_oracle_sql_draft())
    assert response.valid is True
    assert response.errors == []


def test_validate_connector_draft_rejects_sql_pull_with_http_source_type() -> None:
    draft = _valid_sql_draft()
    draft["spec"]["source"]["type"] = "http"

    response = validate_connector_draft(draft)
    assert response.valid is False
    assert response.errors


def test_validate_connector_draft_rejects_rest_pull_with_non_http_source_type() -> None:
    draft = _valid_rest_oauth_draft()
    draft["spec"]["source"]["type"] = "oracle"

    response = validate_connector_draft(draft)
    assert response.valid is False
    assert response.errors


def test_validate_connector_draft_rejects_rest_push_with_non_http_source_type() -> None:
    draft = _valid_sql_draft()
    draft["metadata"]["name"] = "studio-push-oracle"
    draft["spec"]["mode"] = "rest_push"
    draft["spec"]["source"] = {
        "type": "oracle",
        "secretRef": "oracle-push-secret",
    }
    draft["schedule"]["cron"] = "*/5 * * * *"

    response = validate_connector_draft(draft)
    assert response.valid is False
    assert response.errors
