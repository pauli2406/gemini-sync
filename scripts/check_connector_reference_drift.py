#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from scripts.export_connector_reference import _load_doc, render_connector_reference


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when connector field reference markdown is out of date."
    )
    parser.add_argument("--schema", default="schemas/connector.schema.json")
    parser.add_argument("--meta", default="schemas/connector.docs-meta.yaml")
    parser.add_argument("--target", default="docs/reference/connector-fields.md")
    args = parser.parse_args()

    schema_doc = _load_doc(Path(args.schema))
    meta_doc = _load_doc(Path(args.meta))
    expected = render_connector_reference(schema_doc, meta_doc)

    target_path = Path(args.target)
    current = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    if expected == current:
        print("Connector field reference is up to date.")
        return 0

    print(
        "ERROR: Connector field reference drift detected. "
        "Run `python scripts/export_connector_reference.py` and commit the updated markdown.",
        file=sys.stderr,
    )
    diff = difflib.unified_diff(
        current.splitlines(),
        expected.splitlines(),
        fromfile=str(target_path),
        tofile="generated-connector-field-reference.md",
        lineterm="",
    )
    for line in diff:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
