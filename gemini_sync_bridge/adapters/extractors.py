from __future__ import annotations

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
    engine = create_engine(dsn, future=True)
    params = {"watermark": current_watermark}

    with engine.connect() as conn:
        result = conn.execute(text(source.query), params)
        rows = [dict(row._mapping) for row in result]

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


def extract_rest_rows(source: SourceConfig, current_watermark: str | None) -> PullResult:
    if not source.url:
        raise ExtractionError("source.url is required for rest_pull mode")

    token = resolve_secret(source.secret_ref)
    headers = dict(source.headers)
    headers.setdefault("Authorization", f"Bearer {token}")
    headers.setdefault("Accept", "application/json")

    rows: list[dict[str, Any]] = []
    cursor: str | None = None

    with httpx.Client(timeout=30.0) as client:
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
                headers=headers,
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
