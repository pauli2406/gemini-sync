from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from gemini_sync_bridge.services.studio import build_proposed_file_changes


def _base_draft(name: str) -> dict:
    return {
        "metadata": {"name": name},
        "spec": {
            "mode": "rest_pull",
            "source": {
                "type": "http",
                "secretRef": "kb-api-token",
                "url": "https://kb.local/articles",
                "method": "GET",
                "watermarkField": "updated_at",
            },
            "mapping": {
                "idField": "article_id",
                "titleField": "title",
                "contentTemplate": "{{ title }} {{ body }}",
            },
            "output": {"bucket": "file://./local-bucket", "prefix": name, "format": "ndjson"},
            "gemini": {"projectId": "p", "location": "global", "dataStoreId": "ds"},
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
        "schedule": {"cron": "*/30 * * * *", "enabled": True},
    }


def test_build_proposed_file_changes_for_create_and_pause_resume() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        helm_values = root / "values.yaml"
        helm_values.write_text(yaml.safe_dump({"scheduleJobs": []}), encoding="utf-8")

        create_changes = build_proposed_file_changes(
            action="create",
            connector_id="studio-kb",
            draft=_base_draft("studio-kb"),
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        assert "connectors/studio-kb.yaml" in create_changes
        assert "infra/helm/ingest-relay/values.yaml" in create_changes

        # simulate apply of create result
        (connectors_dir / "studio-kb.yaml").write_text(
            create_changes["connectors/studio-kb.yaml"],
            encoding="utf-8",
        )
        helm_values.write_text(
            create_changes["infra/helm/ingest-relay/values.yaml"], encoding="utf-8"
        )

        pause_changes = build_proposed_file_changes(
            action="pause",
            connector_id="studio-kb",
            draft=None,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        payload = yaml.safe_load(pause_changes["infra/helm/ingest-relay/values.yaml"])
        assert payload["scheduleJobs"][0]["enabled"] is False

        helm_values.write_text(
            pause_changes["infra/helm/ingest-relay/values.yaml"], encoding="utf-8"
        )
        resume_changes = build_proposed_file_changes(
            action="resume",
            connector_id="studio-kb",
            draft=None,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        resumed = yaml.safe_load(resume_changes["infra/helm/ingest-relay/values.yaml"])
        assert resumed["scheduleJobs"][0]["enabled"] is True


def test_build_proposed_file_changes_for_delete_removes_connector_and_schedule() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        (connectors_dir / "to-delete.yaml").write_text(
            "metadata:\n  name: to-delete\n",
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "to-delete",
                            "schedule": "*/30 * * * *",
                            "connectorPath": "connectors/to-delete.yaml",
                            "enabled": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        delete_changes = build_proposed_file_changes(
            action="delete",
            connector_id="to-delete",
            draft=None,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        assert delete_changes["connectors/to-delete.yaml"] is None
        payload = yaml.safe_load(delete_changes["infra/helm/ingest-relay/values.yaml"])
        assert payload["scheduleJobs"] == []


def test_edit_preserves_existing_advanced_fields_and_avoids_schedule_noise() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "hr-employees.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "hr-employees"},
                    "spec": {
                        "mode": "sql_pull",
                        "schedule": "0 */3 * * *",
                        "source": {
                            "type": "postgres",
                            "secretRef": "hr-db-credentials",
                            "query": (
                                "SELECT employee_id, full_name, department, role, bio, "
                                "allowed_users, allowed_groups, updated_at FROM employees "
                                "WHERE updated_at > :watermark"
                            ),
                            "watermarkField": "updated_at",
                        },
                        "mapping": {
                            "idField": "employee_id",
                            "titleField": "full_name",
                            "contentTemplate": "{{ department }} {{ role }} {{ bio }}",
                            "uriTemplate": "https://hr.internal/employees/{{ employee_id }}",
                            "aclUsersField": "allowed_users",
                            "aclGroupsField": "allowed_groups",
                            "metadataFields": ["department", "role"],
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "hr-employees",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "hr-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "hr-employees",
                            "schedule": "0 */3 * * *",
                            "connectorPath": "connectors/hr-employees.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        # Draft mimics Studio's simplified form payload.
        sparse_edit_draft = {
            "metadata": {"name": "hr-employees"},
            "spec": {
                "mode": "sql_pull",
                "source": {
                    "type": "postgres",
                    "secretRef": "hr-db-credentials",
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ department }} {{ role }} {{ bio }}",
                },
                "output": {
                    "bucket": "gs://pochert-test-bucket",
                    "prefix": "hr-employees",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "gemini-enterprise-test-487620",
                    "location": "eu",
                    "dataStoreId": "hr-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "0 */3 * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="hr-employees",
            draft=sparse_edit_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        assert "connectors/hr-employees.yaml" in changes
        assert "infra/helm/ingest-relay/values.yaml" not in changes

        rendered = yaml.safe_load(changes["connectors/hr-employees.yaml"])
        assert rendered["spec"]["source"]["query"].startswith("SELECT employee_id")
        assert rendered["spec"]["mapping"]["uriTemplate"] == (
            "https://hr.internal/employees/{{ employee_id }}"
        )
        assert rendered["spec"]["mapping"]["aclUsersField"] == "allowed_users"
        assert rendered["spec"]["mapping"]["aclGroupsField"] == "allowed_groups"
        assert rendered["spec"]["mapping"]["metadataFields"] == ["department", "role"]
        assert rendered["spec"]["output"]["bucket"] == "gs://pochert-test-bucket"
        assert rendered["spec"]["gemini"]["projectId"] == "gemini-enterprise-test-487620"


def test_edit_mode_switch_prunes_incompatible_source_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "hr-employees.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "hr-employees"},
                    "spec": {
                        "mode": "sql_pull",
                        "schedule": "0 */3 * * *",
                        "source": {
                            "type": "postgres",
                            "secretRef": "hr-db-credentials",
                            "query": (
                                "SELECT employee_id FROM employees "
                                "WHERE updated_at > :watermark"
                            ),
                            "watermarkField": "updated_at",
                        },
                        "mapping": {
                            "idField": "employee_id",
                            "titleField": "full_name",
                            "contentTemplate": "{{ full_name }}",
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "hr-employees",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "hr-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "hr-employees",
                            "schedule": "0 */3 * * *",
                            "connectorPath": "connectors/hr-employees.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        # Sparse draft mirrors old UI behavior where mode could change
        # without sending explicit nulls for source fields.
        mode_switch_draft = {
            "metadata": {"name": "hr-employees"},
            "spec": {
                "mode": "rest_push",
                "source": {
                    "type": "http",
                    "secretRef": "support-push-token",
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ full_name }}",
                },
                "output": {
                    "bucket": "gs://company-ingest-relay",
                    "prefix": "hr-employees",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "hr-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "*/5 * * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="hr-employees",
            draft=mode_switch_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        rendered = yaml.safe_load(changes["connectors/hr-employees.yaml"])
        assert rendered["spec"]["mode"] == "rest_push"
        assert rendered["spec"]["source"]["type"] == "http"
        assert rendered["spec"]["source"]["secretRef"] == "support-push-token"
        assert "query" not in rendered["spec"]["source"]
        assert "watermarkField" not in rendered["spec"]["source"]
        assert "url" not in rendered["spec"]["source"]


def test_edit_sql_pull_prunes_rest_only_source_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "kb-rest.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "kb-rest"},
                    "spec": {
                        "mode": "rest_pull",
                        "schedule": "*/30 * * * *",
                        "source": {
                            "type": "http",
                            "secretRef": "kb-api-token",
                            "url": "https://kb.local/articles",
                            "method": "GET",
                            "payload": {"scope": "internal"},
                            "watermarkField": "updated_at",
                            "paginationCursorField": "cursor",
                            "paginationNextCursorJsonPath": "paging.next_cursor",
                            "headers": {"X-Tenant": "internal"},
                            "oauth": {
                                "grantType": "client_credentials",
                                "tokenUrl": (
                                    "https://auth.local/realms/acme/"
                                    "protocol/openid-connect/token"
                                ),
                                "clientId": "bridge-client",
                                "clientSecretRef": "oauth-client-secret",
                                "scopes": ["api.read"],
                                "audience": "knowledge-api",
                                "clientAuthMethod": "client_secret_post",
                            },
                        },
                        "mapping": {
                            "idField": "article_id",
                            "titleField": "title",
                            "contentTemplate": "{{ title }}",
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "kb-rest",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "kb-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "kb-rest",
                            "schedule": "*/30 * * * *",
                            "connectorPath": "connectors/kb-rest.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        switch_to_sql_draft = {
            "metadata": {"name": "kb-rest"},
            "spec": {
                "mode": "sql_pull",
                "source": {
                    "type": "postgres",
                    "secretRef": "hr-db-credentials",
                    "query": "SELECT employee_id FROM employees WHERE updated_at > :watermark",
                    "watermarkField": "updated_at",
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ full_name }}",
                },
                "output": {
                    "bucket": "gs://pochert-test-bucket",
                    "prefix": "kb-rest",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "kb-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "0 */3 * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="kb-rest",
            draft=switch_to_sql_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        rendered = yaml.safe_load(changes["connectors/kb-rest.yaml"])
        source = rendered["spec"]["source"]
        assert rendered["spec"]["mode"] == "sql_pull"
        assert source["type"] == "postgres"
        assert "url" not in source
        assert "payload" not in source
        assert "paginationCursorField" not in source
        assert "paginationNextCursorJsonPath" not in source
        assert "headers" not in source
        assert "method" not in source
        assert "oauth" not in source


def test_edit_rest_pull_prunes_query_and_forces_http_source_type() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "hr-employees.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "hr-employees"},
                    "spec": {
                        "mode": "sql_pull",
                        "schedule": "0 */3 * * *",
                        "source": {
                            "type": "postgres",
                            "secretRef": "hr-db-credentials",
                            "query": (
                                "SELECT employee_id FROM employees "
                                "WHERE updated_at > :watermark"
                            ),
                            "watermarkField": "updated_at",
                        },
                        "mapping": {
                            "idField": "employee_id",
                            "titleField": "full_name",
                            "contentTemplate": "{{ full_name }}",
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "hr-employees",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "hr-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "hr-employees",
                            "schedule": "0 */3 * * *",
                            "connectorPath": "connectors/hr-employees.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        switch_to_rest_pull_draft = {
            "metadata": {"name": "hr-employees"},
            "spec": {
                "mode": "rest_pull",
                "source": {
                    "type": "postgres",
                    "secretRef": "kb-api-token",
                    "url": "https://kb.local/articles",
                    "method": "GET",
                    "watermarkField": "updated_at",
                    "oauth": {
                        "grantType": "client_credentials",
                        "tokenUrl": (
                            "https://auth.local/realms/acme/protocol/openid-connect/token"
                        ),
                        "clientId": "bridge-client",
                        "clientSecretRef": "oauth-client-secret",
                        "scopes": ["api.read"],
                        "audience": "knowledge-api",
                        "clientAuthMethod": "client_secret_post",
                    },
                },
                "mapping": {
                    "idField": "employee_id",
                    "titleField": "full_name",
                    "contentTemplate": "{{ full_name }}",
                },
                "output": {
                    "bucket": "gs://company-ingest-relay",
                    "prefix": "hr-employees",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "hr-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "*/30 * * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="hr-employees",
            draft=switch_to_rest_pull_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        rendered = yaml.safe_load(changes["connectors/hr-employees.yaml"])
        source = rendered["spec"]["source"]
        assert rendered["spec"]["mode"] == "rest_pull"
        assert source["type"] == "http"
        assert source["secretRef"] == "kb-api-token"
        assert "query" not in source
        assert source["oauth"]["grantType"] == "client_credentials"
        assert source["oauth"]["clientAuthMethod"] == "client_secret_post"


def test_edit_rest_pull_sparse_draft_preserves_existing_oauth_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "kb-rest.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "kb-rest"},
                    "spec": {
                        "mode": "rest_pull",
                        "schedule": "*/30 * * * *",
                        "source": {
                            "type": "http",
                            "secretRef": "kb-api-token",
                            "url": "https://kb.local/articles",
                            "method": "GET",
                            "watermarkField": "updated_at",
                            "oauth": {
                                "grantType": "client_credentials",
                                "tokenUrl": (
                                    "https://auth.local/realms/acme/"
                                    "protocol/openid-connect/token"
                                ),
                                "clientId": "bridge-client",
                                "clientSecretRef": "oauth-client-secret",
                                "scopes": ["api.read"],
                                "audience": "knowledge-api",
                                "clientAuthMethod": "client_secret_post",
                            },
                        },
                        "mapping": {
                            "idField": "article_id",
                            "titleField": "title",
                            "contentTemplate": "{{ title }}",
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "kb-rest",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "kb-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "kb-rest",
                            "schedule": "*/30 * * * *",
                            "connectorPath": "connectors/kb-rest.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        sparse_edit_draft = {
            "metadata": {"name": "kb-rest"},
            "spec": {
                "mode": "rest_pull",
                "source": {
                    "type": "http",
                    "secretRef": "kb-api-token",
                    "url": "https://kb.local/articles",
                    "method": "GET",
                    "watermarkField": "updated_at",
                },
                "mapping": {
                    "idField": "article_id",
                    "titleField": "title",
                    "contentTemplate": "{{ title }}",
                },
                "output": {
                    "bucket": "gs://pochert-test-bucket",
                    "prefix": "kb-rest",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "kb-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "*/30 * * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="kb-rest",
            draft=sparse_edit_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        rendered = yaml.safe_load(changes["connectors/kb-rest.yaml"])
        oauth = rendered["spec"]["source"]["oauth"]
        assert oauth["grantType"] == "client_credentials"
        assert oauth["tokenUrl"].endswith("/protocol/openid-connect/token")


def test_edit_file_pull_prunes_rest_source_fields_and_sets_csv_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        connectors_dir = root / "connectors"
        connectors_dir.mkdir(parents=True)
        connector_path = connectors_dir / "kb-rest.yaml"
        connector_path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "sync.gemini.io/v1alpha1",
                    "kind": "Connector",
                    "metadata": {"name": "kb-rest"},
                    "spec": {
                        "mode": "rest_pull",
                        "schedule": "*/30 * * * *",
                        "source": {
                            "type": "http",
                            "secretRef": "kb-api-token",
                            "url": "https://kb.local/articles",
                            "method": "GET",
                            "payload": {"scope": "internal"},
                            "paginationCursorField": "cursor",
                            "paginationNextCursorJsonPath": "paging.next_cursor",
                            "headers": {"X-Tenant": "internal"},
                            "oauth": {
                                "grantType": "client_credentials",
                                "tokenUrl": (
                                    "https://auth.local/realms/acme/"
                                    "protocol/openid-connect/token"
                                ),
                                "clientId": "bridge-client",
                            },
                        },
                        "mapping": {
                            "idField": "article_id",
                            "titleField": "title",
                            "contentTemplate": "{{ title }}",
                        },
                        "output": {
                            "bucket": "gs://company-ingest-relay",
                            "prefix": "kb-rest",
                            "format": "ndjson",
                        },
                        "gemini": {
                            "projectId": "my-project",
                            "location": "global",
                            "dataStoreId": "kb-ds",
                        },
                        "reconciliation": {"deletePolicy": "auto_delete_missing"},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        helm_values = root / "values.yaml"
        helm_values.write_text(
            yaml.safe_dump(
                {
                    "scheduleJobs": [
                        {
                            "name": "kb-rest",
                            "schedule": "*/30 * * * *",
                            "connectorPath": "connectors/kb-rest.yaml",
                            "enabled": True,
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        switch_to_file_pull_draft = {
            "metadata": {"name": "kb-rest"},
            "spec": {
                "mode": "file_pull",
                "source": {
                    "type": "http",
                    "path": "./runtime/sources/kb",
                    "glob": "*.csv",
                    "format": "csv",
                },
                "mapping": {
                    "idField": "article_id",
                    "titleField": "title",
                    "contentTemplate": "{{ title }}",
                },
                "output": {
                    "bucket": "gs://company-ingest-relay",
                    "prefix": "kb-rest",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "my-project",
                    "location": "global",
                    "dataStoreId": "kb-ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "*/30 * * * *", "enabled": True},
        }

        changes = build_proposed_file_changes(
            action="edit",
            connector_id="kb-rest",
            draft=switch_to_file_pull_draft,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )

        rendered = yaml.safe_load(changes["connectors/kb-rest.yaml"])
        source = rendered["spec"]["source"]
        assert rendered["spec"]["mode"] == "file_pull"
        assert source["type"] == "file"
        assert source["format"] == "csv"
        assert source["csv"]["documentMode"] == "row"
        assert "url" not in source
        assert "method" not in source
        assert "payload" not in source
        assert "paginationCursorField" not in source
        assert "paginationNextCursorJsonPath" not in source
        assert "headers" not in source
        assert "oauth" not in source
