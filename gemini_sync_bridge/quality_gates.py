from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GateResult:
    passed: bool
    errors: list[str]
    details: dict[str, Any]


PRODUCTION_IMPACT_PATTERNS = [
    "gemini_sync_bridge/**",
    "connectors/**",
    "schemas/**",
    "flows/**",
    "infra/**",
    "scripts/**",
    "Dockerfile",
    "docker-compose.yml",
]

BEHAVIOR_IMPACT_PATTERNS = [
    "gemini_sync_bridge/**",
    "connectors/**",
    "schemas/**",
    "flows/**",
    "scripts/**",
]

TEST_PATTERNS = ["tests/**"]
EVAL_SCENARIO_PATTERNS = ["evals/scenarios/**"]
DOC_PATTERNS = ["docs/**", "README.md", "AGENTS.md"]
EXEMPT_ONLY_PATTERNS = [
    "tests/**",
    ".github/**",
    ".gitignore",
    "LICENSE",
    "CONTRIBUTING.md",
    "*.md",
]


def _run_git_diff(base_ref: str, head_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        fallback = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in fallback.stdout.splitlines() if line.strip()]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _untracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base_ref: str = "origin/main", head_ref: str = "HEAD") -> list[str]:
    combined = _run_git_diff(base_ref=base_ref, head_ref=head_ref) + _untracked_files()
    return sorted(set(combined))


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def select_files(paths: list[str], patterns: list[str]) -> list[str]:
    return [path for path in paths if matches_any(path, patterns)]


def is_exempt_only_change(paths: list[str]) -> bool:
    if not paths:
        return True
    return all(matches_any(path, EXEMPT_ONLY_PATTERNS) for path in paths)


def evaluate_tdd_edd_guardrails(paths: list[str]) -> GateResult:
    errors: list[str] = []

    production_changed = select_files(paths, PRODUCTION_IMPACT_PATTERNS)
    behavior_changed = select_files(paths, BEHAVIOR_IMPACT_PATTERNS)
    tests_changed = select_files(paths, TEST_PATTERNS)
    evals_changed = select_files(paths, EVAL_SCENARIO_PATTERNS)

    if is_exempt_only_change(paths):
        return GateResult(
            passed=True,
            errors=[],
            details={
                "changed_files": paths,
                "exempt_only": True,
            },
        )

    if production_changed and not tests_changed:
        errors.append(
            "Production-impacting files changed without test updates in tests/**."
        )

    if behavior_changed and not evals_changed:
        errors.append(
            "Behavior-impacting files changed without scenario eval updates in evals/scenarios/**."
        )

    return GateResult(
        passed=not errors,
        errors=errors,
        details={
            "changed_files": paths,
            "production_changed": production_changed,
            "behavior_changed": behavior_changed,
            "tests_changed": tests_changed,
            "evals_changed": evals_changed,
        },
    )


def load_doc_sync_map(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def evaluate_docs_drift(paths: list[str], mapping: dict[str, Any]) -> GateResult:
    errors: list[str] = []

    exempt_patterns = mapping.get("exempt_sources", [])
    changed_docs = select_files(paths, DOC_PATTERNS)

    relevant_non_exempt = [
        p for p in paths if not matches_any(p, exempt_patterns) and not matches_any(p, DOC_PATTERNS)
    ]
    if not relevant_non_exempt:
        consistency_errors = evaluate_docs_consistency(mapping)
        return GateResult(
            passed=not consistency_errors,
            errors=consistency_errors,
            details={
                "changed_files": paths,
                "changed_docs": changed_docs,
                "triggered_rules": [],
            },
        )

    triggered_rules: list[str] = []
    for rule in mapping.get("rules", []):
        sources = rule.get("sources", [])
        docs_any_of = rule.get("docs_any_of", [])
        source_hits = [p for p in relevant_non_exempt if matches_any(p, sources)]
        if not source_hits:
            continue

        triggered_rules.append(rule.get("name", "unnamed"))

        if not changed_docs:
            errors.append(
                "Rule "
                f"'{rule.get('name', 'unnamed')}' triggered by {source_hits} "
                "but no docs were updated."
            )
            continue

        has_required_doc = any(matches_any(doc_file, docs_any_of) for doc_file in changed_docs)
        if not has_required_doc:
            errors.append(
                "Rule "
                f"'{rule.get('name', 'unnamed')}' requires one of {docs_any_of}; "
                f"changed docs were {changed_docs}."
            )

    errors.extend(evaluate_docs_consistency(mapping))

    return GateResult(
        passed=not errors,
        errors=errors,
        details={
            "changed_files": paths,
            "changed_docs": changed_docs,
            "triggered_rules": triggered_rules,
        },
    )


def evaluate_docs_consistency(mapping: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    consistency = mapping.get("consistency", {})

    required_files: list[str] = consistency.get("required_files", [])
    required_tokens: list[str] = consistency.get("required_tokens", [])

    loaded_files: dict[str, str] = {}
    for file_path in required_files:
        path = Path(file_path)
        if not path.exists():
            errors.append(f"Consistency file '{file_path}' does not exist.")
            continue
        loaded_files[file_path] = path.read_text(encoding="utf-8")

    for token in required_tokens:
        missing = [fp for fp, contents in loaded_files.items() if token not in contents]
        if missing:
            errors.append(
                f"Docs consistency token '{token}' missing from files: {missing}."
            )

    return errors
