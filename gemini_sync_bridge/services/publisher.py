from __future__ import annotations

import json
from datetime import UTC, datetime

from gemini_sync_bridge.adapters.object_store import GCSObjectStore, LocalObjectStore, ObjectStore
from gemini_sync_bridge.schemas import CanonicalDocument, OutputConfig, RunManifest


def _ndjson(docs: list[CanonicalDocument]) -> str:
    return "\n".join(doc.model_dump_json() for doc in docs)


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
    deletes_uri = _build_uri(output.bucket, f"{run_prefix}/deletes.ndjson")
    manifest_uri = _build_uri(output.bucket, f"{run_prefix}/manifest.json")

    store = _build_store(output.bucket)
    store.upload_text(upserts_uri, _ndjson(upserts), content_type="application/x-ndjson")
    store.upload_text(deletes_uri, _ndjson(deletes), content_type="application/x-ndjson")

    manifest = RunManifest(
        run_id=run_id,
        connector_id=connector_id,
        started_at=started_at,
        completed_at=datetime.now(tz=UTC),
        manifest_path=manifest_uri,
        upserts_path=upserts_uri,
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

    state_uri = _build_uri(
        output.bucket,
        f"connectors/{connector_prefix}/state/latest_success.json",
    )
    store.upload_text(
        state_uri,
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True),
        content_type="application/json",
    )

    return manifest
