from __future__ import annotations

from pathlib import Path

import yaml


def _load_connector(path: str) -> dict:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_hr_employees_sample_connector_sql_contract() -> None:
    connector = _load_connector("connectors/hr-employees.yaml")
    assert connector["metadata"]["name"] == "hr-employees"
    assert connector["spec"]["mode"] == "sql_pull"

    source = connector["spec"]["source"]
    assert source["type"] == "postgres"
    assert source["secretRef"] == "hr-db-credentials"
    assert source["watermarkField"] == "updated_at"
    query = source["query"]
    assert ":watermark" not in query
    assert "FROM employees" in query
    assert "SELECT * FROM source_table" not in query

    mapping = connector["spec"]["mapping"]
    assert mapping["idField"] == "employee_id"
    assert mapping["titleField"] == "full_name"
    assert mapping["aclUsersField"] == "allowed_users"
    assert mapping["aclGroupsField"] == "allowed_groups"

    output = connector["spec"]["output"]
    assert output["bucket"].startswith("gs://")
    assert output["prefix"] == "hr-employees"

    reconciliation = connector["spec"]["reconciliation"]
    assert reconciliation["deletePolicy"] == "auto_delete_missing"


def test_oracle_employees_sample_connector_sql_contract() -> None:
    connector = _load_connector("connectors/oracle-employees.yaml")
    assert connector["metadata"]["name"] == "oracle-employees"
    assert connector["spec"]["mode"] == "sql_pull"

    source = connector["spec"]["source"]
    assert source["type"] == "oracle"
    assert source["secretRef"] == "oracle-hr-credentials"
    assert source["watermarkField"] == "updated_at"
    query = source["query"]
    assert ":watermark" not in query
    assert "FROM hr.employees" in query

    mapping = connector["spec"]["mapping"]
    assert mapping["idField"] == "employee_id"
    assert mapping["titleField"] == "full_name"

    reconciliation = connector["spec"]["reconciliation"]
    assert reconciliation["deletePolicy"] == "auto_delete_missing"


def test_hr_file_csv_sample_connector_contract() -> None:
    connector = _load_connector("connectors/hr-file-csv.yaml")
    assert connector["metadata"]["name"] == "hr-file-csv"
    assert connector["spec"]["mode"] == "file_pull"

    source = connector["spec"]["source"]
    assert source["type"] == "file"
    assert source["path"] == "./runtime/sources/hr"
    assert source["glob"] == "*.csv"
    assert source["format"] == "csv"
    assert source["csv"]["documentMode"] == "row"
    assert source["csv"]["delimiter"] == ","
    assert source["csv"]["hasHeader"] is True
    assert source["csv"]["encoding"] == "utf-8"

    mapping = connector["spec"]["mapping"]
    assert mapping["idField"] == "employee_id"
    assert mapping["titleField"] == "full_name"
    assert "file_name" in mapping["metadataFields"]

    output = connector["spec"]["output"]
    assert output["bucket"].startswith("file://")
    assert output["prefix"] == "hr-file-csv"

    reconciliation = connector["spec"]["reconciliation"]
    assert reconciliation["deletePolicy"] == "auto_delete_missing"
