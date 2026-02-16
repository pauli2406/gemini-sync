from __future__ import annotations

from datetime import UTC, datetime

from gemini_sync_bridge.models import RecordState
from gemini_sync_bridge.schemas import CanonicalDocument
from gemini_sync_bridge.services.diff_engine import compute_diffs


def test_compute_diffs_detects_updates_and_deletes(db_session_factory) -> None:
    session = db_session_factory()
    try:
        session.add(
            RecordState(
                connector_id="hr-employees",
                doc_id="hr-employees:old",
                checksum="sha256:old",
                source_updated_at=datetime.now(tz=UTC),
                last_seen_run_id="run-old",
            )
        )
        session.add(
            RecordState(
                connector_id="hr-employees",
                doc_id="hr-employees:keep",
                checksum="sha256:same",
                source_updated_at=datetime.now(tz=UTC),
                last_seen_run_id="run-old",
            )
        )
        session.commit()

        current_docs = [
            CanonicalDocument(
                doc_id="hr-employees:keep",
                title="Keep",
                content="No change",
                uri=None,
                mime_type="text/plain",
                updated_at=datetime.now(tz=UTC),
                acl_users=[],
                acl_groups=[],
                metadata={"connector_id": "hr-employees"},
                checksum="sha256:same",
                op="UPSERT",
            ),
            CanonicalDocument(
                doc_id="hr-employees:new",
                title="New",
                content="Changed",
                uri=None,
                mime_type="text/plain",
                updated_at=datetime.now(tz=UTC),
                acl_users=[],
                acl_groups=[],
                metadata={"connector_id": "hr-employees"},
                checksum="sha256:new",
                op="UPSERT",
            ),
        ]

        upserts, deletes = compute_diffs(
            session,
            "hr-employees",
            current_docs,
            "auto_delete_missing",
        )

        assert {doc.doc_id for doc in upserts} == {"hr-employees:new"}
        assert {doc.doc_id for doc in deletes} == {"hr-employees:old"}
        assert all(doc.op == "DELETE" for doc in deletes)
    finally:
        session.close()
