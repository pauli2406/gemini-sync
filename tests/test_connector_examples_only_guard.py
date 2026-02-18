from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_connector_examples_only.py"


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
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
    connector_file = tmp_path / "connectors" / "customer-specific.yaml"
    connector_file.parent.mkdir(parents=True, exist_ok=True)
    connector_file.write_text("metadata:\n  name: customer-specific\n", encoding="utf-8")

    result = _run(
        "--allowlist",
        str(allowlist),
        "--changed-file",
        "connectors/customer-specific.yaml",
        cwd=tmp_path,
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


def test_guard_allows_deleting_non_allowlisted_connector(tmp_path: Path) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("connectors/hr-employees.yaml\n", encoding="utf-8")

    result = _run(
        "--allowlist",
        str(allowlist),
        "--changed-file",
        "connectors/customer-specific.yaml",
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
