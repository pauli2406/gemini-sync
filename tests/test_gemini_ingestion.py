from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from ingest_relay.schemas import CanonicalDocument, GeminiConfig, RunManifest
from ingest_relay.services.gemini_ingestion import GeminiIngestionClient
from ingest_relay.utils.doc_ids import to_discovery_doc_id


def _client(dry_run: bool = False) -> GeminiIngestionClient:
    return GeminiIngestionClient(SimpleNamespace(gemini_ingestion_dry_run=dry_run))


def test_documents_base_uses_global_endpoint_for_global_location() -> None:
    client = _client()
    gemini = GeminiConfig.model_validate(
        {"projectId": "p", "location": "global", "dataStoreId": "ds"}
    )

    base = client._documents_base(gemini)

    assert base.startswith("https://discoveryengine.googleapis.com/v1/projects/p/locations/global/")


def test_documents_base_uses_regional_endpoint_for_eu_location() -> None:
    client = _client()
    gemini = GeminiConfig.model_validate({"projectId": "p", "location": "eu", "dataStoreId": "ds"})

    base = client._documents_base(gemini)

    assert base.startswith("https://eu-discoveryengine.googleapis.com/v1/projects/p/locations/eu/")


def test_import_documents_uses_document_schema_when_manifest_has_discovery_path() -> None:
    client = _client(dry_run=False)
    gemini = GeminiConfig.model_validate(
        {"projectId": "p", "location": "eu", "dataStoreId": "ds"}
    )
    manifest = RunManifest(
        run_id="r1",
        connector_id="hr-employees",
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC),
        manifest_path="gs://b/manifest.json",
        upserts_path="gs://b/upserts.ndjson",
        import_upserts_path="gs://b/upserts.discovery.ndjson",
        deletes_path="gs://b/deletes.ndjson",
        upserts_count=1,
        deletes_count=0,
        watermark=None,
    )

    captured_payload: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs):
        captured_payload.update(kwargs.get("json", {}))
        return SimpleNamespace(json=lambda: {})

    client._request = fake_request  # type: ignore[assignment]

    client.import_documents(gemini, manifest)

    assert captured_payload["gcsSource"] == {
        "inputUris": ["gs://b/upserts.discovery.ndjson"],
        "dataSchema": "document",
    }
    assert "idField" not in captured_payload


def test_import_documents_falls_back_to_custom_schema_for_legacy_manifest() -> None:
    client = _client(dry_run=False)
    gemini = GeminiConfig.model_validate(
        {"projectId": "p", "location": "eu", "dataStoreId": "ds"}
    )
    manifest = RunManifest(
        run_id="r1",
        connector_id="hr-employees",
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC),
        manifest_path="gs://b/manifest.json",
        upserts_path="gs://b/upserts.ndjson",
        deletes_path="gs://b/deletes.ndjson",
        upserts_count=1,
        deletes_count=0,
        watermark=None,
    )

    captured_payload: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs):
        captured_payload.update(kwargs.get("json", {}))
        return SimpleNamespace(json=lambda: {})

    client._request = fake_request  # type: ignore[assignment]

    client.import_documents(gemini, manifest)

    assert captured_payload["idField"] == "_id"
    assert captured_payload["gcsSource"] == {
        "inputUris": ["gs://b/upserts.ndjson"],
        "dataSchema": "custom",
    }


def test_delete_documents_uses_discovery_safe_doc_id() -> None:
    client = _client(dry_run=False)
    gemini = GeminiConfig.model_validate(
        {"projectId": "p", "location": "eu", "dataStoreId": "ds"}
    )
    doc = CanonicalDocument(
        doc_id="hr-employees:1001",
        title="",
        content="",
        uri=None,
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": "hr-employees"},
        checksum="sha256:test",
        op="DELETE",
    )

    captured: list[tuple[str, str]] = []

    def fake_request(method: str, url: str, **kwargs):
        captured.append((method, url))
        return SimpleNamespace(json=lambda: {})

    client._request = fake_request  # type: ignore[assignment]

    client.delete_documents(gemini, [doc])

    assert captured
    method, url = captured[0]
    assert method == "DELETE"
    assert url.endswith(to_discovery_doc_id("hr-employees:1001"))
