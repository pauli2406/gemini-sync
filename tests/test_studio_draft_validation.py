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
