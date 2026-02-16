#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_DENY_PREFIXES = [
    "git reset --hard",
    "git checkout --",
    "sudo",
    "curl | sh",
    "wget | sh",
]


def _load_yaml(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    ignored = {".git", ".venv", "__pycache__", ".ruff_cache", ".pytest_cache"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored for part in path.parts):
            continue
        files.append(path)
    return files


def _contains_secret_like_patterns(repo_root: Path, patterns: list[str]) -> list[str]:
    findings: list[str] = []
    compiled = [re.compile(re.escape(pattern)) for pattern in patterns]
    ignored_files = {
        ".agent/tool_policy.yaml",
        ".agent/risk_policy.yaml",
    }

    for file_path in _iter_files(repo_root):
        relative = file_path.relative_to(repo_root).as_posix()
        if relative in ignored_files:
            continue
        if fnmatch.fnmatch(relative, "*.json") and "baseline" in relative:
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for regex in compiled:
            if regex.search(content):
                findings.append(f"Potential secret pattern '{regex.pattern}' in {relative}")
                break

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate security policy files")
    parser.add_argument("--risk-policy", default=".agent/risk_policy.yaml")
    parser.add_argument("--tool-policy", default=".agent/tool_policy.yaml")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    risk_policy = _load_yaml(args.risk_policy)
    tool_policy = _load_yaml(args.tool_policy)

    errors: list[str] = []

    mode = tool_policy.get("mode")
    if mode != "deny_by_default":
        errors.append("tool policy must set mode=deny_by_default")

    deny_prefixes = tool_policy.get("command_policy", {}).get("deny_prefixes", [])
    for required in REQUIRED_DENY_PREFIXES:
        if required not in deny_prefixes:
            errors.append(f"tool policy missing required deny prefix: {required}")

    tiers = risk_policy.get("tiers", {})
    for required_tier in ["tier_0", "tier_1", "tier_2", "tier_3"]:
        if required_tier not in tiers:
            errors.append(f"risk policy missing {required_tier}")

    if tiers.get("tier_3", {}).get("merge", {}).get("auto_merge", True):
        errors.append("tier_3 must enforce auto_merge=false")

    blocked_patterns = tool_policy.get("secrets", {}).get("blocked_patterns", [])
    if not blocked_patterns:
        errors.append("tool policy must define secrets.blocked_patterns")
    else:
        errors.extend(_contains_secret_like_patterns(Path(args.repo_root), blocked_patterns))

    print(
        json.dumps(
            {
                "risk_policy": args.risk_policy,
                "tool_policy": args.tool_policy,
                "errors": errors,
                "passed": not errors,
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
