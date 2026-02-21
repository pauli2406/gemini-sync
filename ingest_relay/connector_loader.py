from __future__ import annotations

from pathlib import Path

import yaml

from ingest_relay.schemas import ConnectorConfig


def load_connector_config(path: str | Path) -> ConnectorConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return ConnectorConfig.model_validate(raw)
