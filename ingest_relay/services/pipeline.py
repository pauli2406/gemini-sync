from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ingest_relay.adapters.extractors import (
    extract_file_rows,
    extract_rest_rows,
    extract_sql_rows,
)
from ingest_relay.connector_loader import load_connector_config
from ingest_relay.db import SessionLocal
from ingest_relay.models import ConnectorCheckpoint, PushBatch, PushEvent, RunState
from ingest_relay.schemas import CanonicalDocument
from ingest_relay.services.diff_engine import apply_record_state, compute_diffs
from ingest_relay.services.gemini_ingestion import GeminiIngestionClient
from ingest_relay.services.normalizer import normalize_records
from ingest_relay.services.observability import send_splunk_event, send_teams_alert
from ingest_relay.services.publisher import publish_artifacts, publish_csv_artifacts
from ingest_relay.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    run_id: str
    connector_id: str
    upserts: int
    deletes: int
    manifest_path: str | None


@contextmanager
def _session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _start_run(session: Session, run_id: str, connector_id: str) -> RunState:
    run = RunState(
        run_id=run_id,
        connector_id=connector_id,
        status="RUNNING",
        started_at=datetime.now(tz=UTC),
    )
    session.add(run)
    session.commit()
    return run


def _set_run_failure(session: Session, run_id: str, exc: Exception) -> None:
    run = session.get(RunState, run_id)
    if not run:
        return
    run.status = "FAILED"
    run.finished_at = datetime.now(tz=UTC)
    run.error_class = exc.__class__.__name__
    run.error_message = str(exc)
    session.commit()


def _set_run_success(session: Session, run_id: str, upserts: int, deletes: int) -> None:
    run = session.get(RunState, run_id)
    if not run:
        return
    run.status = "SUCCESS"
    run.finished_at = datetime.now(tz=UTC)
    run.upserts_count = upserts
    run.deletes_count = deletes
    session.commit()


def _get_checkpoint(session: Session, connector_id: str) -> str | None:
    checkpoint = session.get(ConnectorCheckpoint, connector_id)
    return checkpoint.watermark if checkpoint else None


def _set_checkpoint(session: Session, connector_id: str, watermark: str | None) -> None:
    checkpoint = session.get(ConnectorCheckpoint, connector_id)
    if checkpoint:
        checkpoint.watermark = watermark
        checkpoint.updated_at = datetime.now(tz=UTC)
    else:
        checkpoint = ConnectorCheckpoint(
            connector_id=connector_id,
            watermark=watermark,
            updated_at=datetime.now(tz=UTC),
        )
        session.add(checkpoint)


def _consume_push_batch(
    session: Session,
    connector_id: str,
    requested_run_id: str | None,
) -> tuple[list[CanonicalDocument], str | None]:
    query = select(PushBatch).where(
        PushBatch.connector_id == connector_id,
        PushBatch.status == "PENDING",
    )
    if requested_run_id:
        query = query.where(PushBatch.run_id == requested_run_id)
    query = query.order_by(PushBatch.created_at.asc())

    batch = session.execute(query).scalars().first()
    if not batch:
        return [], None

    events = session.execute(
        select(PushEvent).where(
            PushEvent.connector_id == connector_id,
            PushEvent.run_id == batch.run_id,
            PushEvent.processed.is_(False),
        )
    ).scalars()

    docs = [CanonicalDocument.model_validate(event.payload) for event in events]
    return docs, batch.run_id


def _mark_push_batch_processed(session: Session, connector_id: str, run_id: str) -> None:
    batch = session.get(PushBatch, run_id)
    if batch:
        batch.status = "PROCESSED"

    events = session.execute(
        select(PushEvent).where(
            PushEvent.connector_id == connector_id,
            PushEvent.run_id == run_id,
            PushEvent.processed.is_(False),
        )
    ).scalars()

    for event in events:
        event.processed = True


def _split_push_docs(
    docs: list[CanonicalDocument],
) -> tuple[list[CanonicalDocument], list[CanonicalDocument]]:
    upserts: list[CanonicalDocument] = []
    deletes: list[CanonicalDocument] = []
    for doc in docs:
        if doc.op == "DELETE":
            deletes.append(doc)
        else:
            upserts.append(doc)
    return upserts, deletes


