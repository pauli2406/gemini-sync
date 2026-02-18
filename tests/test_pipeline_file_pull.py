from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

from gemini_sync_bridge.adapters.extractors import PullResult
from gemini_sync_bridge.models import Base, ConnectorCheckpoint, RunState
from gemini_sync_bridge.schemas import CanonicalDocument, ConnectorConfig, RunManifest
from gemini_sync_bridge.services import pipeline


class NoopGeminiIngestionClient:
    def __init__(self, settings) -> None:
        self.settings = settings

    def import_documents(self, gemini, manifest) -> None:  # pragma: no cover
        return

    def delete_documents(self, gemini, deletes) -> None:  # pragma: no cover
        return


def _file_connector_config() -> ConnectorConfig:
    return ConnectorConfig.model_validate(
        {
            "apiVersion": "sync.gemini.io/v1alpha1",
            "kind": "Connector",
            "metadata": {"name": "hr-file-csv"},
            "spec": {
                "mode": "file_pull",
                "schedule": "*/30 * * * *",
                "source": {
                    "type": "file",
                    "path": "./runtime/sources/hr",
                    "glob": "*.csv",
                    "format": "csv",
                    "watermarkField": "updated_at",
                    "csv": {
                        "documentMode": "row",
                        "delimiter": ",",
                        "hasHeader": True,
                        "encoding": "utf-8",
                    },
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ full_name }}",
                },
                "output": {
                    "bucket": "file://./tmp-test-output",
                    "prefix": "hr-file-csv",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "hr-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
        }
    )


def _build_doc(doc_id: str) -> CanonicalDocument:
    return CanonicalDocument(
        doc_id=doc_id,
        title="Ada",
        content="Ada",
        uri=None,
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": "hr-file-csv"},
        checksum=f"sha256:{doc_id}",
        op="UPSERT",
    )


def _manifest(run_id: str, watermark: str | None) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        connector_id="hr-file-csv",
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC),
        manifest_path="file://manifest.json",
        upserts_path="file://upserts.ndjson",
        deletes_path="file://deletes.ndjson",
        upserts_count=1,
        deletes_count=0,
        watermark=watermark,
    )


def test_run_connector_file_pull_persists_compact_checkpoint(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "pipeline.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    checkpoint_value = (
        '{"v":1,"rw":"2026-02-16T10:00:00+00:00","fc":1,'
        '"lm":"2026-02-16T10:00:00+00:00","fh":"sha256:test"}'
    )

    try:
        monkeypatch.setattr(pipeline, "SessionLocal", session_local)
        monkeypatch.setattr(pipeline, "load_connector_config", lambda _: _file_connector_config())
        monkeypatch.setattr(
            pipeline,
            "extract_file_rows",
            lambda source, checkpoint: PullResult(
                rows=[
                    {
                        "employee_id": "1",
                        "full_name": "Ada",
                        "updated_at": "2026-02-16T10:00:00+00:00",
                        "file_path": "/tmp/hr/a.csv",
                        "file_name": "a.csv",
                        "file_mtime": "2026-02-16T10:00:00+00:00",
                        "file_size_bytes": 12,
                    }
                ],
                watermark=checkpoint_value,
            ),
        )
        monkeypatch.setattr(
            pipeline,
            "normalize_records",
            lambda *args, **kwargs: [_build_doc("x:1")],
        )
        monkeypatch.setattr(
            pipeline,
            "compute_diffs",
            lambda session, connector_id, docs, delete_policy: (docs, []),
        )
        monkeypatch.setattr(
            pipeline,
            "publish_artifacts",
            lambda **kwargs: _manifest(kwargs["run_id"], kwargs.get("watermark")),
        )
        monkeypatch.setattr(pipeline, "GeminiIngestionClient", NoopGeminiIngestionClient)

        result = pipeline.run_connector("connectors/hr-file-csv.yaml")

        assert result.upserts == 1
        assert result.deletes == 0
        with session_local() as session:
            checkpoint = session.get(ConnectorCheckpoint, "hr-file-csv")
            assert checkpoint is not None
            assert checkpoint.watermark == checkpoint_value
            run = session.get(RunState, result.run_id)
            assert run is not None
            assert run.status == "SUCCESS"
    finally:
        close_all_sessions()
        engine.dispose()


def test_run_connector_file_pull_rejects_duplicate_doc_ids(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "pipeline.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    try:
        monkeypatch.setattr(pipeline, "SessionLocal", session_local)
        monkeypatch.setattr(pipeline, "load_connector_config", lambda _: _file_connector_config())
        monkeypatch.setattr(
            pipeline,
            "extract_file_rows",
            lambda source, checkpoint: PullResult(
                rows=[{"employee_id": "1", "full_name": "Ada"}],
                watermark='{"v":1,"rw":null,"fc":1,"lm":null,"fh":"sha256:test"}',
            ),
        )
        duplicate_a = _build_doc("hr-file-csv:1")
        duplicate_b = _build_doc("hr-file-csv:1")
        monkeypatch.setattr(
            pipeline,
            "normalize_records",
            lambda *args, **kwargs: [duplicate_a, duplicate_b],
        )
        monkeypatch.setattr(pipeline, "GeminiIngestionClient", NoopGeminiIngestionClient)

        with pytest.raises(
            ValueError,
            match="Duplicate document IDs detected in file_pull extraction",
        ):
            pipeline.run_connector("connectors/hr-file-csv.yaml")
    finally:
        close_all_sessions()
        engine.dispose()
