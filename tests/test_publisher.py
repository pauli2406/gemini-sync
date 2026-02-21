from __future__ import annotations

import base64
import csv
import io
import json
from datetime import UTC, datetime

from ingest_relay.adapters.object_store import ObjectLocation
from ingest_relay.schemas import CanonicalDocument, OutputConfig
from ingest_relay.services import publisher
from ingest_relay.services.publisher import _canonical_ndjson, _discovery_document_ndjson
from ingest_relay.utils.doc_ids import to_discovery_doc_id


def _sample_doc(*, content: str = "Engineering Manager profile") -> CanonicalDocument:
    return CanonicalDocument(
        doc_id="hr-employees:1001",
        title="Jane Doe",
        content=content,
        uri="https://hr.internal/employees/1001",
        mime_type="text/plain",
        updated_at=datetime.now(tz=UTC),
        acl_users=["jane@company.com"],
        acl_groups=["eng-managers"],
        metadata={"connector_id": "hr-employees"},
        checksum="sha256:abc",
        op="UPSERT",
    )


def test_discovery_document_ndjson_contains_content_and_safe_id() -> None:
    doc = _sample_doc()

    payload = json.loads(_discovery_document_ndjson([doc]).splitlines()[0])

    assert payload["id"] == to_discovery_doc_id(doc.doc_id)
    assert payload["content"]["mimeType"] == "text/plain"
    decoded = base64.b64decode(payload["content"]["rawBytes"]).decode("utf-8")
    assert decoded == doc.content
    assert payload["structData"]["doc_id"] == doc.doc_id


def test_discovery_document_ndjson_uses_title_when_content_empty() -> None:
    doc = _sample_doc(content="")

    payload = json.loads(_discovery_document_ndjson([doc]).splitlines()[0])
    decoded = base64.b64decode(payload["content"]["rawBytes"]).decode("utf-8")

    assert decoded == doc.title


def test_canonical_ndjson_keeps_internal_shape() -> None:
    doc = _sample_doc()

    payload = json.loads(_canonical_ndjson([doc]).splitlines()[0])

    assert payload["doc_id"] == doc.doc_id
    assert "id" not in payload
    assert "content" in payload


def test_publish_artifacts_writes_latest_alias_and_state_pointer(monkeypatch) -> None:
    uploads: list[tuple[str, str, str]] = []

    class FakeStore:
        def upload_text(
            self,
            uri: str,
            data: str,
            content_type: str = "application/json",
        ) -> ObjectLocation:
            uploads.append((uri, data, content_type))
            return ObjectLocation(uri=uri)

    monkeypatch.setattr(publisher, "_build_store", lambda bucket: FakeStore())

    output = OutputConfig.model_validate(
        {
            "bucket": "gs://company-ingest-relay",
            "prefix": "oracle-qn-data-march-2025",
            "format": "ndjson",
            "publishLatestAlias": True,
        }
    )
    run_id = "run-123"
    manifest = publisher.publish_artifacts(
        connector_id="oracle-qn-data-march-2025",
        output=output,
        run_id=run_id,
        upserts=[_sample_doc()],
        deletes=[],
        watermark="2025-03-31T23:59:59+00:00",
        started_at=datetime.now(tz=UTC),
    )

    uploaded_uris = [uri for uri, _, _ in uploads]
    assert (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/upserts.ndjson"
        in uploaded_uris
    )
    assert (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/"
        "upserts.discovery.ndjson" in uploaded_uris
    )
    assert (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/deletes.ndjson"
        in uploaded_uris
    )
    assert (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/manifest.json"
        in uploaded_uris
    )

    assert (
        manifest.manifest_path
        == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/runs/run-123/manifest.json"
    )
    state_payload = json.loads(
        next(
            data
            for uri, data, _ in uploads
            if uri
            == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/state/latest_success.json"
        )
    )
    assert (
        state_payload["manifest_path"]
        == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/manifest.json"
    )


