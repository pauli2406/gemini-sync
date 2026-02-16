#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SLO metrics against thresholds")
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--min-success-rate", type=float, default=99.0)
    parser.add_argument("--max-freshness-lag-seconds", type=int, default=3 * 60 * 60)
    parser.add_argument("--max-mttr-seconds", type=int, default=30 * 60)
    args = parser.parse_args()

    payload = json.loads(Path(args.metrics).read_text(encoding="utf-8"))

    success_rate = float(payload.get("success_rate_percent", 0.0))
    freshness_lag = int(payload.get("freshness_lag_seconds_max", 0))
    mttr_seconds = int(payload.get("mttr_seconds", 0))

    errors: list[str] = []

    if success_rate < args.min_success_rate:
        errors.append(
            "success_rate_percent below threshold "
            f"({success_rate:.2f} < {args.min_success_rate:.2f})"
        )

    if freshness_lag > args.max_freshness_lag_seconds:
        errors.append(
            "freshness_lag_seconds_max above threshold "
            f"({freshness_lag} > {args.max_freshness_lag_seconds})"
        )

    if mttr_seconds > args.max_mttr_seconds:
        errors.append(
            "mttr_seconds above threshold "
            f"({mttr_seconds} > {args.max_mttr_seconds})"
        )

    print(
        json.dumps(
            {
                "success_rate_percent": success_rate,
                "freshness_lag_seconds_max": freshness_lag,
                "mttr_seconds": mttr_seconds,
                "passed": not errors,
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
