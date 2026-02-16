from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gemini_sync_bridge.adapters.extractors import PullResult
from gemini_sync_bridge.models import Base, ConnectorCheckpoint
from gemini_sync_bridge.schemas import CanonicalDocument, ConnectorConfig, RunManifest
from gemini_sync_bridge.services import pipeline


class FailingGeminiIngestionClient:
    def __init__(self, settings) -> None:
        self.settings = settings

    def import_documents(self, gemini, manifest) -> None:
        raise RuntimeError("ingestion failure")

    def delete_documents(self, gemini, deletes) -> None:  # pragma: no cover
        return


def _connector_config() -> ConnectorConfig:
    return ConnectorConfig.model_validate(
        {
            "apiVersion": "sync.gemini.io/v1alpha1",
            "kind": "Connector",
            "metadata": {"name": "hr-employees"},
            "spec": {
                "mode": "sql_pull",
                "schedule": "0 */3 * * *",
                "source": {
                    "type": "postgres",
                    "secretRef": "hr-db-credentials",
                    "query": "SELECT 1",
                    "watermarkField": "updated_at",
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ full_name }}",
                },
                "output": {
                    "bucket": "file://./tmp-test-output",
                    "prefix": "hr-employees",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "hr-ds",
                },
                "reconciliation": {
                    "deletePolicy": "auto_delete_missing",
                },
            },
        }
    )


def test_checkpoint_not_advanced_when_ingestion_fails(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "pipeline.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with session_local() as session:
        session.add(
            ConnectorCheckpoint(
                connector_id="hr-employees",
                watermark="2026-02-01T00:00:00+00:00",
                updated_at=datetime.now(tz=UTC),
            )
        )
        session.commit()

    doc = CanonicalDocument(
        doc_id="hr-employees:1",
        title="Jane Doe",
        content="Jane Doe",
        uri=None,
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": "hr-employees"},
        checksum="sha256:test",
        op="UPSERT",
    )

    manifest = RunManifest(
        run_id="run-1",
        connector_id="hr-employees",
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC),
        manifest_path="file://manifest.json",
        upserts_path="file://upserts.ndjson",
        deletes_path="file://deletes.ndjson",
        upserts_count=1,
        deletes_count=0,
        watermark="2026-02-16T00:00:00+00:00",
    )

    monkeypatch.setattr(pipeline, "SessionLocal", session_local)
    monkeypatch.setattr(pipeline, "load_connector_config", lambda _: _connector_config())
    monkeypatch.setattr(
        pipeline,
        "extract_sql_rows",
        lambda source, checkpoint: PullResult(
            rows=[
                {
                    "employee_id": 1,
                    "full_name": "Jane Doe",
                    "updated_at": "2026-02-16T00:00:00+00:00",
                }
            ],
            watermark="2026-02-16T00:00:00+00:00",
        ),
    )
    monkeypatch.setattr(pipeline, "normalize_records", lambda *args, **kwargs: [doc])
    monkeypatch.setattr(pipeline, "publish_artifacts", lambda **kwargs: manifest)
    monkeypatch.setattr(pipeline, "GeminiIngestionClient", FailingGeminiIngestionClient)

    with pytest.raises(RuntimeError):
        pipeline.run_connector("connectors/hr-employees.yaml")

    with session_local() as session:
        checkpoint = session.get(ConnectorCheckpoint, "hr-employees")
        assert checkpoint is not None
        assert checkpoint.watermark == "2026-02-01T00:00:00+00:00"
