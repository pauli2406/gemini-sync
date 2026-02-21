#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from ingest_relay.api import app


def render_openapi_json() -> str:
    payload = app.openapi()
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if committed OpenAPI spec is out of date.")
    parser.add_argument(
        "--target",
        default="website/static/openapi.json",
        help="Path to committed OpenAPI JSON file.",
    )
    args = parser.parse_args()

    target_path = Path(args.target)
    expected = render_openapi_json()
    current = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    if expected == current:
        print("OpenAPI schema is up to date.")
        return 0

    print(
        "ERROR: OpenAPI schema drift detected. "
        "Run `python scripts/export_openapi.py` and commit the updated spec.",
        file=sys.stderr,
    )
    diff = difflib.unified_diff(
        current.splitlines(),
        expected.splitlines(),
        fromfile=str(target_path),
        tofile="generated-openapi.json",
        lineterm="",
    )
    for line in diff:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
