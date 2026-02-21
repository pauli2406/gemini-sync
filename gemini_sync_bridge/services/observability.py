from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from gemini_sync_bridge.settings import Settings
from gemini_sync_bridge.utils.http_clients import create_httpx_client

logger = logging.getLogger(__name__)


def send_splunk_event(settings: Settings, event: dict[str, Any]) -> None:
    if not settings.splunk_hec_url or not settings.splunk_hec_token:
        return

    payload = {
        "time": datetime.now(tz=UTC).timestamp(),
        "event": event,
        "source": "ingest-relay",
    }
    headers = {"Authorization": f"Splunk {settings.splunk_hec_token}"}

    try:
        with create_httpx_client(timeout=10) as client:
            response = client.post(settings.splunk_hec_url, headers=headers, json=payload)
            response.raise_for_status()
    except Exception:
        logger.exception("failed_to_send_splunk_event", extra={"event": event})


def send_teams_alert(
    settings: Settings,
    title: str,
    message: str,
    facts: dict[str, str] | None = None,
) -> None:
    if not settings.teams_webhook_url:
        return

    sections = []
    if facts:
        sections.append({"facts": [{"name": k, "value": v} for k, v in facts.items()]})

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "E81123",
        "title": title,
        "text": message,
        "sections": sections,
    }

    try:
        with create_httpx_client(timeout=10) as client:
            response = client.post(settings.teams_webhook_url, json=payload)
            response.raise_for_status()
    except Exception:
        logger.exception("failed_to_send_teams_alert", extra={"title": title})
