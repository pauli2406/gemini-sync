from __future__ import annotations

from ingest_relay.quality_gates import evaluate_tdd_edd_guardrails


def test_tdd_guardrail_fails_without_test_updates() -> None:
    result = evaluate_tdd_edd_guardrails(["ingest_relay/services/pipeline.py"])

    assert not result.passed
    assert any("test updates" in error for error in result.errors)


def test_tdd_guardrail_fails_without_eval_updates_for_behavior_change() -> None:
    result = evaluate_tdd_edd_guardrails(
        [
            "ingest_relay/services/normalizer.py",
            "tests/test_normalizer.py",
        ]
    )

    assert not result.passed
    assert any("scenario eval updates" in error for error in result.errors)


def test_tdd_guardrail_passes_with_source_test_and_eval_updates() -> None:
    result = evaluate_tdd_edd_guardrails(
        [
            "ingest_relay/services/normalizer.py",
            "tests/test_normalizer.py",
            "evals/scenarios/prompt-injection-rest-pull.yaml",
        ]
    )

    assert result.passed


def test_tdd_guardrail_passes_for_exempt_only_changes() -> None:
    result = evaluate_tdd_edd_guardrails(
        ["tests/test_push_api.py", "docs/concepts/architecture.mdx"]
    )

    assert result.passed
