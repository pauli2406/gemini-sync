from __future__ import annotations

import base64
import json
from datetime import UTC, datetime

from gemini_sync_bridge.schemas import CanonicalDocument
from gemini_sync_bridge.services.publisher import _canonical_ndjson, _discovery_document_ndjson
from gemini_sync_bridge.utils.doc_ids import to_discovery_doc_id


def _sample_doc(*, content: str = "Engineering Manager profile") -> CanonicalDocument:
    return CanonicalDocument(
        doc_id="hr-employees:1001",
        title="Jane Doe",
        content=content,
        uri="https://hr.internal/employees/1001",
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=["jane@company.com"],
        acl_groups=["eng-managers"],
        metadata={"connector_id": "hr-employees"},
        checksum="sha256:abc",
        op="UPSERT",
    )


def test_discovery_document_ndjson_contains_content_and_safe_id() -> None:
    doc = _sample_doc()

    payload = json.loads(_discovery_document_ndjson([doc]).splitlines()[0])

    assert payload["id"] == to_discovery_doc_id(doc.doc_id)
    assert payload["content"]["mimeType"] == "text/plain"
    decoded = base64.b64decode(payload["content"]["rawBytes"]).decode("utf-8")
    assert decoded == doc.content
    assert payload["structData"]["doc_id"] == doc.doc_id


def test_discovery_document_ndjson_uses_title_when_content_empty() -> None:
    doc = _sample_doc(content="")

    payload = json.loads(_discovery_document_ndjson([doc]).splitlines()[0])
    decoded = base64.b64decode(payload["content"]["rawBytes"]).decode("utf-8")

    assert decoded == doc.title


def test_canonical_ndjson_keeps_internal_shape() -> None:
    doc = _sample_doc()

    payload = json.loads(_canonical_ndjson([doc]).splitlines()[0])

    assert payload["doc_id"] == doc.doc_id
    assert "id" not in payload
    assert "content" in payload
