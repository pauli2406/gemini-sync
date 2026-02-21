from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from ingest_relay.models import RunState
from ingest_relay.services import ops


def test_ops_snapshot_contract_and_cache_headers(client, db_session_factory) -> None:
    with db_session_factory() as session:
        session.add(
            RunState(
                run_id="run-ops-1",
                connector_id="support-push",
                status="SUCCESS",
                started_at=datetime(2026, 2, 16, 8, 0, tzinfo=UTC),
                finished_at=datetime(2026, 2, 16, 8, 5, tzinfo=UTC),
                upserts_count=3,
                deletes_count=0,
            )
        )
        session.commit()

    response = client.get("/v1/ops/snapshot")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"

    payload = response.json()
    assert set(payload.keys()) == {"summary", "connectors", "recent_runs", "runs_page"}

    summary = payload["summary"]
    assert {
        "window_hours",
        "total_runs",
        "successful_runs",
        "failed_runs",
        "running_runs",
        "success_rate_percent",
        "mttr_seconds",
        "freshness_lag_seconds_max",
        "pending_push_batches",
        "generated_at",
    }.issubset(summary.keys())

    assert payload["recent_runs"]
    row = payload["recent_runs"][0]
    assert {
        "run_id",
        "connector_id",
        "status",
        "started_at",
        "finished_at",
        "duration_seconds",
        "upserts_count",
        "deletes_count",
        "error_class",
        "links",
    }.issubset(row.keys())



def test_ops_connector_not_found_returns_404(client) -> None:
    response = client.get("/v1/ops/connectors/does-not-exist")
    assert response.status_code == 404



def test_ops_run_detail_returns_failure_context(client, db_session_factory) -> None:
    with db_session_factory() as session:
        session.add(
            RunState(
                run_id="run-fail-1",
                connector_id="support-push",
                status="FAILED",
                started_at=datetime(2026, 2, 16, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 2, 16, 9, 1, tzinfo=UTC),
                error_class="ValueError",
                error_message="broken payload",
            )
        )
        session.commit()

    response = client.get("/v1/ops/runs/run-fail-1")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["run_id"] == "run-fail-1"
    assert payload["status"] == "FAILED"
    assert payload["error_class"] == "ValueError"
    assert payload["error_message"] == "broken payload"


def test_ops_snapshot_filters_paginates_and_returns_linkouts(
    client, db_session_factory, monkeypatch
) -> None:
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
                    run_id="run-filter-1",
                    connector_id="support-push",
                    status="FAILED",
                    started_at=datetime(2026, 2, 16, 10, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 16, 10, 1, tzinfo=UTC),
                ),
                RunState(
                    run_id="run-filter-2",
                    connector_id="support-push",
                    status="FAILED",
                    started_at=datetime(2026, 2, 16, 9, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 16, 9, 1, tzinfo=UTC),
                ),
                RunState(
                    run_id="run-filter-3",
                    connector_id="hr-employees",
                    status="FAILED",
                    started_at=datetime(2026, 2, 16, 8, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 16, 8, 1, tzinfo=UTC),
                ),
            ]
        )
        session.commit()

    response = client.get(
        "/v1/ops/snapshot",
        params={
            "status": "failed",
            "connector_id": "support-push",
            "limit_runs": 1,
            "offset_runs": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["runs_page"]["total_runs"] == 2
    assert payload["runs_page"]["offset_runs"] == 1
    assert payload["runs_page"]["has_more"] is False
    assert len(payload["connectors"]) == 1
    assert payload["connectors"][0]["connector_id"] == "support-push"
    assert payload["recent_runs"][0]["run_id"] == "run-filter-2"
    assert payload["recent_runs"][0]["links"]["splunk_url"].endswith("run-filter-2")
    assert payload["recent_runs"][0]["links"]["kestra_url"].endswith("/run-filter-2")
