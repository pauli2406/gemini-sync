from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_export_connector_reference_writes_expected_sections(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"
    table_header = (
        "| Field Path | Type | Required | Default | Allowed Values / Pattern | "
        "Modes | Description | Example | Operational Notes |"
    )

    result = _run(
        "scripts/export_connector_reference.py",
        "--schema",
        "schemas/connector.schema.json",
        "--meta",
        "schemas/connector.docs-meta.yaml",
        "--output",
        str(target),
    )

    assert result.returncode == 0, result.stderr
    content = target.read_text(encoding="utf-8")
    assert "# Connector Field Reference" in content
    assert table_header in content
    assert "`spec.reconciliation.deletePolicy`" in content
    assert "enum: `postgres`, `mssql`, `mysql`, `oracle`, `http`" in content


def test_check_connector_reference_drift_passes_for_matching_target(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"

    export_result = _run(
        "scripts/export_connector_reference.py",
        "--schema",
        "schemas/connector.schema.json",
        "--meta",
        "schemas/connector.docs-meta.yaml",
        "--output",
        str(target),
    )
    assert export_result.returncode == 0, export_result.stderr

    check_result = _run(
        "scripts/check_connector_reference_drift.py",
        "--schema",
        "schemas/connector.schema.json",
        "--meta",
        "schemas/connector.docs-meta.yaml",
        "--target",
        str(target),
    )
    assert check_result.returncode == 0, check_result.stderr
    assert "Connector field reference is up to date." in check_result.stdout


def test_check_connector_reference_drift_fails_for_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"
    target.write_text("# stale\n", encoding="utf-8")

    result = _run(
        "scripts/check_connector_reference_drift.py",
        "--schema",
        "schemas/connector.schema.json",
        "--meta",
        "schemas/connector.docs-meta.yaml",
        "--target",
        str(target),
    )

    assert result.returncode == 1
    assert "Connector field reference drift detected" in result.stderr
