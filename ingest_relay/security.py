from __future__ import annotations

PROMPT_INJECTION_MARKERS = [
    "ignore previous instructions",
    "disregard all prior instructions",
    "reveal system prompt",
    "system prompt",
    "developer message",
    "<script",
    "javascript:",
]


class PromptInjectionDetectedError(ValueError):
    pass


def contains_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in PROMPT_INJECTION_MARKERS)


def validate_prompt_injection_safe(*values: str) -> None:
    for value in values:
        if contains_prompt_injection(value):
            raise PromptInjectionDetectedError(
                "Potential prompt-injection marker detected in document content."
            )
