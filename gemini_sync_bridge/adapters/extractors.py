from __future__ import annotations

import time
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import create_engine, text
from tenacity import retry, stop_after_attempt, wait_exponential

from gemini_sync_bridge.schemas import SourceConfig
from gemini_sync_bridge.utils.secrets import resolve_secret


class ExtractionError(RuntimeError):
    pass


class PullResult:
    def __init__(self, rows: list[dict[str, Any]], watermark: str | None):
        self.rows = rows
        self.watermark = watermark


def _as_iso(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()
    return str(value)


def _max_watermark(
    rows: Iterable[dict[str, Any]],
    watermark_field: str | None,
    fallback: str | None,
) -> str | None:
    if not watermark_field:
        return fallback

    values: list[str] = []
    for row in rows:
        if watermark_field in row and row[watermark_field] is not None:
            values.append(_as_iso(row[watermark_field]))

    if not values:
        return fallback
    return max(values)


def extract_sql_rows(source: SourceConfig, current_watermark: str | None) -> PullResult:
    if not source.query:
        raise ExtractionError("source.query is required for sql_pull mode")

    dsn = resolve_secret(source.secret_ref)
    try:
        engine = create_engine(dsn, future=True)
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(
            f"Invalid DSN for SQL source type '{source.type}': {exc}"
        ) from exc
    params = {"watermark": current_watermark}

    try:
        with engine.connect() as conn:
            result = conn.execute(text(source.query), params)
            rows = [dict(row._mapping) for row in result]
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(
            f"SQL extraction failed for source type '{source.type}': {exc}"
        ) from exc

    watermark = _max_watermark(rows, source.watermark_field, current_watermark)
    return PullResult(rows=rows, watermark=watermark)


def _extract_json_path(data: dict[str, Any], dotted_path: str) -> Any:
    cursor: Any = data
    for part in dotted_path.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3), reraise=True)
def _request_with_retry(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    response = client.request(method, url, **kwargs)
    if response.status_code >= 500 or response.status_code == 429:
        response.raise_for_status()
    return response


def _coerce_expires_in(raw: Any, default: int = 300) -> int:
    try:
        expires = int(float(raw))
    except (TypeError, ValueError):
        return default
    return expires if expires > 0 else default


class OAuthClientCredentialsTokenProvider:
    def __init__(self, source: SourceConfig, client: httpx.Client) -> None:
        self.source = source
        self.client = client
        self._access_token: str | None = None
        self._token_type: str = "Bearer"
        self._expires_at: float = 0.0
        self._refresh_window_seconds = 30

    def authorization_header(self, *, force_refresh: bool = False) -> str:
        if force_refresh or self._needs_refresh():
            self._refresh_token()
        if not self._access_token:
            raise ExtractionError("OAuth token provider failed to acquire an access token.")
        return f"{self._token_type} {self._access_token}"

    def _needs_refresh(self) -> bool:
        if not self._access_token:
            return True
        return (self._expires_at - time.time()) <= self._refresh_window_seconds

    def _refresh_token(self) -> None:
        oauth = self.source.oauth
        if oauth is None:
            raise ExtractionError("OAuth configuration is required for token refresh.")

        secret_ref = oauth.client_secret_ref or self.source.secret_ref
        if not secret_ref:
            raise ExtractionError(
                "OAuth client secret reference is required. "
                "Set source.secretRef or source.oauth.clientSecretRef."
            )
        client_secret = resolve_secret(secret_ref)

        form_data: dict[str, str] = {"grant_type": oauth.grant_type}
        if oauth.scopes:
            form_data["scope"] = " ".join(scope.strip() for scope in oauth.scopes if scope.strip())
        if oauth.audience:
            form_data["audience"] = oauth.audience

        auth: tuple[str, str] | None = None
        if oauth.client_auth_method == "client_secret_post":
            form_data["client_id"] = oauth.client_id
            form_data["client_secret"] = client_secret
        else:
            auth = (oauth.client_id, client_secret)

        response = _request_with_retry(
            self.client,
            "POST",
            oauth.token_url,
            data=form_data,
            auth=auth,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if response.status_code >= 400:
            raise ExtractionError(f"OAuth token request failed with status {response.status_code}.")

        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ExtractionError("OAuth token response was not valid JSON.") from exc

        if not isinstance(payload, dict):
            raise ExtractionError("OAuth token response must be a JSON object.")

        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise ExtractionError("OAuth token response missing required 'access_token' field.")

        token_type = payload.get("token_type")
        if isinstance(token_type, str) and token_type.strip():
            self._token_type = token_type.strip()
        else:
            self._token_type = "Bearer"

        expires_in = _coerce_expires_in(payload.get("expires_in"), default=300)
        self._access_token = access_token
        self._expires_at = time.time() + expires_in


def extract_rest_rows(source: SourceConfig, current_watermark: str | None) -> PullResult:
    if not source.url:
        raise ExtractionError("source.url is required for rest_pull mode")

    rows: list[dict[str, Any]] = []
    cursor: str | None = None

    with httpx.Client(timeout=30.0) as client:
        headers = dict(source.headers)
        headers.setdefault("Accept", "application/json")

        oauth_provider: OAuthClientCredentialsTokenProvider | None = None
        if source.oauth:
            oauth_provider = OAuthClientCredentialsTokenProvider(source, client)
        else:
            token = resolve_secret(source.secret_ref)
            headers.setdefault("Authorization", f"Bearer {token}")

        def _request_headers(*, force_oauth_refresh: bool = False) -> dict[str, str]:
            request_headers = dict(headers)
            if oauth_provider:
                request_headers["Authorization"] = oauth_provider.authorization_header(
                    force_refresh=force_oauth_refresh
                )
            return request_headers

        while True:
            params: dict[str, Any] = {}
            if current_watermark:
                params["watermark"] = current_watermark
            if cursor and source.pagination_cursor_field:
                params[source.pagination_cursor_field] = cursor

            response = _request_with_retry(
                client,
                source.method,
                source.url,
                headers=_request_headers(),
                params=params,
                json=source.payload,
            )
            if oauth_provider and response.status_code == 401:
                response = _request_with_retry(
                    client,
                    source.method,
                    source.url,
                    headers=_request_headers(force_oauth_refresh=True),
                    params=params,
                    json=source.payload,
                )
            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, list):
                page_rows = payload
            elif isinstance(payload, dict):
                page_rows = payload.get("items", [])
            else:
                raise ExtractionError(
                    "Unsupported REST payload. Expected list or object with 'items'."
                )

            if not isinstance(page_rows, list):
                raise ExtractionError("REST 'items' must be a list")

            rows.extend([item for item in page_rows if isinstance(item, dict)])

            next_cursor = None
            if source.pagination_next_cursor_json_path and isinstance(payload, dict):
                next_cursor = _extract_json_path(payload, source.pagination_next_cursor_json_path)
            if not next_cursor:
                break
            cursor = str(next_cursor)

    watermark = _max_watermark(rows, source.watermark_field, current_watermark)
    return PullResult(rows=rows, watermark=watermark)
