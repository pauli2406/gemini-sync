from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas/connector.schema.json"
META_PATH = REPO_ROOT / "schemas/connector.docs-meta.yaml"
EXPORT_SCRIPT = REPO_ROOT / "scripts/export_connector_reference.py"
CHECK_SCRIPT = REPO_ROOT / "scripts/check_connector_reference_drift.py"


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
    )


def test_export_connector_reference_writes_expected_sections(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"
    table_header = (
        "| Field Path | Type | Required | Default | Allowed Values / Pattern | "
        "Modes | Description | Example | Operational Notes |"
    )

    result = _run(
        str(EXPORT_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        "--output",
        str(target),
    )

    assert result.returncode == 0, result.stderr
    content = target.read_text(encoding="utf-8")
    assert "# Connector Field Reference" in content
    assert table_header in content
    assert "`spec.reconciliation.deletePolicy`" in content
    assert "enum: `postgres`, `mssql`, `mysql`, `oracle`, `http`, `file`" in content
    assert "connectors/&lt;prefix&gt;/latest/" in content


def test_check_connector_reference_drift_passes_for_matching_target(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"

    export_result = _run(
        str(EXPORT_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        "--output",
        str(target),
    )
    assert export_result.returncode == 0, export_result.stderr

    check_result = _run(
        str(CHECK_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        "--target",
        str(target),
    )
    assert check_result.returncode == 0, check_result.stderr
    assert "Connector field reference is up to date." in check_result.stdout


def test_check_connector_reference_drift_fails_for_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "connector-field-reference.md"
    target.write_text("# stale\n", encoding="utf-8")

    result = _run(
        str(CHECK_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        "--target",
        str(target),
    )

    assert result.returncode == 1
    assert "Connector field reference drift detected" in result.stderr


def test_export_connector_reference_uses_default_output_path(tmp_path: Path) -> None:
    result = _run(
        str(EXPORT_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    default_target = tmp_path / "docs/reference/connector-fields.md"
    assert default_target.exists()
    content = default_target.read_text(encoding="utf-8")
    assert "# Connector Field Reference" in content


def test_check_connector_reference_drift_uses_default_target_path(tmp_path: Path) -> None:
    export_result = _run(
        str(EXPORT_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        cwd=tmp_path,
    )
    assert export_result.returncode == 0, export_result.stderr

    check_result = _run(
        str(CHECK_SCRIPT),
        "--schema",
        str(SCHEMA_PATH),
        "--meta",
        str(META_PATH),
        cwd=tmp_path,
    )
    assert check_result.returncode == 0, check_result.stderr
    assert "Connector field reference is up to date." in check_result.stdout
