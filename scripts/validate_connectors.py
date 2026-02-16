#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jsonschema
import yaml


def validate_connectors(schema_path: Path, connectors_dir: Path) -> int:
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    errors = 0

    for connector_file in sorted(connectors_dir.glob("*.yaml")):
        payload = yaml.safe_load(connector_file.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        file_errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
        if file_errors:
            errors += len(file_errors)
            print(f"{connector_file}:")
            for err in file_errors:
                path = ".".join(str(p) for p in err.path)
                print(f"  - {path}: {err.message}")

    if errors == 0:
        print("All connector definitions are valid.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate connector YAML files against schema")
    parser.add_argument("--schema", default="schemas/connector.schema.json")
    parser.add_argument("--connectors", default="connectors")
    args = parser.parse_args()

    return 1 if validate_connectors(Path(args.schema), Path(args.connectors)) else 0


if __name__ == "__main__":
    sys.exit(main())
