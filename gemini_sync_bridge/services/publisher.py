from __future__ import annotations

import base64
import csv
import io
import json
from datetime import UTC, datetime
from typing import Any

from gemini_sync_bridge.adapters.object_store import GCSObjectStore, LocalObjectStore, ObjectStore
from gemini_sync_bridge.schemas import CanonicalDocument, OutputConfig, RunManifest
from gemini_sync_bridge.utils.doc_ids import to_discovery_doc_id


def _canonical_ndjson(docs: list[CanonicalDocument]) -> str:
    return "\n".join(doc.model_dump_json() for doc in docs)


def _non_empty_content(doc: CanonicalDocument) -> str:
    if doc.content and doc.content.strip():
        return doc.content
    if doc.title and doc.title.strip():
        return doc.title
    return doc.doc_id


def _discovery_document_ndjson(docs: list[CanonicalDocument]) -> str:
    lines: list[str] = []
    for doc in docs:
        discovery_doc = {
            "id": to_discovery_doc_id(doc.doc_id),
            "structData": {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "uri": doc.uri,
                "updated_at": doc.updated_at.isoformat(),
                "acl_users": doc.acl_users,
                "acl_groups": doc.acl_groups,
                "metadata": doc.metadata,
                "checksum": doc.checksum,
            },
            "content": {
                "mimeType": doc.mime_type,
                "rawBytes": base64.b64encode(
                    _non_empty_content(doc).encode("utf-8")
                ).decode("ascii"),
            },
        }
        lines.append(json.dumps(discovery_doc, sort_keys=True, ensure_ascii=True))
    return "\n".join(lines)


def _build_uri(bucket: str, relative_path: str) -> str:
    normalized = relative_path.lstrip("/")
    if bucket.startswith("gs://"):
        return f"{bucket.rstrip('/')}/{normalized}"
    if bucket.startswith("file://"):
        return f"{bucket.rstrip('/')}/{normalized}"
    raise ValueError("output.bucket must start with gs:// or file://")


def _build_store(bucket: str) -> ObjectStore:
    if bucket.startswith("gs://"):
        return GCSObjectStore()
    if bucket.startswith("file://"):
        # bucket format: file://<base-path>
        return LocalObjectStore(base_dir=bucket.removeprefix("file://"))
    raise ValueError("Unsupported bucket URI")


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return str(value)


def _csv_snapshot(rows: list[dict[str, Any]]) -> str:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                headers.append(key)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_cell(row.get(key)) for key in headers})
    return buffer.getvalue()


