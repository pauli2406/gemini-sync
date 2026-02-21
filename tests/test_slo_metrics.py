from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ingest_relay.models import Base, ConnectorCheckpoint, RunState
from ingest_relay.services.slo import compute_slo_metrics


def test_compute_slo_metrics_from_run_state() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(tz=UTC)

    try:
        with SessionLocal() as session:
            session.add_all(
                [
                    RunState(
                        run_id="run-failed",
                        connector_id="hr",
                        status="FAILED",
                        started_at=now - timedelta(hours=2),
                        finished_at=now - timedelta(hours=2) + timedelta(minutes=5),
                    ),
                    RunState(
                        run_id="run-success-after-fail",
                        connector_id="hr",
                        status="SUCCESS",
                        started_at=now - timedelta(hours=2) + timedelta(minutes=15),
                        finished_at=now - timedelta(hours=2) + timedelta(minutes=20),
                    ),
                    RunState(
                        run_id="run-success-2",
                        connector_id="kb",
                        status="SUCCESS",
                        started_at=now - timedelta(hours=1),
                        finished_at=now - timedelta(hours=1) + timedelta(minutes=3),
                    ),
                ]
            )
            session.add_all(
                [
                    ConnectorCheckpoint(
                        connector_id="hr",
                        watermark="2026-02-16T00:00:00+00:00",
                        updated_at=now - timedelta(hours=1),
                    ),
                    ConnectorCheckpoint(
                        connector_id="kb",
                        watermark="2026-02-16T00:00:00+00:00",
                        updated_at=now - timedelta(minutes=30),
                    ),
                ]
            )
            session.commit()

            metrics = compute_slo_metrics(session=session, now=now)

        assert round(metrics.success_rate_percent, 2) == 66.67
        assert metrics.mttr_seconds == 600
        assert metrics.freshness_lag_seconds_max == 3600
    finally:
        engine.dispose()
