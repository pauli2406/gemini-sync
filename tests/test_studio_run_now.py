from __future__ import annotations

from unittest.mock import patch


def test_run_now_endpoint_enqueues_request(client) -> None:
    with patch("gemini_sync_bridge.api._execute_manual_run", return_value=None):
        response = client.post("/v1/studio/connectors/support-push/run-now")

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] in {"QUEUED", "RUNNING", "SUCCESS", "FAILED"}
    assert payload["request_id"]
