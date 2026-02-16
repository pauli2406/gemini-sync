from __future__ import annotations

import json
import subprocess
import sys


def test_slo_gate_passes(tmp_path) -> None:
    metrics_path = tmp_path / "slo-pass.json"
    metrics_path.write_text(
        json.dumps(
            {
                "success_rate_percent": 99.5,
                "freshness_lag_seconds_max": 1200,
                "mttr_seconds": 300,
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_slo_gate.py",
            "--metrics",
            str(metrics_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0


def test_slo_gate_fails(tmp_path) -> None:
    metrics_path = tmp_path / "slo-fail.json"
    metrics_path.write_text(
        json.dumps(
            {
                "success_rate_percent": 80.0,
                "freshness_lag_seconds_max": 99999,
                "mttr_seconds": 99999,
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/check_slo_gate.py",
            "--metrics",
            str(metrics_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "ERROR:" in result.stderr
