from __future__ import annotations

import httpx
from tenacity import stop_after_attempt, wait_none

from gemini_sync_bridge.adapters.extractors import _request_with_retry


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        self.calls += 1
        request = httpx.Request(method, url)
        if self.calls == 1:
            return httpx.Response(status_code=429, request=request, json={"error": "rate limited"})
        return httpx.Response(status_code=200, request=request, json={"items": []})


def test_request_with_retry_retries_on_429_then_succeeds(monkeypatch) -> None:
    monkeypatch.setattr(_request_with_retry.retry, "wait", wait_none())
    monkeypatch.setattr(_request_with_retry.retry, "stop", stop_after_attempt(2))

    client = FakeClient()
    response = _request_with_retry(client, "GET", "https://example.local")

    assert response.status_code == 200
    assert client.calls == 2
