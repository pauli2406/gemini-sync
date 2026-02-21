from __future__ import annotations

import httpx
import pytest

from ingest_relay.adapters import extractors
from ingest_relay.schemas import SourceConfig


def _response(method: str, url: str, status: int, payload: dict | list) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        request=httpx.Request(method, url),
        json=payload,
    )


def _oauth_source(**oauth_overrides) -> SourceConfig:
    oauth = {
        "grantType": "client_credentials",
        "tokenUrl": "https://auth.local/realms/acme/protocol/openid-connect/token",
        "clientId": "bridge-client",
        "clientSecretRef": "oauth-client-secret",
        "clientAuthMethod": "client_secret_post",
        "scopes": ["api.read", "api.write"],
        "audience": "knowledge-api",
    }
    oauth.update(oauth_overrides)

    return SourceConfig(
        type="http",
        secretRef="fallback-secret",
        url="https://api.local/v1/articles",
        method="GET",
        watermarkField="updated_at",
        paginationCursorField="cursor",
        paginationNextCursorJsonPath="paging.next_cursor",
        oauth=oauth,
    )


def test_extract_rest_rows_oauth_client_secret_post(monkeypatch) -> None:
    calls: list[tuple[str, str, dict]] = []

    def fake_request(client, method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "openid-connect/token" in url:
            return _response(
                method,
                url,
                200,
                {
                    "access_token": "oauth-token-1",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        return _response(
            method,
            url,
            200,
            {
                "items": [
                    {
                        "id": 1,
                        "title": "First",
                        "updated_at": "2026-02-16T08:00:00+00:00",
                    }
                ],
                "paging": {"next_cursor": None},
            },
        )

    resolved_refs: list[str] = []

    def fake_resolve_secret(secret_ref: str) -> str:
        resolved_refs.append(secret_ref)
        return "oauth-secret"

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", fake_resolve_secret)

    source = _oauth_source()
    result = extractors.extract_rest_rows(source, "2026-02-16T07:00:00+00:00")

    assert len(result.rows) == 1
    assert result.watermark == "2026-02-16T08:00:00+00:00"
    assert resolved_refs == ["oauth-client-secret"]

    token_call = next(call for call in calls if "openid-connect/token" in call[1])
    token_data = token_call[2]["data"]
    assert token_data["grant_type"] == "client_credentials"
    assert token_data["client_id"] == "bridge-client"
    assert token_data["client_secret"] == "oauth-secret"
    assert token_data["scope"] == "api.read api.write"
    assert token_data["audience"] == "knowledge-api"
    assert token_call[2].get("auth") is None

    api_call = next(call for call in calls if call[1] == "https://api.local/v1/articles")
    assert api_call[2]["headers"]["Authorization"] == "Bearer oauth-token-1"


def test_extract_rest_rows_oauth_client_secret_basic(monkeypatch) -> None:
    calls: list[tuple[str, str, dict]] = []

    def fake_request(client, method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "openid-connect/token" in url:
            return _response(
                method,
                url,
                200,
                {
                    "access_token": "oauth-token-basic",
                    "expires_in": 3600,
                },
            )
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    source = _oauth_source(clientAuthMethod="client_secret_basic")
    extractors.extract_rest_rows(source, None)

    token_call = next(call for call in calls if "openid-connect/token" in call[1])
    assert token_call[2]["auth"] == ("bridge-client", "oauth-secret")
    assert "client_secret" not in token_call[2]["data"]
    assert "client_id" not in token_call[2]["data"]

    api_call = next(call for call in calls if call[1] == "https://api.local/v1/articles")
    assert api_call[2]["headers"]["Authorization"] == "Bearer oauth-token-basic"


def test_extract_rest_rows_oauth_falls_back_to_source_secret_ref(monkeypatch) -> None:
    resolved_refs: list[str] = []

    def fake_resolve_secret(secret_ref: str) -> str:
        resolved_refs.append(secret_ref)
        return "oauth-secret"

    def fake_request(client, method, url, **kwargs):
        if "openid-connect/token" in url:
            return _response(method, url, 200, {"access_token": "oauth-token", "expires_in": 3600})
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", fake_resolve_secret)

    source = _oauth_source(clientSecretRef=None)
    extractors.extract_rest_rows(source, None)

    assert resolved_refs == ["fallback-secret"]


def test_extract_rest_rows_oauth_proactive_refresh_during_pagination(monkeypatch) -> None:
    calls: list[tuple[str, str, dict]] = []
    now = {"value": 1000.0}
    issued = {"count": 0}

    def fake_time() -> float:
        return now["value"]

    def fake_request(client, method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "openid-connect/token" in url:
            issued["count"] += 1
            return _response(
                method,
                url,
                200,
                {
                    "access_token": f"oauth-token-{issued['count']}",
                    "expires_in": 20,
                },
            )

        auth = kwargs["headers"]["Authorization"]
        if kwargs["params"].get("cursor") is None:
            now["value"] += 5
            assert auth == "Bearer oauth-token-1"
            return _response(
                method,
                url,
                200,
                {
                    "items": [{"updated_at": "2026-02-16T08:00:00+00:00"}],
                    "paging": {"next_cursor": "cursor-2"},
                },
            )

        assert auth == "Bearer oauth-token-2"
        return _response(
            method,
            url,
            200,
            {
                "items": [{"updated_at": "2026-02-16T09:00:00+00:00"}],
                "paging": {"next_cursor": None},
            },
        )

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")
    monkeypatch.setattr(extractors.time, "time", fake_time)

    source = _oauth_source()
    result = extractors.extract_rest_rows(source, None)

    assert result.watermark == "2026-02-16T09:00:00+00:00"
    token_calls = [call for call in calls if "openid-connect/token" in call[1]]
    assert len(token_calls) == 2


def test_extract_rest_rows_oauth_refreshes_once_on_401(monkeypatch) -> None:
    calls: list[tuple[str, str, dict]] = []
    issued = {"count": 0}
    api_attempts = {"count": 0}

    def fake_request(client, method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "openid-connect/token" in url:
            issued["count"] += 1
            return _response(
                method,
                url,
                200,
                {
                    "access_token": f"oauth-token-{issued['count']}",
                    "expires_in": 3600,
                },
            )

        api_attempts["count"] += 1
        if api_attempts["count"] == 1:
            return _response(method, url, 401, {"error": "unauthorized"})
        return _response(
            method,
            url,
            200,
            {
                "items": [{"updated_at": "2026-02-16T08:00:00+00:00"}],
                "paging": {"next_cursor": None},
            },
        )

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    source = _oauth_source()
    result = extractors.extract_rest_rows(source, None)

    assert len(result.rows) == 1
    api_calls = [call for call in calls if call[1] == "https://api.local/v1/articles"]
    assert api_calls[0][2]["headers"]["Authorization"] == "Bearer oauth-token-1"
    assert api_calls[1][2]["headers"]["Authorization"] == "Bearer oauth-token-2"


def test_extract_rest_rows_oauth_raises_after_second_401(monkeypatch) -> None:
    def fake_request(client, method, url, **kwargs):
        if "openid-connect/token" in url:
            return _response(method, url, 200, {"access_token": "oauth-token", "expires_in": 3600})
        return _response(method, url, 401, {"error": "unauthorized"})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    source = _oauth_source()
    with pytest.raises(httpx.HTTPStatusError):
        extractors.extract_rest_rows(source, None)


def test_extract_rest_rows_oauth_overrides_manual_authorization_header(monkeypatch) -> None:
    api_headers: list[dict[str, str]] = []

    def fake_request(client, method, url, **kwargs):
        if "openid-connect/token" in url:
            return _response(method, url, 200, {"access_token": "oauth-token", "expires_in": 3600})
        api_headers.append(kwargs["headers"])
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    source = _oauth_source()
    source.headers["Authorization"] = "Bearer manual-token"
    source.headers["X-Tenant"] = "internal"

    extractors.extract_rest_rows(source, None)

    assert api_headers
    assert api_headers[0]["Authorization"] == "Bearer oauth-token"
    assert api_headers[0]["X-Tenant"] == "internal"


def test_extract_rest_rows_without_oauth_keeps_manual_authorization_header(monkeypatch) -> None:
    captured_headers: list[dict[str, str]] = []

    def fake_request(client, method, url, **kwargs):
        captured_headers.append(kwargs["headers"])
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "static-token")

    source = SourceConfig(
        type="http",
        secretRef="kb-api-token",
        url="https://api.local/v1/articles",
        method="GET",
        headers={"Authorization": "Bearer manual-token"},
    )
    extractors.extract_rest_rows(source, None)

    assert captured_headers
    assert captured_headers[0]["Authorization"] == "Bearer manual-token"


def test_extract_rest_rows_oauth_raises_for_non_2xx_token_response(monkeypatch) -> None:
    def fake_request(client, method, url, **kwargs):
        if "openid-connect/token" in url:
            return _response(method, url, 403, {"error": "forbidden"})
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    with pytest.raises(extractors.ExtractionError, match="OAuth token request failed"):
        extractors.extract_rest_rows(_oauth_source(), None)


def test_extract_rest_rows_oauth_raises_for_missing_access_token(monkeypatch) -> None:
    def fake_request(client, method, url, **kwargs):
        if "openid-connect/token" in url:
            return _response(method, url, 200, {"expires_in": 3600})
        return _response(method, url, 200, {"items": []})

    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    with pytest.raises(extractors.ExtractionError, match="access_token"):
        extractors.extract_rest_rows(_oauth_source(), None)
