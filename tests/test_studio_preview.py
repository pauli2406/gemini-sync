from __future__ import annotations

import pytest

from ingest_relay.services.studio import preview_connector_draft


def test_preview_connector_draft_renders_sample_document() -> None:
    draft = {
        "metadata": {"name": "preview-kb"},
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
                "prefix": "preview-kb",
                "format": "ndjson",
            },
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "*/30 * * * *", "enabled": True},
    }

    sample = {
        "article_id": "a-1",
        "title": "VPN",
        "body": "Issue details",
        "updated_at": "2026-02-16T08:30:00Z",
    }

    response = preview_connector_draft(draft=draft, sample_record=sample)

    assert response.preview_document.doc_id == "preview-kb:a-1"
    assert "VPN" in response.preview_document.content
    assert response.preview_document.uri == "https://kb.local/articles/a-1"


def test_preview_connector_draft_auto_fills_missing_template_fields() -> None:
    draft = {
        "metadata": {"name": "preview-hr"},
        "spec": {
            "mode": "sql_pull",
            "source": {
                "type": "postgres",
                "secretRef": "hr-db-credentials",
                "query": "SELECT * FROM employees WHERE updated_at > :watermark",
                "watermarkField": "updated_at",
            },
            "mapping": {
                "idField": "employee_id",
                "titleField": "full_name",
                "contentTemplate": "{{ department }} {{ role }} {{ bio }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": "preview-hr",
                "format": "ndjson",
            },
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "0 */3 * * *", "enabled": True},
    }

    response = preview_connector_draft(draft=draft, sample_record=None)
    assert "sample-department" in response.preview_document.content
    assert "sample-role" in response.preview_document.content
    assert "sample-bio" in response.preview_document.content


def test_preview_connector_draft_returns_clear_error_for_invalid_nested_template() -> None:
    draft = {
        "metadata": {"name": "preview-bad"},
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
                "contentTemplate": "{{ department.name }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": "preview-bad",
                "format": "ndjson",
            },
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "*/30 * * * *", "enabled": True},
    }

    with pytest.raises(ValueError, match="Unable to render content template"):
        preview_connector_draft(draft=draft, sample_record=None)
