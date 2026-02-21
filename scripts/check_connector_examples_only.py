#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ingest_relay.quality_gates import changed_files


def _normalize(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _load_allowlist(path: str | Path) -> set[str]:
    allowlist_path = Path(path)
    entries: set[str] = set()
    for raw in allowlist_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(_normalize(line))
    return entries


def _disallowed_connector_changes(
    paths: list[str],
    *,
    allowlisted_paths: set[str],
    allowlist_file: str,
) -> list[str]:
    violations: list[str] = []
    for raw in paths:
        path = _normalize(raw)
        if not path.startswith("connectors/"):
            continue
        if path == allowlist_file:
            continue
        if path in allowlisted_paths:
            continue
        # Deletions are allowed so migrated custom connectors can be cleaned up.
        # `git diff --name-only` does not include status, so infer deletion from
        # missing path in the current workspace.
        if not Path(path).exists():
            continue
        violations.append(path)
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when non-example connector files are changed in connectors/."
    )
    parser.add_argument(
        "--allowlist",
        default="connectors/examples-allowlist.txt",
        help="Relative path to allowlisted connector files.",
    )
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Optional explicit changed file path. Can be supplied multiple times.",
    )
    args = parser.parse_args()

    allowlist_file = _normalize(args.allowlist)
    allowlisted_paths = _load_allowlist(args.allowlist)
    files = args.changed_file or changed_files(base_ref=args.base_ref, head_ref=args.head_ref)
    violations = _disallowed_connector_changes(
        files,
        allowlisted_paths=allowlisted_paths,
        allowlist_file=allowlist_file,
    )

    print(
        json.dumps(
            {
                "changed_files": sorted({_normalize(path) for path in files}),
                "allowlist_file": allowlist_file,
                "allowlisted_paths": sorted(allowlisted_paths),
                "violations": violations,
            },
            indent=2,
            sort_keys=True,
        )
    )

    if violations:
        print(
            "ERROR: Non-example connector files changed under connectors/: "
            f"{violations}. Keep user-specific connectors outside this repo "
            "(set CONNECTORS_DIR) or update only allowlisted sample connectors.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
