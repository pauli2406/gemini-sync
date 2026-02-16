from __future__ import annotations

import hashlib
import re

_INVALID_DISCOVERY_ID_CHARS = re.compile(r"[^a-zA-Z0-9_-]")


def to_discovery_doc_id(doc_id: str) -> str:
    """Return a Discovery Engine-compatible document id.

    Discovery Engine document ids must match `[a-zA-Z0-9-_]*`.
    """
    normalized = _INVALID_DISCOVERY_ID_CHARS.sub("_", doc_id).strip("_")
    if not normalized:
        normalized = "doc"

    if normalized == doc_id:
        return normalized

    digest = hashlib.sha1(doc_id.encode("utf-8")).hexdigest()[:8]
    return f"{normalized}_{digest}"
