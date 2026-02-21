from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from jinja2 import StrictUndefined, Template

from ingest_relay.schemas import CanonicalDocument, MappingConfig
from ingest_relay.security import validate_prompt_injection_safe


class NormalizationError(RuntimeError):
    pass


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return datetime.now(tz=UTC)


def _normalize_acl(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if item is not None]
    return [str(raw)]


def _checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def normalize_records(
    connector_id: str,
    mapping: MappingConfig,
    source_watermark_field: str | None,
    rows: list[dict[str, Any]],
) -> list[CanonicalDocument]:
    content_template = Template(mapping.content_template, undefined=StrictUndefined)
    uri_template = (
        Template(mapping.uri_template, undefined=StrictUndefined) if mapping.uri_template else None
    )

    docs: list[CanonicalDocument] = []

    for row in rows:
        if mapping.id_field not in row:
            raise NormalizationError(f"Missing id field '{mapping.id_field}' in source record")
        if mapping.title_field not in row:
            raise NormalizationError(
                f"Missing title field '{mapping.title_field}' in source record"
            )

        doc_key = str(row[mapping.id_field])
        doc_id = f"{connector_id}:{doc_key}"
        updated_at_value = row.get(source_watermark_field) if source_watermark_field else None
        updated_at = _parse_datetime(updated_at_value)

        metadata = {"connector_id": connector_id}
        for field_name in mapping.metadata_fields:
            if field_name in row:
                metadata[field_name] = row[field_name]

        payload_for_hash = {
            "doc_id": doc_id,
            "title": str(row[mapping.title_field]),
            "content": content_template.render(**row),
            "uri": uri_template.render(**row) if uri_template else None,
            "mime_type": mapping.mime_type,
            "metadata": metadata,
            "acl_users": (
                _normalize_acl(row.get(mapping.acl_users_field)) if mapping.acl_users_field else []
            ),
            "acl_groups": (
                _normalize_acl(row.get(mapping.acl_groups_field))
                if mapping.acl_groups_field
                else []
            ),
        }
        validate_prompt_injection_safe(
            payload_for_hash["title"],
            payload_for_hash["content"],
        )

        doc = CanonicalDocument(
            doc_id=doc_id,
            title=payload_for_hash["title"],
            content=payload_for_hash["content"],
            uri=payload_for_hash["uri"],
            mime_type=payload_for_hash["mime_type"],
            updated_at=updated_at,
            acl_users=payload_for_hash["acl_users"],
            acl_groups=payload_for_hash["acl_groups"],
            metadata=metadata,
            checksum=_checksum(payload_for_hash),
            op="UPSERT",
        )
        docs.append(doc)

    return docs
