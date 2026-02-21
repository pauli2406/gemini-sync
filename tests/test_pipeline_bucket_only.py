from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

from ingest_relay.adapters.extractors import PullResult
from ingest_relay.models import Base, ConnectorCheckpoint, RunState
from ingest_relay.schemas import ConnectorConfig, RunManifest
from ingest_relay.services import pipeline


class ForbiddenGeminiIngestionClient:
    def __init__(self, settings) -> None:
        raise AssertionError("GeminiIngestionClient must not be instantiated for bucket-only mode")


def _bucket_only_connector_config() -> ConnectorConfig:
    return ConnectorConfig.model_validate(
        {
            "apiVersion": "sync.gemini.io/v1alpha1",
            "kind": "Connector",
            "metadata": {"name": "oracle-qn-data-march-2025"},
            "spec": {
                "mode": "sql_pull",
                "schedule": "0 2 * * *",
                "source": {
                    "type": "oracle",
                    "secretRef": "oracle-qn-data-credentials",
                    "query": (
                        "SELECT 1 AS notiz_id, 'Ada' AS autor, "
                        "'note' AS notiz, 42 AS kundennummer"
                    ),
                },
                "output": {
                    "bucket": "file://./tmp-test-output",
                    "prefix": "oracle-qn-data-march-2025",
                    "format": "csv",
                    "publishLatestAlias": True,
                },
                "ingestion": {"enabled": False},
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
        }
    )


def _manifest(run_id: str, watermark: str | None) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        connector_id="oracle-qn-data-march-2025",
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC),
        manifest_path="file://manifest.json",
        csv_path="file://rows.csv",
        upserts_count=1,
        deletes_count=0,
        watermark=watermark,
    )


def test_run_connector_bucket_only_skips_gemini_ingestion(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "pipeline.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    try:
        monkeypatch.setattr(pipeline, "SessionLocal", session_local)
        monkeypatch.setattr(
            pipeline,
            "load_connector_config",
            lambda _: _bucket_only_connector_config(),
        )
        monkeypatch.setattr(
            pipeline,
            "extract_sql_rows",
            lambda source, checkpoint: PullResult(
                rows=[
                    {
                        "notiz_id": 1,
                        "autor": "Ada",
                        "notiz": "note",
                        "kundennummer": 42,
                        "erstellt_am": "2025-03-01T10:00:00+00:00",
                    }
                ],
                watermark="2025-03-01T10:00:00+00:00",
            ),
        )
        monkeypatch.setattr(
            pipeline,
            "normalize_records",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("normalize_records must not run for csv export")
            ),
        )
        monkeypatch.setattr(
            pipeline,
            "compute_diffs",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("compute_diffs must not run for csv export")
            ),
        )
        monkeypatch.setattr(
            pipeline,
            "publish_csv_artifacts",
            lambda **kwargs: _manifest(kwargs["run_id"], kwargs.get("watermark")),
        )
        monkeypatch.setattr(
            pipeline,
            "GeminiIngestionClient",
            ForbiddenGeminiIngestionClient,
        )

        result = pipeline.run_connector("connectors/oracle-qn-data-march-2025.yaml")

        assert result.upserts == 1
        assert result.deletes == 0
        with session_local() as session:
            checkpoint = session.get(ConnectorCheckpoint, "oracle-qn-data-march-2025")
            assert checkpoint is not None
            assert checkpoint.watermark == "2025-03-01T10:00:00+00:00"
            run = session.get(RunState, result.run_id)
            assert run is not None
            assert run.status == "SUCCESS"
    finally:
        close_all_sessions()
        engine.dispose()
