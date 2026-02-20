from __future__ import annotations

import pytest

from gemini_sync_bridge.schemas import ConnectorConfig, SourceConfig


def _base_connector_spec() -> dict:
    return {
        "mapping": {
            "idField": "id",
            "titleField": "title",
            "contentTemplate": "{{ title }}",
        },
        "output": {
            "bucket": "file://./local-bucket",
            "prefix": "sample",
            "format": "ndjson",
        },
        "gemini": {
            "projectId": "my-project",
            "location": "global",
            "dataStoreId": "sample-ds",
        },
        "reconciliation": {"deletePolicy": "auto_delete_missing"},
    }


def _validate(mode: str, source: dict, schedule: str | None = "*/30 * * * *") -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "sample"},
        "spec": {
            "mode": mode,
            "schedule": schedule,
            "source": source,
            **_base_connector_spec(),
        },
    }
    ConnectorConfig.model_validate(payload)


def test_csv_config_validator_rejects_multi_character_delimiter() -> None:
    with pytest.raises(ValueError, match="single character"):
        SourceConfig.model_validate(
            {
                "type": "file",
                "path": "./runtime/sources/hr",
                "glob": "*.csv",
                "format": "csv",
                "csv": {
                    "documentMode": "row",
                    "delimiter": "||",
                    "hasHeader": True,
                    "encoding": "utf-8",
                },
            }
        )


def test_sql_pull_requires_secret_ref() -> None:
    with pytest.raises(ValueError, match="source.secretRef is required for sql_pull mode"):
        _validate(
            "sql_pull",
            {
                "type": "postgres",
                "query": "SELECT 1",
            },
        )


def test_rest_pull_requires_secret_ref() -> None:
    with pytest.raises(ValueError, match="source.secretRef is required for rest_pull mode"):
        _validate(
            "rest_pull",
            {
                "type": "http",
                "url": "https://api.local/items",
            },
        )


def test_rest_push_requires_secret_ref() -> None:
    with pytest.raises(ValueError, match="source.secretRef is required for rest_push mode"):
        _validate(
            "rest_push",
            {
                "type": "http",
            },
            schedule=None,
        )


def test_file_pull_requires_file_source_type() -> None:
    with pytest.raises(ValueError, match="source.type must be file for file_pull mode"):
        _validate(
            "file_pull",
            {
                "type": "http",
                "path": "./runtime/sources/hr",
                "glob": "*.csv",
                "format": "csv",
                "csv": {"documentMode": "row"},
            },
        )


def test_file_pull_requires_glob() -> None:
    with pytest.raises(ValueError, match="source.glob is required for file_pull mode"):
        _validate(
            "file_pull",
            {
                "type": "file",
                "path": "./runtime/sources/hr",
                "format": "csv",
                "csv": {"documentMode": "row"},
            },
        )


def test_file_pull_requires_csv_format() -> None:
    with pytest.raises(ValueError, match="source.format must be csv for file_pull mode"):
        _validate(
            "file_pull",
            {
                "type": "file",
                "path": "./runtime/sources/hr",
                "glob": "*.csv",
                "format": None,
                "csv": {"documentMode": "row"},
            },
        )


def test_file_pull_requires_csv_block() -> None:
    with pytest.raises(ValueError, match="source.csv is required for file_pull mode"):
        _validate(
            "file_pull",
            {
                "type": "file",
                "path": "./runtime/sources/hr",
                "glob": "*.csv",
                "format": "csv",
            },
        )


def test_connector_config_allows_missing_gemini_when_ingestion_disabled() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "sample"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "*/30 * * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-sample-credentials",
                "query": "SELECT 1 AS id, 'title' AS title",
            },
            "mapping": {
                "idField": "id",
                "titleField": "title",
                "contentTemplate": "{{ title }}",
            },
            "output": {
                "bucket": "gs://sample-bucket",
                "prefix": "sample",
                "format": "ndjson",
                "publishLatestAlias": True,
            },
            "ingestion": {"enabled": False},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    connector = ConnectorConfig.model_validate(payload)
    assert connector.spec.gemini is None
    assert connector.spec.ingestion.enabled is False
    assert connector.spec.output.publish_latest_alias is True


def test_connector_config_requires_gemini_when_ingestion_enabled() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "sample"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "*/30 * * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-sample-credentials",
                "query": "SELECT 1 AS id, 'title' AS title",
            },
            "mapping": {
                "idField": "id",
                "titleField": "title",
                "contentTemplate": "{{ title }}",
            },
            "output": {
                "bucket": "gs://sample-bucket",
                "prefix": "sample",
                "format": "ndjson",
            },
            "ingestion": {"enabled": True},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    with pytest.raises(
        ValueError,
        match="spec.gemini is required when spec.ingestion.enabled is true",
    ):
        ConnectorConfig.model_validate(payload)


def test_connector_config_allows_sql_pull_csv_export_without_mapping() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "sample"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "*/30 * * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-sample-credentials",
                "query": "SELECT 1 AS id, 'title' AS title",
            },
            "output": {
                "bucket": "gs://sample-bucket",
                "prefix": "sample",
                "format": "csv",
                "publishLatestAlias": True,
            },
            "ingestion": {"enabled": False},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    connector = ConnectorConfig.model_validate(payload)
    assert connector.spec.mapping is None
    assert connector.spec.output.format == "csv"
    assert connector.spec.ingestion.enabled is False


def test_connector_config_rejects_sql_pull_csv_export_with_ingestion_enabled() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "sample"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "*/30 * * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-sample-credentials",
                "query": "SELECT 1 AS id, 'title' AS title",
            },
            "output": {
                "bucket": "gs://sample-bucket",
                "prefix": "sample",
                "format": "csv",
            },
            "ingestion": {"enabled": True},
            "gemini": {
                "projectId": "my-project",
                "location": "global",
                "dataStoreId": "sample-ds",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    with pytest.raises(
        ValueError,
        match="spec.ingestion.enabled must be false when spec.output.format is csv",
    ):
        ConnectorConfig.model_validate(payload)