def publish_artifacts(
    connector_id: str,
    output: OutputConfig,
    run_id: str,
    upserts: list[CanonicalDocument],
    deletes: list[CanonicalDocument],
    watermark: str | None,
    started_at: datetime,
) -> RunManifest:
    connector_prefix = output.prefix.strip("/") or connector_id
    run_prefix = f"connectors/{connector_prefix}/runs/{run_id}"
    upserts_uri = _build_uri(output.bucket, f"{run_prefix}/upserts.ndjson")
    import_upserts_uri = _build_uri(output.bucket, f"{run_prefix}/upserts.discovery.ndjson")
    deletes_uri = _build_uri(output.bucket, f"{run_prefix}/deletes.ndjson")
    manifest_uri = _build_uri(output.bucket, f"{run_prefix}/manifest.json")

    store = _build_store(output.bucket)
    store.upload_text(upserts_uri, _canonical_ndjson(upserts), content_type="application/x-ndjson")
    store.upload_text(
        import_upserts_uri,
        _discovery_document_ndjson(upserts),
        content_type="application/x-ndjson",
    )
    store.upload_text(deletes_uri, _canonical_ndjson(deletes), content_type="application/x-ndjson")

    manifest = RunManifest(
        run_id=run_id,
        connector_id=connector_id,
        started_at=started_at,
        completed_at=datetime.now(tz=UTC),
        manifest_path=manifest_uri,
        upserts_path=upserts_uri,
        import_upserts_path=import_upserts_uri,
        deletes_path=deletes_uri,
        upserts_count=len(upserts),
        deletes_count=len(deletes),
        watermark=watermark,
    )
    store.upload_text(
        manifest_uri,
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True),
        content_type="application/json",
    )

    state_manifest = manifest
    if output.publish_latest_alias:
        latest_prefix = f"connectors/{connector_prefix}/latest"
        latest_upserts_uri = _build_uri(output.bucket, f"{latest_prefix}/upserts.ndjson")
        latest_import_upserts_uri = _build_uri(
            output.bucket,
            f"{latest_prefix}/upserts.discovery.ndjson",
        )
        latest_deletes_uri = _build_uri(output.bucket, f"{latest_prefix}/deletes.ndjson")
        latest_manifest_uri = _build_uri(output.bucket, f"{latest_prefix}/manifest.json")

        store.upload_text(
            latest_upserts_uri,
            _canonical_ndjson(upserts),
            content_type="application/x-ndjson",
        )
        store.upload_text(
            latest_import_upserts_uri,
            _discovery_document_ndjson(upserts),
            content_type="application/x-ndjson",
        )
        store.upload_text(
            latest_deletes_uri,
            _canonical_ndjson(deletes),
            content_type="application/x-ndjson",
        )

        state_manifest = manifest.model_copy(
            update={
                "manifest_path": latest_manifest_uri,
                "upserts_path": latest_upserts_uri,
                "import_upserts_path": latest_import_upserts_uri,
                "deletes_path": latest_deletes_uri,
            }
        )
        store.upload_text(
            latest_manifest_uri,
            json.dumps(state_manifest.model_dump(mode="json"), sort_keys=True),
            content_type="application/json",
        )

    state_uri = _build_uri(
        output.bucket,
        f"connectors/{connector_prefix}/state/latest_success.json",
    )
    store.upload_text(
        state_uri,
        json.dumps(state_manifest.model_dump(mode="json"), sort_keys=True),
        content_type="application/json",
    )

    return manifest


def publish_csv_artifacts(
    connector_id: str,
    output: OutputConfig,
    run_id: str,
    rows: list[dict[str, Any]],
    watermark: str | None,
    started_at: datetime,
) -> RunManifest:
    connector_prefix = output.prefix.strip("/") or connector_id
    run_prefix = f"connectors/{connector_prefix}/runs/{run_id}"
    csv_uri = _build_uri(output.bucket, f"{run_prefix}/rows.csv")
    manifest_uri = _build_uri(output.bucket, f"{run_prefix}/manifest.json")

    csv_data = _csv_snapshot(rows)
    store = _build_store(output.bucket)
    store.upload_text(csv_uri, csv_data, content_type="text/csv")

    manifest = RunManifest(
        run_id=run_id,
        connector_id=connector_id,
        started_at=started_at,
        completed_at=datetime.now(tz=UTC),
        manifest_path=manifest_uri,
        csv_path=csv_uri,
        upserts_count=len(rows),
        deletes_count=0,
        watermark=watermark,
    )
    store.upload_text(
        manifest_uri,
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True),
        content_type="application/json",
    )

    state_manifest = manifest
    if output.publish_latest_alias:
        latest_prefix = f"connectors/{connector_prefix}/latest"
        latest_csv_uri = _build_uri(output.bucket, f"{latest_prefix}/rows.csv")
        latest_manifest_uri = _build_uri(output.bucket, f"{latest_prefix}/manifest.json")
        store.upload_text(latest_csv_uri, csv_data, content_type="text/csv")

        state_manifest = manifest.model_copy(
            update={
                "manifest_path": latest_manifest_uri,
                "csv_path": latest_csv_uri,
            }
        )
        store.upload_text(
            latest_manifest_uri,
            json.dumps(state_manifest.model_dump(mode="json"), sort_keys=True),
            content_type="application/json",
        )

    state_uri = _build_uri(
        output.bucket,
        f"connectors/{connector_prefix}/state/latest_success.json",
    )
    store.upload_text(
        state_uri,
        json.dumps(state_manifest.model_dump(mode="json"), sort_keys=True),
        content_type="application/json",
    )

    return manifest
