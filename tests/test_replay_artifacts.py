from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ingest_relay.schemas import CanonicalDocument
from ingest_relay.services.replay import FaultInjectionError, replay_artifacts


def _write_ndjson(path, docs: list[CanonicalDocument]) -> None:
    path.write_text("\n".join(doc.model_dump_json() for doc in docs), encoding="utf-8")


def test_replay_artifacts_is_deterministic(tmp_path) -> None:
    upserts_path = tmp_path / "upserts.ndjson"
    deletes_path = tmp_path / "deletes.ndjson"

    upserts = [
        CanonicalDocument(
            doc_id="connector:1",
            title="One",
            content="content",
            uri=None,
            mime_type="text/plain",
            updated_at=datetime.now(tz=UTC),
            acl_users=[],
            acl_groups=[],
            metadata={"connector_id": "connector"},
            checksum="sha256:one",
            op="UPSERT",
        )
    ]
    deletes = [
        CanonicalDocument(
            doc_id="connector:2",
            title="",
            content="",
            uri=None,
            mime_type="text/plain",
            updated_at=datetime.now(tz=UTC),
            acl_users=[],
            acl_groups=[],
            metadata={"connector_id": "connector"},
            checksum="sha256:two",
            op="DELETE",
        )
    ]

    _write_ndjson(upserts_path, upserts)
    _write_ndjson(deletes_path, deletes)

    digest_a = replay_artifacts(str(upserts_path), str(deletes_path))
    digest_b = replay_artifacts(str(upserts_path), str(deletes_path))

    assert digest_a == digest_b


def test_replay_artifacts_supports_fault_injection(tmp_path) -> None:
    upserts_path = tmp_path / "upserts.ndjson"
    deletes_path = tmp_path / "deletes.ndjson"
    upserts_path.write_text("", encoding="utf-8")
    deletes_path.write_text("", encoding="utf-8")

    with pytest.raises(FaultInjectionError):
        replay_artifacts(
            str(upserts_path),
            str(deletes_path),
            fault_step="load_upserts",
        )
