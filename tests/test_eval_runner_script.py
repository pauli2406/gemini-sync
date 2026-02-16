from __future__ import annotations

import subprocess
import sys

import yaml


def test_run_scenario_evals_script_passes_for_valid_registry(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        yaml.safe_dump(
            {
                "id": "sample",
                "name": "sample",
                "critical": True,
                "pytest_selector": (
                    "tests/test_quality_gate_tdd.py::"
                    "test_tdd_guardrail_passes_for_exempt_only_changes"
                ),
            }
        ),
        encoding="utf-8",
    )

    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(
            {
                "thresholds": {
                    "min_pass_rate_percent": 95,
                    "min_critical_pass_rate_percent": 100,
                },
                "scenarios": [
                    {
                        "id": "sample",
                        "path": str(scenario_path),
                        "critical": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    baseline_path = tmp_path / "baseline.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_scenario_evals.py",
            "--registry",
            str(registry_path),
            "--baseline",
            str(baseline_path),
            "--update-baseline",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert baseline_path.exists()
