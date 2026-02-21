from __future__ import annotations

from ingest_relay.quality_gates import evaluate_docs_consistency, evaluate_docs_drift


def _mapping() -> dict:
    return {
        "exempt_sources": ["tests/**", ".github/**"],
        "rules": [
            {
                "name": "runtime",
                "sources": ["ingest_relay/**"],
                "docs_any_of": ["README.md", "docs/concepts/architecture.mdx"],
            }
        ],
        "consistency": {
            "required_files": [],
            "required_tokens": [],
        },
    }


def test_docs_drift_fails_when_runtime_changes_without_docs() -> None:
    result = evaluate_docs_drift(["ingest_relay/services/pipeline.py"], _mapping())

    assert not result.passed
    assert any("no docs were updated" in error for error in result.errors)


def test_docs_drift_passes_when_mapped_doc_changes() -> None:
    result = evaluate_docs_drift(
        [
            "ingest_relay/services/pipeline.py",
            "docs/concepts/architecture.mdx",
        ],
        _mapping(),
    )

    assert result.passed


def test_docs_drift_passes_for_exempt_changes() -> None:
    result = evaluate_docs_drift(["tests/test_quality_gate_docs.py"], _mapping())

    assert result.passed


def test_docs_consistency_detects_missing_tokens(tmp_path, monkeypatch) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hello", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    errors = evaluate_docs_consistency(
        {
            "consistency": {
                "required_files": ["README.md"],
                "required_tokens": ["must-exist-token"],
            }
        }
    )

    assert errors
    assert "must-exist-token" in errors[0]
