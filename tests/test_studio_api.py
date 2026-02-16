from __future__ import annotations


def _valid_rest_draft(name: str = "api-kb") -> dict:
    return {
        "metadata": {"name": name},
        "spec": {
            "mode": "rest_pull",
            "source": {
                "type": "http",
                "secretRef": "kb-api-token",
                "url": "https://kb.local/articles",
                "method": "GET",
                "watermarkField": "updated_at",
            },
            "mapping": {
                "idField": "article_id",
                "titleField": "title",
                "contentTemplate": "{{ title }} {{ body }}",
                "uriTemplate": "https://kb.local/articles/{{ article_id }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": name,
                "format": "ndjson",
            },
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "*/30 * * * *", "enabled": True},
    }


def test_studio_catalog_endpoint_returns_items(client) -> None:
    response = client.get("/v1/studio/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload


def test_studio_validate_endpoint_returns_valid_payload(client) -> None:
    draft = {
        "metadata": {"name": "api-hr"},
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
                "prefix": "api-hr",
                "format": "ndjson",
            },
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "0 */3 * * *", "enabled": True},
    }

    response = client.post("/v1/studio/connectors/validate", json={"draft": draft})
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_studio_secrets_create_and_list(client) -> None:
    create = client.post(
        "/v1/studio/secrets",
        json={"secret_ref": "studio-secret", "secret_value": "token-123"},
    )
    assert create.status_code == 200

    listed = client.get("/v1/studio/secrets")
    assert listed.status_code == 200
    refs = [row["secret_ref"] for row in listed.json()["items"]]
    assert "studio-secret" in refs


def test_studio_connector_editor_returns_404_for_unknown_connector(client) -> None:
    response = client.get("/v1/studio/connectors/unknown-connector")
    assert response.status_code == 404


def test_studio_preview_endpoint_returns_document(client) -> None:
    response = client.post(
        "/v1/studio/connectors/preview",
        json={
            "draft": _valid_rest_draft(),
            "sample_record": {
                "article_id": "a-100",
                "title": "VPN",
                "body": "Troubleshooting",
                "updated_at": "2026-02-16T08:30:00Z",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_document"]["doc_id"] == "api-kb:a-100"


def test_studio_preview_endpoint_returns_400_for_invalid_template(client) -> None:
    draft = _valid_rest_draft(name="api-bad-template")
    draft["spec"]["mapping"]["contentTemplate"] = "{{ department.name }}"

    response = client.post("/v1/studio/connectors/preview", json={"draft": draft})
    assert response.status_code == 400
    assert "Unable to render content template" in response.json()["detail"]


def test_studio_propose_endpoint_returns_400_for_invalid_pause_request(client) -> None:
    response = client.post(
        "/v1/studio/connectors/propose",
        json={"action": "pause", "connector_id": "unknown-connector"},
    )
    assert response.status_code == 400
    assert "No schedule job found" in response.json()["detail"]
