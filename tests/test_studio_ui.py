from __future__ import annotations


def test_studio_pages_render(client) -> None:
    index = client.get("/studio/connectors")
    assert index.status_code == 200
    assert "Connector Studio" in index.text

    wizard = client.get("/studio/connectors/new")
    assert wizard.status_code == 200
    assert "Create Connection Profile" in wizard.text


def test_studio_wizard_exposes_mode_specific_configuration_controls(client) -> None:
    wizard = client.get("/studio/connectors/new")
    assert wizard.status_code == 200

    # Source controls
    assert '<option value="oracle">oracle</option>' in wizard.text
    assert '<option value="file_pull">File Pull</option>' in wizard.text
    assert '<option value="file">file</option>' in wizard.text
    assert 'id="draft-source-query"' in wizard.text
    assert 'id="draft-source-url"' in wizard.text
    assert 'id="draft-source-path"' in wizard.text
    assert 'id="draft-source-glob"' in wizard.text
    assert 'id="draft-source-format"' in wizard.text
    assert 'id="draft-source-csv-document-mode"' in wizard.text
    assert 'id="draft-source-csv-delimiter"' in wizard.text
    assert 'id="draft-source-csv-has-header"' in wizard.text
    assert 'id="draft-source-csv-encoding"' in wizard.text
    assert 'id="draft-source-method"' in wizard.text
    assert 'id="draft-source-watermark"' in wizard.text
    assert 'id="draft-source-headers"' in wizard.text
    assert 'id="draft-source-auth-mode"' in wizard.text
    assert 'id="draft-source-oauth-token-url"' in wizard.text
    assert 'id="draft-source-oauth-client-id"' in wizard.text
    assert 'id="draft-source-oauth-client-secret-ref"' in wizard.text
    assert 'id="draft-source-oauth-client-auth-method"' in wizard.text
    assert 'id="draft-source-oauth-scopes"' in wizard.text
    assert 'id="draft-source-oauth-audience"' in wizard.text

    # Advanced mapping + reconciliation controls
    assert 'id="draft-uri-template"' in wizard.text
    assert 'id="draft-mime-type"' in wizard.text
    assert 'id="draft-acl-users-field"' in wizard.text
    assert 'id="draft-acl-groups-field"' in wizard.text
    assert 'id="draft-metadata-fields"' in wizard.text
    assert 'id="draft-delete-policy"' in wizard.text


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
