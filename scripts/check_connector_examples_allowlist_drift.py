#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWLIST_LINE_RE = re.compile(r"^connectors/[^/]+\.yaml$")


def _normalize(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _load_allowlist(path: Path) -> tuple[list[str], list[str]]:
    entries: list[str] = []
    errors: list[str] = []

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        normalized = _normalize(line)
        if not ALLOWLIST_LINE_RE.fullmatch(normalized):
            errors.append(
                f"{path}:{lineno} invalid entry '{line}' "
                "(expected connectors/<name>.yaml)"
            )
            continue
        entries.append(normalized)

    duplicates = sorted({entry for entry in entries if entries.count(entry) > 1})
    for entry in duplicates:
        errors.append(f"{path}: duplicate entry '{entry}'")

    return sorted(set(entries)), errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when connectors examples allowlist drifts from tracked connector samples."
    )
    parser.add_argument(
        "--allowlist",
        default="connectors/examples-allowlist.txt",
        help="Path to canonical connector examples allowlist.",
    )
    parser.add_argument(
        "--connectors-dir",
        default="connectors",
        help="Directory containing connector YAML samples.",
    )
    args = parser.parse_args()

    allowlist_path = Path(args.allowlist)
    connectors_dir = Path(args.connectors_dir)

    if not allowlist_path.exists():
        print(f"ERROR: allowlist file not found: {allowlist_path}", file=sys.stderr)
        return 1
    if not connectors_dir.exists():
        print(f"ERROR: connectors directory not found: {connectors_dir}", file=sys.stderr)
        return 1

    allowlisted, parse_errors = _load_allowlist(allowlist_path)
    actual = sorted(f"connectors/{path.name}" for path in connectors_dir.glob("*.yaml"))

    missing_in_allowlist = sorted(set(actual) - set(allowlisted))
    stale_allowlist_entries = sorted(set(allowlisted) - set(actual))

    payload = {
        "allowlist_file": _normalize(str(allowlist_path)),
        "allowlisted_connectors": allowlisted,
        "actual_connectors": actual,
        "missing_in_allowlist": missing_in_allowlist,
        "stale_allowlist_entries": stale_allowlist_entries,
        "parse_errors": parse_errors,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if parse_errors or missing_in_allowlist or stale_allowlist_entries:
        print(
            "ERROR: Connector examples allowlist drift detected. "
            "Update connectors/examples-allowlist.txt to exactly match core sample connectors.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
