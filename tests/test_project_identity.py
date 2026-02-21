from __future__ import annotations

import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from gemini_sync_bridge import cli
from gemini_sync_bridge.services import observability


class _RecorderClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __enter__(self) -> _RecorderClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None

    def post(self, url: str, headers: dict[str, str], json: dict[str, Any]):  # type: ignore[override]
        self.calls.append({"url": url, "headers": headers, "json": json})

        class _Response:
            @staticmethod
            def raise_for_status() -> None:
                return None

        return _Response()


def test_pyproject_uses_ingest_relay_identity() -> None:
    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = payload["project"]
    scripts = project["scripts"]

    assert project["name"] == "ingest-relay"
    assert "ingest-relay" in scripts
    assert scripts["ingest-relay"] == "gemini_sync_bridge.cli:app"
    assert "gemini-sync-bridge" not in scripts


def test_splunk_event_source_uses_ingest_relay(monkeypatch) -> None:
    recorder = _RecorderClient()
    monkeypatch.setattr(observability, "create_httpx_client", lambda **_: recorder, raising=False)

    settings = SimpleNamespace(
        splunk_hec_url="https://splunk.example/hec",
        splunk_hec_token="token",
    )
    observability.send_splunk_event(settings, {"status": "SUCCESS"})

    assert recorder.calls
    assert recorder.calls[0]["json"]["source"] == "ingest-relay"


def test_cli_help_uses_ingest_relay_branding() -> None:
    assert cli.app.info.help == "IngestRelay command line interface"
