#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from gemini_sync_bridge.quality_gates import (
    changed_files,
    evaluate_docs_drift,
    load_doc_sync_map,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect docs drift for changed source files")
    parser.add_argument("--mapping", default="docs/doc_sync_map.yaml")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Optional explicit changed file path. Can be supplied multiple times.",
    )
    args = parser.parse_args()

    mapping = load_doc_sync_map(args.mapping)
    files = args.changed_file or changed_files(base_ref=args.base_ref, head_ref=args.head_ref)
    result = evaluate_docs_drift(files, mapping)

    print(json.dumps(result.details, indent=2, sort_keys=True))
    if not result.passed:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
