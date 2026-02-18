from __future__ import annotations

from typing import Any

import httpx


def create_httpx_client(**kwargs: Any) -> httpx.Client:
    """Create outbound HTTPX clients with explicit env-based proxy/CA support."""
    kwargs["trust_env"] = True
    return httpx.Client(**kwargs)
