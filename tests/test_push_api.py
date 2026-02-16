from __future__ import annotations


def _payload(doc_id: str) -> list[dict]:
    return [
        {
            "doc_id": doc_id,
            "title": "VPN issue",
            "content": "Cannot connect",
            "uri": "https://support.internal/tickets/123",
            "mime_type": "text/plain",
            "updated_at": "2026-02-16T08:30:00Z",
            "acl_users": [],
            "acl_groups": ["it-support"],
            "metadata": {"connector_id": "support-push"},
            "checksum": "sha256:test",
            "op": "UPSERT",
        }
    ]


def test_push_events_idempotency(client) -> None:
    headers = {"Idempotency-Key": "idempo-1"}
    first = client.post(
        "/v1/connectors/support-push/events",
        headers=headers,
        json=_payload("support-push:1"),
    )
    assert first.status_code == 200

    first_body = first.json()
    assert first_body["accepted"] == 1
    assert first_body["rejected"] == 0

    second = client.post(
        "/v1/connectors/support-push/events",
        headers=headers,
        json=_payload("support-push:1"),
    )
    assert second.status_code == 200
    assert second.json() == first_body

    conflict = client.post(
        "/v1/connectors/support-push/events",
        headers=headers,
        json=_payload("support-push:2"),
    )
    assert conflict.status_code == 409
