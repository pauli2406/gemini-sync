from __future__ import annotations

import json
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


def test_export_openapi_writes_expected_file(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"

    result = _run("scripts/export_openapi.py", "--output", str(target))

    assert result.returncode == 0, result.stderr
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["info"]["title"] == "IngestRelay"
    assert payload["openapi"].startswith("3.")


def test_check_openapi_drift_passes_for_matching_target(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    export_result = _run("scripts/export_openapi.py", "--output", str(target))
    assert export_result.returncode == 0, export_result.stderr

    check_result = _run("scripts/check_openapi_drift.py", "--target", str(target))

    assert check_result.returncode == 0, check_result.stderr
    assert "OpenAPI schema is up to date." in check_result.stdout


def test_check_openapi_drift_fails_for_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    target.write_text("{}", encoding="utf-8")

    result = _run("scripts/check_openapi_drift.py", "--target", str(target))

    assert result.returncode == 1
    assert "OpenAPI schema drift detected" in result.stderr
