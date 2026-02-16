from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from gemini_sync_bridge.models import ConnectorCheckpoint, PushBatch, RunState
from gemini_sync_bridge.services import ops


def test_build_ops_snapshot_empty_db_returns_zeroes_and_empty_lists(
    db_session_factory, monkeypatch
) -> None:
    monkeypatch.setattr(ops, "_load_connector_catalog", lambda: {})

    with db_session_factory() as session:
        snapshot = ops.build_ops_snapshot(session=session, now=datetime(2026, 2, 16, tzinfo=UTC))

    assert snapshot.summary.total_runs == 0
    assert snapshot.summary.successful_runs == 0
    assert snapshot.summary.failed_runs == 0
    assert snapshot.summary.running_runs == 0
    assert snapshot.summary.pending_push_batches == 0
    assert snapshot.summary.success_rate_percent == 100.0
    assert snapshot.connectors == []
    assert snapshot.recent_runs == []



def test_build_ops_snapshot_selects_latest_run_and_computes_lag_and_pending(
    db_session_factory, monkeypatch
) -> None:
    now = datetime(2026, 2, 16, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        ops,
        "_load_connector_catalog",
        lambda: {
            "alpha": {
                "mode": "sql_pull",
                "schedule": "0 */3 * * *",
                "source_type": "postgres",
            }
        },
    )

    with db_session_factory() as session:
        session.add(
            RunState(
                run_id="run-old",
                connector_id="alpha",
                status="FAILED",
                started_at=now - timedelta(hours=4),
                finished_at=now - timedelta(hours=3, minutes=45),
                error_class="RuntimeError",
            )
        )
        session.add(
            RunState(
                run_id="run-new",
                connector_id="alpha",
                status="SUCCESS",
                started_at=now - timedelta(hours=1),
                finished_at=now - timedelta(minutes=50),
                upserts_count=5,
                deletes_count=1,
            )
        )
        session.add(
            ConnectorCheckpoint(
                connector_id="alpha",
                watermark="2026-02-16T10:00:00Z",
                updated_at=now - timedelta(hours=2),
            )
        )
        session.add(
            PushBatch(
                run_id="push-run-1",
                connector_id="alpha",
                idempotency_key="idem-1",
                status="PENDING",
                accepted=2,
                rejected=0,
            )
        )
        session.commit()

        snapshot = ops.build_ops_snapshot(session=session, now=now)

    connector = snapshot.connectors[0]
    assert connector.connector_id == "alpha"
    assert connector.last_run_id == "run-new"
    assert connector.last_status == "SUCCESS"
    assert connector.pending_push_batches == 1
    assert connector.freshness_lag_seconds == 7200

    assert snapshot.summary.total_runs == 2
    assert snapshot.summary.successful_runs == 1
    assert snapshot.summary.failed_runs == 1
    assert snapshot.summary.pending_push_batches == 1
    assert len(snapshot.recent_runs) == 2


def test_build_ops_snapshot_filters_and_paginates_recent_runs_with_links(
    db_session_factory, monkeypatch
) -> None:
    now = datetime(2026, 2, 16, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        ops,
        "_load_connector_catalog",
        lambda: {
            "support-push": {"mode": "rest_push", "schedule": None, "source_type": "http"},
            "alpha": {"mode": "sql_pull", "schedule": "0 */3 * * *", "source_type": "postgres"},
        },
    )
    monkeypatch.setattr(
        ops,
        "get_settings",
        lambda: SimpleNamespace(
            splunk_run_url_template="https://splunk.example/search?q={run_id}",
            kestra_run_url_template="https://kestra.example/executions/{run_id}",
        ),
    )

    with db_session_factory() as session:
        session.add_all(
            [
                RunState(
                    run_id="run-1",
                    connector_id="support-push",
                    status="FAILED",
                    started_at=now - timedelta(minutes=30),
                    finished_at=now - timedelta(minutes=25),
                    error_class="ValueError",
                ),
                RunState(
                    run_id="run-2",
                    connector_id="support-push",
                    status="FAILED",
                    started_at=now - timedelta(hours=1),
                    finished_at=now - timedelta(minutes=55),
                    error_class="RuntimeError",
                ),
                RunState(
                    run_id="run-3",
                    connector_id="support-push",
                    status="SUCCESS",
                    started_at=now - timedelta(hours=2),
                    finished_at=now - timedelta(hours=2, minutes=-5),
                ),
                RunState(
                    run_id="run-4",
                    connector_id="alpha",
                    status="FAILED",
                    started_at=now - timedelta(hours=3),
                    finished_at=now - timedelta(hours=2, minutes=50),
                ),
            ]
        )
        session.commit()

        snapshot = ops.build_ops_snapshot(
            session=session,
            now=now,
            status_filter="failed",
            connector_id="support-push",
            limit_runs=1,
            offset_runs=0,
        )
        second_page = ops.build_ops_snapshot(
            session=session,
            now=now,
            status_filter="FAILED",
            connector_id="support-push",
            limit_runs=1,
            offset_runs=1,
        )

    assert snapshot.runs_page.total_runs == 2
    assert snapshot.runs_page.has_more is True
    assert snapshot.recent_runs[0].run_id == "run-1"
    assert snapshot.recent_runs[0].links.splunk_url.endswith("run-1")
    assert snapshot.recent_runs[0].links.kestra_url.endswith("/run-1")
    assert len(snapshot.connectors) == 1
    assert snapshot.connectors[0].connector_id == "support-push"

    assert second_page.runs_page.total_runs == 2
    assert second_page.runs_page.has_more is False
    assert second_page.recent_runs[0].run_id == "run-2"
