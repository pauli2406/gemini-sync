from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from gemini_sync_bridge import api
from gemini_sync_bridge.services import ops, studio
from gemini_sync_bridge.services.studio import build_proposed_file_changes
from gemini_sync_bridge.settings import get_settings


def _write_connector(connectors_dir: Path, connector_id: str, mode: str) -> Path:
    payload = {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": connector_id},
        "spec": {
            "mode": mode,
            "schedule": "*/15 * * * *",
            "source": {
                "type": "http" if mode != "sql_pull" else "postgres",
                "secretRef": "example-secret",
                "url": "https://example.test/api" if mode != "sql_pull" else None,
                "method": "GET" if mode != "sql_pull" else None,
                "query": "SELECT 1" if mode == "sql_pull" else None,
                "watermarkField": "updated_at",
            },
            "mapping": {
                "idField": "id",
                "titleField": "title",
                "contentTemplate": "{{ title }}",
            },
            "output": {
                "bucket": "file://./local-bucket",
                "prefix": connector_id,
                "format": "ndjson",
            },
            "gemini": {
                "projectId": "project",
                "location": "global",
                "dataStoreId": "datastore",
            },
            "reconciliation": {"deletePolicy": "auto_delete_missing"},
        },
    }

    source = payload["spec"]["source"]
    source = {key: value for key, value in source.items() if value is not None}
    payload["spec"]["source"] = source

    path = connectors_dir / f"{connector_id}.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_api_connector_lookup_honors_connectors_dir_env(monkeypatch, tmp_path: Path) -> None:
    connectors_dir = tmp_path / "custom-connectors"
    connectors_dir.mkdir(parents=True)
    connector_path = _write_connector(connectors_dir, "external-api", mode="rest_pull")

    monkeypatch.setenv("CONNECTORS_DIR", str(connectors_dir))

    assert api._find_connector_path("external-api") == str(connector_path)
    assert api._load_connector_mode("external-api") == "rest_pull"


def test_ops_catalog_honors_connectors_dir_env(monkeypatch, tmp_path: Path) -> None:
    connectors_dir = tmp_path / "ops-connectors"
    connectors_dir.mkdir(parents=True)
    _write_connector(connectors_dir, "external-ops", mode="rest_push")

    monkeypatch.setenv("CONNECTORS_DIR", str(connectors_dir))

    catalog = ops._load_connector_catalog()

    assert set(catalog.keys()) == {"external-ops"}
    assert catalog["external-ops"]["mode"] == "rest_push"


def test_studio_document_loader_honors_connectors_dir_env(monkeypatch, tmp_path: Path) -> None:
    connectors_dir = tmp_path / "studio-connectors"
    connectors_dir.mkdir(parents=True)
    _write_connector(connectors_dir, "external-studio", mode="rest_pull")

    monkeypatch.setenv("CONNECTORS_DIR", str(connectors_dir))

    docs = studio._load_connector_documents()

    assert set(docs.keys()) == {"external-studio"}


def test_default_connector_discovery_still_uses_repo_connectors_when_env_unset(monkeypatch) -> None:
    monkeypatch.delenv("CONNECTORS_DIR", raising=False)

    catalog = ops._load_connector_catalog()

    assert "support-push" in catalog


def test_studio_proposals_keep_repo_relative_connector_paths_with_external_source_dir(
    tmp_path: Path,
) -> None:
    connectors_dir = tmp_path / "profiles"
    connectors_dir.mkdir(parents=True)
    helm_values = tmp_path / "values.yaml"
    helm_values.write_text(yaml.safe_dump({"scheduleJobs": []}), encoding="utf-8")

    changes = build_proposed_file_changes(
        action="create",
        connector_id="external-profile",
        draft={
            "metadata": {"name": "external-profile"},
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
                    "uriTemplate": "https://kb.local/articles/{{ article_id }}",
                },
                "output": {
                    "bucket": "file://./local-bucket",
                    "prefix": "external-profile",
                    "format": "ndjson",
                },
                "gemini": {
                    "projectId": "p",
                    "location": "global",
                    "dataStoreId": "ds",
                },
                "reconciliation": {"deletePolicy": "auto_delete_missing"},
            },
            "schedule": {"cron": "*/30 * * * *", "enabled": True},
        },
        connectors_dir=connectors_dir,
        helm_values_path=helm_values,
    )

    assert "connectors/external-profile.yaml" in changes
    assert "profiles/external-profile.yaml" not in changes
