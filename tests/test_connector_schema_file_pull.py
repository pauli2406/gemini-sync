from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _schema() -> dict:
    return json.loads(Path("schemas/connector.schema.json").read_text(encoding="utf-8"))


def _valid_file_pull_connector() -> dict:
    return {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "hr-file-csv"},
        "spec": {
            "mode": "file_pull",
            "schedule": "0 */2 * * *",
            "source": {
                "type": "file",
                "path": "./runtime/sources/hr",
                "glob": "*.csv",
                "format": "csv",
                "watermarkField": "updated_at",
                "csv": {
                    "documentMode": "row",
                    "delimiter": ",",
                    "hasHeader": True,
                    "encoding": "utf-8",
                },
            },
            "mapping": {
                "idField": "employee_id",
                "titleField": "full_name",
                "contentTemplate": "{{ full_name }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": "hr-file-csv",
                "format": "ndjson",
            },
            "gemini": {
                "projectId": "my-project",
                "location": "global",
                "dataStoreId": "hr-ds",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }


def test_connector_schema_accepts_file_pull_with_optional_secret_ref() -> None:
    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(_valid_file_pull_connector()))
    assert errors == []


def test_connector_schema_rejects_file_pull_missing_path() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"]["source"].pop("path")

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("path" in err.message for err in errors)


def test_connector_schema_rejects_file_pull_with_non_file_source_type() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"]["source"]["type"] = "http"

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("file" in err.message for err in errors)


def test_connector_schema_rejects_invalid_csv_delimiter_length() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"]["source"]["csv"]["delimiter"] = "||"

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("is too long" in err.message or "maxLength" in err.message for err in errors)


def test_connector_schema_accepts_csv_normalize_headers_and_clean_errors() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"]["source"]["csv"]["normalizeHeaders"] = True
    payload["spec"]["source"]["csv"]["cleanErrors"] = True

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))
    assert errors == []


def test_connector_schema_accepts_ingestion_disabled_without_gemini() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"].pop("gemini")
    payload["spec"]["ingestion"] = {"enabled": False}

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors == []


def test_connector_schema_rejects_missing_gemini_when_ingestion_enabled() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"].pop("gemini")

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("gemini" in err.message for err in errors)


def test_connector_schema_accepts_output_publish_latest_alias() -> None:
    payload = _valid_file_pull_connector()
    payload["spec"]["output"]["publishLatestAlias"] = True

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors == []


def test_connector_schema_accepts_sql_pull_csv_export_without_mapping() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "oracle-csv"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "0 */2 * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-csv-credentials",
                "query": "SELECT 1 AS id",
            },
            "output": {
                "bucket": "gs://local-bucket",
                "prefix": "oracle-csv",
                "format": "csv",
                "publishLatestAlias": True,
            },
            "ingestion": {"enabled": False},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors == []


def test_connector_schema_rejects_csv_export_without_explicit_ingestion_false() -> None:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": "oracle-csv"},
        "spec": {
            "mode": "sql_pull",
            "schedule": "0 */2 * * *",
            "source": {
                "type": "oracle",
                "secretRef": "oracle-csv-credentials",
                "query": "SELECT 1 AS id",
            },
            "output": {
                "bucket": "gs://local-bucket",
                "prefix": "oracle-csv",
                "format": "csv",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    validator = jsonschema.Draft202012Validator(_schema())
    errors = list(validator.iter_errors(payload))

    assert errors
    assert any("ingestion" in err.message or "required property" in err.message for err in errors)
