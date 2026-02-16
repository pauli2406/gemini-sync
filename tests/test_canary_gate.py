from __future__ import annotations

import json
import subprocess
import sys


def test_canary_gate_passes(tmp_path) -> None:
    metrics = {
        "error_budget_burn": 0.05,
        "failed_run_rate_delta": 0.0,
        "freshness_lag_breach": False,
    }
    metrics_path = tmp_path / "metrics-pass.json"
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/canary_gate.py",
            "--metrics",
            str(metrics_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0


def test_canary_gate_fails(tmp_path) -> None:
    metrics = {
        "error_budget_burn": 0.50,
        "failed_run_rate_delta": 0.20,
        "freshness_lag_breach": True,
    }
    metrics_path = tmp_path / "metrics-fail.json"
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/canary_gate.py",
            "--metrics",
            str(metrics_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "ERROR:" in result.stderr
