from __future__ import annotations

import httpx

from ingest_relay.adapters import extractors
from ingest_relay.schemas import SourceConfig


def test_extract_rest_rows_paginates_and_tracks_watermark(monkeypatch) -> None:
    calls: list[dict] = []

    responses = [
        httpx.Response(
            status_code=200,
            request=httpx.Request("GET", "https://example.local/items"),
            json={
                "items": [
                    {
                        "id": 1,
                        "title": "First",
                        "updated_at": "2026-02-16T08:00:00+00:00",
                    }
                ],
                "paging": {"next_cursor": "cursor-2"},
            },
        ),
        httpx.Response(
            status_code=200,
            request=httpx.Request("GET", "https://example.local/items"),
            json={
                "items": [
                    {
                        "id": 2,
                        "title": "Second",
                        "updated_at": "2026-02-16T09:00:00+00:00",
                    }
                ],
                "paging": {"next_cursor": None},
            },
        ),
    ]

    def fake_request(client, method, url, **kwargs):
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "token")

    source = SourceConfig(
        type="http",
        secretRef="kb-api-token",
        url="https://example.local/items",
        method="GET",
        watermarkField="updated_at",
        paginationCursorField="cursor",
        paginationNextCursorJsonPath="paging.next_cursor",
    )

    result = extractors.extract_rest_rows(source, "2026-02-16T07:00:00+00:00")

    assert len(result.rows) == 2
    assert result.watermark == "2026-02-16T09:00:00+00:00"
    assert calls[0]["params"]["watermark"] == "2026-02-16T07:00:00+00:00"
    assert calls[1]["params"]["cursor"] == "cursor-2"