def test_publish_artifacts_skips_latest_alias_when_disabled(monkeypatch) -> None:
    uploads: list[tuple[str, str, str]] = []

    class FakeStore:
        def upload_text(
            self,
            uri: str,
            data: str,
            content_type: str = "application/json",
        ) -> ObjectLocation:
            uploads.append((uri, data, content_type))
            return ObjectLocation(uri=uri)

    monkeypatch.setattr(publisher, "_build_store", lambda bucket: FakeStore())

    output = OutputConfig.model_validate(
        {
            "bucket": "gs://company-ingest-relay",
            "prefix": "oracle-qn-data-march-2025",
            "format": "ndjson",
        }
    )
    publisher.publish_artifacts(
        connector_id="oracle-qn-data-march-2025",
        output=output,
        run_id="run-123",
        upserts=[_sample_doc()],
        deletes=[],
        watermark=None,
        started_at=datetime.now(tz=UTC),
    )

    uploaded_uris = [uri for uri, _, _ in uploads]
    assert not any("/latest/" in uri for uri in uploaded_uris)


def test_publish_csv_artifacts_writes_all_fields_and_latest_alias(monkeypatch) -> None:
    uploads: list[tuple[str, str, str]] = []

    class FakeStore:
        def upload_text(
            self,
            uri: str,
            data: str,
            content_type: str = "application/json",
        ) -> ObjectLocation:
            uploads.append((uri, data, content_type))
            return ObjectLocation(uri=uri)

    monkeypatch.setattr(publisher, "_build_store", lambda bucket: FakeStore())

    output = OutputConfig.model_validate(
        {
            "bucket": "gs://company-ingest-relay",
            "prefix": "oracle-qn-data-march-2025",
            "format": "csv",
            "publishLatestAlias": True,
        }
    )
    rows = [
        {"notiz_id": 1, "autor": "Ada", "notiz": "First"},
        {"notiz_id": 2, "autor": "Grace", "business_unit": "BU-A"},
    ]

    manifest = publisher.publish_csv_artifacts(
        connector_id="oracle-qn-data-march-2025",
        output=output,
        run_id="run-123",
        rows=rows,
        watermark="2025-03-31T23:59:59+00:00",
        started_at=datetime.now(tz=UTC),
    )

    run_csv_uri = (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/runs/run-123/rows.csv"
    )
    csv_payload = next(data for uri, data, _ in uploads if uri == run_csv_uri)
    reader = csv.DictReader(io.StringIO(csv_payload))
    parsed_rows = list(reader)
    assert reader.fieldnames is not None
    assert reader.fieldnames == ["notiz_id", "autor", "notiz", "business_unit"]
    assert parsed_rows[0]["notiz_id"] == "1"
    assert parsed_rows[0]["business_unit"] == ""
    assert parsed_rows[1]["notiz"] == ""
    assert parsed_rows[1]["business_unit"] == "BU-A"

    assert (
        manifest.csv_path
        == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/runs/run-123/rows.csv"
    )
    assert manifest.upserts_count == 2

    uploaded_uris = [uri for uri, _, _ in uploads]
    assert (
        "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/rows.csv"
        in uploaded_uris
    )
    state_payload = json.loads(
        next(
            data
            for uri, data, _ in uploads
            if uri
            == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/state/latest_success.json"
        )
    )
    assert (
        state_payload["csv_path"]
        == "gs://company-ingest-relay/connectors/oracle-qn-data-march-2025/latest/rows.csv"
    )


def test_publish_csv_artifacts_skips_latest_alias_when_disabled(monkeypatch) -> None:
    uploads: list[tuple[str, str, str]] = []

    class FakeStore:
        def upload_text(
            self,
            uri: str,
            data: str,
            content_type: str = "application/json",
        ) -> ObjectLocation:
            uploads.append((uri, data, content_type))
            return ObjectLocation(uri=uri)

    monkeypatch.setattr(publisher, "_build_store", lambda bucket: FakeStore())

    output = OutputConfig.model_validate(
        {
            "bucket": "gs://company-ingest-relay",
            "prefix": "oracle-qn-data-march-2025",
            "format": "csv",
        }
    )
    publisher.publish_csv_artifacts(
        connector_id="oracle-qn-data-march-2025",
        output=output,
        run_id="run-123",
        rows=[{"id": 1, "title": "A"}],
        watermark=None,
        started_at=datetime.now(tz=UTC),
    )

    uploaded_uris = [uri for uri, _, _ in uploads]
    assert not any("/latest/" in uri for uri in uploaded_uris)
