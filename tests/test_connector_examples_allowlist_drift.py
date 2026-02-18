from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_connector_examples_allowlist_drift.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _write_connector(dir_path: Path, name: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / name).write_text(
        "apiVersion: sync.gemini.io/v1alpha1\nkind: Connector\nmetadata:\n  name: sample\n",
        encoding="utf-8",
    )


def test_allowlist_drift_check_passes_when_inventory_matches(tmp_path: Path) -> None:
    connectors_dir = tmp_path / "connectors"
    _write_connector(connectors_dir, "a.yaml")
    _write_connector(connectors_dir, "b.yaml")

    allowlist = tmp_path / "examples-allowlist.txt"
    allowlist.write_text("connectors/a.yaml\nconnectors/b.yaml\n", encoding="utf-8")

    result = _run("--allowlist", str(allowlist), "--connectors-dir", str(connectors_dir))

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"missing_in_allowlist": []' in result.stdout
    assert '"stale_allowlist_entries": []' in result.stdout


def test_allowlist_drift_check_fails_when_connector_not_allowlisted(tmp_path: Path) -> None:
    connectors_dir = tmp_path / "connectors"
    _write_connector(connectors_dir, "a.yaml")
    _write_connector(connectors_dir, "b.yaml")

    allowlist = tmp_path / "examples-allowlist.txt"
    allowlist.write_text("connectors/a.yaml\n", encoding="utf-8")

    result = _run("--allowlist", str(allowlist), "--connectors-dir", str(connectors_dir))

    assert result.returncode == 1
    assert "connectors/b.yaml" in result.stdout


def test_allowlist_drift_check_fails_when_allowlist_entry_is_stale(tmp_path: Path) -> None:
    connectors_dir = tmp_path / "connectors"
    _write_connector(connectors_dir, "a.yaml")

    allowlist = tmp_path / "examples-allowlist.txt"
    allowlist.write_text("connectors/a.yaml\nconnectors/missing.yaml\n", encoding="utf-8")

    result = _run("--allowlist", str(allowlist), "--connectors-dir", str(connectors_dir))

    assert result.returncode == 1
    assert "connectors/missing.yaml" in result.stdout


def test_allowlist_drift_check_fails_on_invalid_or_duplicate_entries(tmp_path: Path) -> None:
    connectors_dir = tmp_path / "connectors"
    _write_connector(connectors_dir, "a.yaml")

    allowlist = tmp_path / "examples-allowlist.txt"
    allowlist.write_text(
        "connectors/a.yaml\nconnectors/a.yaml\nbad/path.yaml\n",
        encoding="utf-8",
    )

    result = _run("--allowlist", str(allowlist), "--connectors-dir", str(connectors_dir))

    assert result.returncode == 1
    assert "duplicate entry 'connectors/a.yaml'" in result.stdout
    assert "invalid entry 'bad/path.yaml'" in result.stdout
