from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/check_connector_examples_only.py", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_guard_passes_for_allowlisted_connector_change(tmp_path: Path) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("connectors/hr-employees.yaml\n", encoding="utf-8")

    result = _run(
        "--allowlist",
        str(allowlist),
        "--changed-file",
        "connectors/hr-employees.yaml",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_guard_fails_for_non_allowlisted_connector_change(tmp_path: Path) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("connectors/hr-employees.yaml\n", encoding="utf-8")

    result = _run(
        "--allowlist",
        str(allowlist),
        "--changed-file",
        "connectors/customer-specific.yaml",
    )

    assert result.returncode == 1
    assert "customer-specific.yaml" in result.stderr


def test_guard_ignores_non_connector_changes(tmp_path: Path) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("connectors/hr-employees.yaml\n", encoding="utf-8")

    result = _run(
        "--allowlist",
        str(allowlist),
        "--changed-file",
        "README.md",
    )

    assert result.returncode == 0, result.stdout + result.stderr