def _ensure_unique_doc_ids(docs: list[CanonicalDocument]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for doc in docs:
        if doc.doc_id in seen:
            duplicates.add(doc.doc_id)
        seen.add(doc.doc_id)
    if duplicates:
        ordered = sorted(duplicates)
        raise ValueError(
            "Duplicate document IDs detected in file_pull extraction: "
            f"{', '.join(ordered)}"
        )


def run_connector(connector_path: str, push_run_id: str | None = None) -> PipelineResult:
    settings = get_settings()
    connector = load_connector_config(connector_path)
    connector_id = connector.metadata.name
    run_id = push_run_id or uuid.uuid4().hex
    started_at = datetime.now(tz=UTC)

    with _session_scope() as session:
        _start_run(session, run_id, connector_id)

    logger.info("connector_run_started", extra={"connector_id": connector_id, "run_id": run_id})

    try:
        with _session_scope() as session:
            checkpoint = _get_checkpoint(session, connector_id)
            docs: list[CanonicalDocument] = []
            upserts: list[CanonicalDocument] = []
            deletes: list[CanonicalDocument] = []
            rows_for_csv: list[dict[str, Any]] | None = None
            upsert_count = 0
            delete_count = 0

            if connector.spec.mode == "sql_pull":
                pulled = extract_sql_rows(connector.spec.source, checkpoint)
                watermark = pulled.watermark
                push_batch_id = None
                if connector.spec.output.format == "csv":
                    rows_for_csv = pulled.rows
                else:
                    if connector.spec.mapping is None:
                        raise ValueError(
                            "spec.mapping is required when spec.output.format is ndjson"
                        )
                    docs = normalize_records(
                        connector_id,
                        connector.spec.mapping,
                        connector.spec.source.watermark_field,
                        pulled.rows,
                    )
            elif connector.spec.mode == "rest_pull":
                if connector.spec.mapping is None:
                    raise ValueError("spec.mapping is required when spec.output.format is ndjson")
                pulled = extract_rest_rows(connector.spec.source, checkpoint)
                docs = normalize_records(
                    connector_id,
                    connector.spec.mapping,
                    connector.spec.source.watermark_field,
                    pulled.rows,
                )
                watermark = pulled.watermark
                push_batch_id = None
            elif connector.spec.mode == "file_pull":
                if connector.spec.mapping is None:
                    raise ValueError("spec.mapping is required when spec.output.format is ndjson")
                pulled = extract_file_rows(connector.spec.source, checkpoint)
                docs = normalize_records(
                    connector_id,
                    connector.spec.mapping,
                    connector.spec.source.watermark_field,
                    pulled.rows,
                )
                _ensure_unique_doc_ids(docs)
                watermark = pulled.watermark
                push_batch_id = None
            elif connector.spec.mode == "rest_push":
                docs, push_batch_id = _consume_push_batch(session, connector_id, push_run_id)
                if not push_batch_id:
                    session.commit()
                    with _session_scope() as status_session:
                        _set_run_success(status_session, run_id, 0, 0)
                    return PipelineResult(
                        run_id=run_id,
                        connector_id=connector_id,
                        upserts=0,
                        deletes=0,
                        manifest_path=None,
                    )

                upserts, deletes = _split_push_docs(docs)
                watermark = checkpoint
            else:
                raise ValueError(f"Unsupported connector mode: {connector.spec.mode}")

            if connector.spec.mode != "rest_push" and connector.spec.output.format != "csv":
                upserts, deletes = compute_diffs(
                    session,
                    connector_id,
                    docs,
                    connector.spec.reconciliation.delete_policy,
                )

            if connector.spec.output.format == "csv":
                if rows_for_csv is None:
                    raise ValueError(
                        "CSV export is only supported for sql_pull connectors with extracted rows."
                    )
                manifest = publish_csv_artifacts(
                    connector_id=connector_id,
                    output=connector.spec.output,
                    run_id=run_id,
                    rows=rows_for_csv,
                    watermark=watermark,
                    started_at=started_at,
                )
            else:
                manifest = publish_artifacts(
                    connector_id=connector_id,
                    output=connector.spec.output,
                    run_id=run_id,
                    upserts=upserts,
                    deletes=deletes,
                    watermark=watermark,
                    started_at=started_at,
                )

            if connector.spec.ingestion.enabled:
                if connector.spec.gemini is None:
                    raise ValueError(
                        "Connector validation failed: spec.gemini is required when "
                        "spec.ingestion.enabled is true"
                    )

                ingestion_client = GeminiIngestionClient(settings)
                ingestion_client.import_documents(connector.spec.gemini, manifest)
                ingestion_client.delete_documents(connector.spec.gemini, deletes)

            if connector.spec.output.format != "csv":
                apply_record_state(session, connector_id, run_id, upserts, deletes)
                upsert_count = len(upserts)
                delete_count = len(deletes)
            else:
                upsert_count = len(rows_for_csv or [])
                delete_count = 0
            _set_checkpoint(session, connector_id, watermark)
            if connector.spec.mode == "rest_push" and push_batch_id:
                _mark_push_batch_processed(session, connector_id, push_batch_id)

            session.commit()

        with _session_scope() as session:
            _set_run_success(session, run_id, upsert_count, delete_count)

        event = {
            "status": "SUCCESS",
            "connector_id": connector_id,
            "run_id": run_id,
            "upserts": upsert_count,
            "deletes": delete_count,
            "manifest_path": manifest.manifest_path,
        }
        send_splunk_event(settings, event)
        logger.info("connector_run_completed", extra=event)

        return PipelineResult(
            run_id=run_id,
            connector_id=connector_id,
            upserts=upsert_count,
            deletes=delete_count,
            manifest_path=manifest.manifest_path,
        )

    except Exception as exc:
        logger.exception(
            "connector_run_failed",
            extra={"connector_id": connector_id, "run_id": run_id, "error": str(exc)},
        )

        with _session_scope() as session:
            _set_run_failure(session, run_id, exc)

        send_splunk_event(
            settings,
            {
                "status": "FAILED",
                "connector_id": connector_id,
                "run_id": run_id,
                "error_class": exc.__class__.__name__,
                "error_message": str(exc),
            },
        )
        send_teams_alert(
            settings,
            title=f"IngestRelay failed: {connector_id}",
            message=str(exc),
            facts={
                "connector": connector_id,
                "run_id": run_id,
                "error": exc.__class__.__name__,
            },
        )
        raise
