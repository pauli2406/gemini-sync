from __future__ import annotations

from datetime import UTC, datetime

from ingest_relay.models import RunState


def test_ops_dashboard_renders_with_polling_hooks(client) -> None:
    response = client.get("/ops")

    assert response.status_code == 200
    assert "Operations Dashboard" in response.text
    assert "/v1/ops/snapshot" in response.text
    assert "data-refresh-ms=\"15000\"" in response.text
    assert "id=\"status-filter\"" in response.text
    assert "id=\"connector-filter\"" in response.text
    assert "id=\"window-hours-filter\"" in response.text
    assert "id=\"runs-prev\"" in response.text
    assert "id=\"runs-next\"" in response.text
    assert "/static/ops.js" in response.text



def test_ops_connector_detail_renders_and_not_found(client) -> None:
    ok = client.get("/ops/connectors/support-push")
    assert ok.status_code == 200
    assert "/v1/ops/connectors/support-push" in ok.text
    assert "id=\"connector-status-filter\"" in ok.text
    assert "id=\"connector-runs-prev\"" in ok.text
    assert "id=\"connector-runs-next\"" in ok.text

    missing = client.get("/ops/connectors/unknown-connector")
    assert missing.status_code == 404



def test_ops_run_detail_renders_and_not_found(client, db_session_factory) -> None:
    with db_session_factory() as session:
        session.add(
            RunState(
                run_id="run-ui-1",
                connector_id="support-push",
                status="SUCCESS",
                started_at=datetime(2026, 2, 16, 10, 0, tzinfo=UTC),
                finished_at=datetime(2026, 2, 16, 10, 2, tzinfo=UTC),
            )
        )
        session.commit()

    ok = client.get("/ops/runs/run-ui-1")
    assert ok.status_code == 200
    assert "/v1/ops/runs/run-ui-1" in ok.text
    assert "id=\"run-link-splunk\"" in ok.text
    assert "id=\"run-link-kestra\"" in ok.text

    missing = client.get("/ops/runs/run-ui-missing")
    assert missing.status_code == 404
