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
        assert "infra/helm/gemini-sync-bridge/values.yaml" in create_changes

        # simulate apply of create result
        (connectors_dir / "studio-kb.yaml").write_text(
            create_changes["connectors/studio-kb.yaml"],
            encoding="utf-8",
        )
        helm_values.write_text(
            create_changes["infra/helm/gemini-sync-bridge/values.yaml"], encoding="utf-8"
        )

        pause_changes = build_proposed_file_changes(
            action="pause",
            connector_id="studio-kb",
            draft=None,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        payload = yaml.safe_load(pause_changes["infra/helm/gemini-sync-bridge/values.yaml"])
        assert payload["scheduleJobs"][0]["enabled"] is False

        helm_values.write_text(
            pause_changes["infra/helm/gemini-sync-bridge/values.yaml"], encoding="utf-8"
        )
        resume_changes = build_proposed_file_changes(
            action="resume",
            connector_id="studio-kb",
            draft=None,
            connectors_dir=connectors_dir,
            helm_values_path=helm_values,
        )
        resumed = yaml.safe_load(resume_changes["infra/helm/gemini-sync-bridge/values.yaml"])
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
        payload = yaml.safe_load(delete_changes["infra/helm/gemini-sync-bridge/values.yaml"])
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
                            "bucket": "gs://company-gemini-sync",
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
        assert "infra/helm/gemini-sync-bridge/values.yaml" not in changes

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
