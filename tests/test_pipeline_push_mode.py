from __future__ import annotations

from datetime import UTC, datetime

from ingest_relay.schemas import CanonicalDocument
from ingest_relay.services.pipeline import _split_push_docs


def test_split_push_docs_respects_operation() -> None:
    upsert_doc = CanonicalDocument(
        doc_id="support-push:1",
        title="Ticket 1",
        content="Body",
        uri=None,
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": "support-push"},
        checksum="sha256:upsert",
        op="UPSERT",
    )
    delete_doc = CanonicalDocument(
        doc_id="support-push:2",
        title="",
        content="",
        uri=None,
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": "support-push"},
        checksum="sha256:delete",
        op="DELETE",
    )

    upserts, deletes = _split_push_docs([upsert_doc, delete_doc])

    assert [doc.doc_id for doc in upserts] == ["support-push:1"]
    assert [doc.doc_id for doc in deletes] == ["support-push:2"]
