from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gemini_sync_bridge.schemas import CanonicalDocument


class FaultInjectionError(RuntimeError):
    pass


def _maybe_inject_fault(step: str, fault_step: str | None) -> None:
    if fault_step and step == fault_step:
        raise FaultInjectionError(f"Injected fault at step: {step}")


def _normalize_path(path: str) -> Path:
    if path.startswith("file://"):
        return Path(path.removeprefix("file://"))
    return Path(path)


def _load_ndjson(path: str, fault_step: str | None, step_name: str) -> list[CanonicalDocument]:
    _maybe_inject_fault(step_name, fault_step)

    resolved = _normalize_path(path)
    if not resolved.exists():
        return []

    docs: list[CanonicalDocument] = []
    for line in resolved.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        docs.append(CanonicalDocument.model_validate_json(line))
    return docs


def replay_artifacts(
    upserts_path: str,
    deletes_path: str,
    fault_step: str | None = None,
) -> str:
    upserts = _load_ndjson(upserts_path, fault_step=fault_step, step_name="load_upserts")
    deletes = _load_ndjson(deletes_path, fault_step=fault_step, step_name="load_deletes")

    _maybe_inject_fault("digest", fault_step)

    canonical = [
        {
            "doc_id": doc.doc_id,
            "op": doc.op,
            "checksum": doc.checksum,
            "updated_at": doc.updated_at.isoformat(),
        }
        for doc in (upserts + deletes)
    ]
    canonical_sorted = sorted(
        canonical,
        key=lambda item: (item["op"], item["doc_id"], item["checksum"]),
    )

    payload = json.dumps(canonical_sorted, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
