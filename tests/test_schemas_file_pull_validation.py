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
