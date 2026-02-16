#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from gemini_sync_bridge.quality_gates import changed_files, evaluate_tdd_edd_guardrails


def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce TDD + EDD changed-files guardrails")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Optional explicit changed file path. Can be supplied multiple times.",
    )
    args = parser.parse_args()

    files = args.changed_file or changed_files(base_ref=args.base_ref, head_ref=args.head_ref)
    result = evaluate_tdd_edd_guardrails(files)

    print(json.dumps(result.details, indent=2, sort_keys=True))
    if not result.passed:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
