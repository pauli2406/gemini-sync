from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from gemini_sync_bridge.models import RecordState
from gemini_sync_bridge.schemas import CanonicalDocument, DeletePolicy


def _delete_checksum(doc_id: str) -> str:
    return f"sha256:{hashlib.sha256(doc_id.encode('utf-8')).hexdigest()}"


def compute_diffs(
    session: Session,
    connector_id: str,
    current_docs: list[CanonicalDocument],
    delete_policy: DeletePolicy,
) -> tuple[list[CanonicalDocument], list[CanonicalDocument]]:
    previous_rows = session.execute(
        select(RecordState).where(RecordState.connector_id == connector_id)
    ).scalars()
    previous_by_doc = {row.doc_id: row for row in previous_rows}

    upserts: list[CanonicalDocument] = []
    for doc in current_docs:
        previous = previous_by_doc.get(doc.doc_id)
        if not previous or previous.checksum != doc.checksum:
            upserts.append(doc)

    deletes: list[CanonicalDocument] = []
    if delete_policy == "auto_delete_missing":
        current_ids = {doc.doc_id for doc in current_docs}
        for doc_id in previous_by_doc:
            if doc_id not in current_ids:
                deletes.append(
                    CanonicalDocument(
                        doc_id=doc_id,
                        title="",
                        content="",
                        uri=None,
                        mime_type="text/plain",
                        updated_at=datetime.now(tz=UTC),
                        acl_users=[],
                        acl_groups=[],
                        metadata={"connector_id": connector_id},
                        checksum=_delete_checksum(doc_id),
                        op="DELETE",
                    )
                )

    if delete_policy == "soft_delete_only":
        current_ids = {doc.doc_id for doc in current_docs}
        for doc_id, state in previous_by_doc.items():
            if doc_id not in current_ids:
                deletes.append(
                    CanonicalDocument(
                        doc_id=doc_id,
                        title="",
                        content="",
                        uri=None,
                        mime_type="text/plain",
                        updated_at=state.source_updated_at,
                        acl_users=[],
                        acl_groups=[],
                        metadata={"connector_id": connector_id, "soft_delete": True},
                        checksum=_delete_checksum(doc_id),
                        op="DELETE",
                    )
                )

    return upserts, deletes


def apply_record_state(
    session: Session,
    connector_id: str,
    run_id: str,
    current_docs: list[CanonicalDocument],
    deletes: list[CanonicalDocument],
) -> None:
    existing_rows = session.execute(
        select(RecordState).where(RecordState.connector_id == connector_id)
    ).scalars()
    existing_by_doc = {row.doc_id: row for row in existing_rows}

    for doc in current_docs:
        existing = existing_by_doc.get(doc.doc_id)
        if existing:
            existing.checksum = doc.checksum
            existing.source_updated_at = doc.updated_at
            existing.last_seen_run_id = run_id
        else:
            session.add(
                RecordState(
                    connector_id=connector_id,
                    doc_id=doc.doc_id,
                    checksum=doc.checksum,
                    source_updated_at=doc.updated_at,
                    last_seen_run_id=run_id,
                )
            )

    if deletes:
        delete_ids = [doc.doc_id for doc in deletes]
        session.execute(
            delete(RecordState).where(
                RecordState.connector_id == connector_id,
                RecordState.doc_id.in_(delete_ids),
            )
        )
