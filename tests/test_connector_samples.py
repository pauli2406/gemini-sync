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
    assert ":watermark" in query
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
