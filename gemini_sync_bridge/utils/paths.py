from __future__ import annotations

from pathlib import Path

from gemini_sync_bridge.settings import get_settings

DEFAULT_CONNECTORS_DIR = "connectors"


def configured_connectors_dir(*, cwd: Path | None = None) -> Path:
    configured = get_settings().connectors_dir.strip() or DEFAULT_CONNECTORS_DIR
    path = Path(configured).expanduser()
    if path.is_absolute():
        return path
    return (cwd or Path.cwd()) / path
