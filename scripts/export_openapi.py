#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ingest_relay.api import app


def render_openapi_json() -> str:
    payload = app.openapi()
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI schema for docs site.")
    parser.add_argument(
        "--output",
        default="website/static/openapi.json",
        help="Path where OpenAPI JSON should be written.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_openapi_json(), encoding="utf-8")
    print(f"Wrote OpenAPI schema to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
