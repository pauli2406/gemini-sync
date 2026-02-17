from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_security_policy_script_passes_for_repo_defaults() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_security_policy.py",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def _write_policies(tmp_path: Path) -> None:
    (tmp_path / ".agent").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".agent" / "risk_policy.yaml").write_text(
        (Path(".agent") / "risk_policy.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / ".agent" / "tool_policy.yaml").write_text(
        (Path(".agent") / "tool_policy.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _git(tmp_path: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(tmp_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _run_policy_check(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/check_security_policy.py",
            "--repo-root",
            str(tmp_path),
            "--risk-policy",
            str(tmp_path / ".agent" / "risk_policy.yaml"),
            "--tool-policy",
            str(tmp_path / ".agent" / "tool_policy.yaml"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_security_policy_script_ignores_untracked_node_modules_files(tmp_path: Path) -> None:
    _write_policies(tmp_path)
    (tmp_path / "README.md").write_text("safe", encoding="utf-8")

    _git(tmp_path, "init")
    _git(tmp_path, "add", ".")

    node_module_file = tmp_path / "website" / "node_modules" / "pkg.js"
    node_module_file.parent.mkdir(parents=True, exist_ok=True)
    token = "AI" + "za" + "FakeDependencyToken"
    node_module_file.write_text(f"const key = '{token}';", encoding="utf-8")

    result = _run_policy_check(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_security_policy_script_detects_tracked_secret_pattern(tmp_path: Path) -> None:
    _write_policies(tmp_path)
    (tmp_path / "README.md").write_text("safe", encoding="utf-8")
    tracked_secret = tmp_path / "secrets.txt"
    token = "gh" + "p_" + "example_secret_token"
    tracked_secret.write_text(token, encoding="utf-8")

    _git(tmp_path, "init")
    _git(tmp_path, "add", ".")

    result = _run_policy_check(tmp_path)
    assert result.returncode == 1
    assert "Potential secret pattern" in (result.stdout + result.stderr)
