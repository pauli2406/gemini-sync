from __future__ import annotations

import re

from gemini_sync_bridge.utils.doc_ids import to_discovery_doc_id


def test_to_discovery_doc_id_keeps_already_valid_ids() -> None:
    assert to_discovery_doc_id("hr-employees-1001") == "hr-employees-1001"


def test_to_discovery_doc_id_normalizes_invalid_characters() -> None:
    converted = to_discovery_doc_id("hr-employees:1001")
    assert converted.startswith("hr-employees_1001_")
    assert re.fullmatch(r"[a-zA-Z0-9_-]+", converted)


def test_to_discovery_doc_id_is_deterministic() -> None:
    first = to_discovery_doc_id("hr-employees:1001")
    second = to_discovery_doc_id("hr-employees:1001")
    assert first == second
