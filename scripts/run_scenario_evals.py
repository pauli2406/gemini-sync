#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _run_selector(selector: str) -> tuple[bool, str]:
    cmd = ["pytest", "-q", selector]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode == 0, output


def _load_baseline(path: str | Path) -> dict[str, bool]:
    baseline_path = Path(path)
    if not baseline_path.exists():
        return {}
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    return {str(k): bool(v) for k, v in payload.get("results", {}).items()}


def _save_baseline(path: str | Path, results: dict[str, bool]) -> None:
    payload = {"results": results}
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scenario eval suite")
    parser.add_argument("--registry", default="evals/eval_registry.yaml")
    parser.add_argument("--baseline", default="evals/baseline.json")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    registry = _load_yaml(args.registry)
    thresholds = registry.get("thresholds", {})
    min_pass_rate = float(thresholds.get("min_pass_rate_percent", 95))
    min_critical_rate = float(thresholds.get("min_critical_pass_rate_percent", 100))

    scenario_results: dict[str, bool] = {}
    details: list[dict[str, Any]] = []

    for item in registry.get("scenarios", []):
        scenario_file = item["path"]
        scenario = _load_yaml(scenario_file)
        selector = scenario["pytest_selector"]
        passed, output = _run_selector(selector)

        scenario_id = str(item["id"])
        scenario_results[scenario_id] = passed
        details.append(
            {
                "id": scenario_id,
                "critical": bool(item.get("critical", False)),
                "passed": passed,
                "selector": selector,
                "output": output,
            }
        )

    total = len(details)
    passed_count = sum(1 for row in details if row["passed"])
    pass_rate = (passed_count / total * 100) if total else 100.0

    critical_rows = [row for row in details if row["critical"]]
    critical_total = len(critical_rows)
    critical_passed = sum(1 for row in critical_rows if row["passed"])
    critical_rate = (critical_passed / critical_total * 100) if critical_total else 100.0

    baseline = _load_baseline(args.baseline)
    unresolved_regressions = [
        row["id"]
        for row in details
        if baseline.get(row["id"], True) and not row["passed"]
    ]

    summary = {
        "total": total,
        "passed": passed_count,
        "pass_rate_percent": pass_rate,
        "critical_total": critical_total,
        "critical_passed": critical_passed,
        "critical_pass_rate_percent": critical_rate,
        "min_pass_rate_percent": min_pass_rate,
        "min_critical_pass_rate_percent": min_critical_rate,
        "unresolved_regressions": unresolved_regressions,
        "details": details,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.update_baseline:
        _save_baseline(args.baseline, scenario_results)

    if pass_rate < min_pass_rate:
        print(
            f"ERROR: scenario pass rate {pass_rate:.2f}% is below required {min_pass_rate:.2f}%",
            file=sys.stderr,
        )
        return 1

    if critical_rate < min_critical_rate:
        print(
            "ERROR: critical scenario pass rate "
            f"{critical_rate:.2f}% is below required {min_critical_rate:.2f}%",
            file=sys.stderr,
        )
        return 1

    if unresolved_regressions:
        print(
            f"ERROR: unresolved regressions compared to baseline: {unresolved_regressions}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
