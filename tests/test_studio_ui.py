from __future__ import annotations


def test_studio_pages_render(client) -> None:
    index = client.get("/studio/connectors")
    assert index.status_code == 200
    assert "Connector Studio" in index.text

    wizard = client.get("/studio/connectors/new")
    assert wizard.status_code == 200
    assert "Create Connection Profile" in wizard.text


def test_studio_connector_lifecycle_pages_render(client) -> None:
    for path in [
        "/studio/connectors/support-push/edit",
        "/studio/connectors/support-push/clone",
        "/studio/connectors/support-push/delete",
        "/studio/connectors/support-push/pause",
        "/studio/connectors/support-push/resume",
        "/studio/connectors/support-push/run",
    ]:
        response = client.get(path)
        assert response.status_code == 200
