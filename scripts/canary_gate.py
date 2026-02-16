#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate canary SLO gates")
    parser.add_argument(
        "--metrics",
        required=True,
        help="Path to JSON file containing canary metrics",
    )
    parser.add_argument("--max-error-budget-burn", type=float, default=0.20)
    parser.add_argument("--max-failed-run-rate-delta", type=float, default=0.0)
    parser.add_argument("--allow-freshness-breach", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    error_budget_burn = float(payload.get("error_budget_burn", 0.0))
    failed_run_rate_delta = float(payload.get("failed_run_rate_delta", 0.0))
    freshness_lag_breach = bool(payload.get("freshness_lag_breach", False))

    errors: list[str] = []

    if error_budget_burn >= args.max_error_budget_burn:
        errors.append(
            "error_budget_burn exceeded threshold "
            f"({error_budget_burn:.4f} >= {args.max_error_budget_burn:.4f})"
        )

    if failed_run_rate_delta > args.max_failed_run_rate_delta:
        errors.append(
            "failed_run_rate_delta exceeded threshold "
            f"({failed_run_rate_delta:.4f} > {args.max_failed_run_rate_delta:.4f})"
        )

    if freshness_lag_breach and not args.allow_freshness_breach:
        errors.append("freshness lag breach detected")

    result = {
        "error_budget_burn": error_budget_burn,
        "failed_run_rate_delta": failed_run_rate_delta,
        "freshness_lag_breach": freshness_lag_breach,
        "passed": not errors,
        "errors": errors,
    }

    print(json.dumps(result, indent=2, sort_keys=True))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
