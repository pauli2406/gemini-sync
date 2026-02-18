from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from gemini_sync_bridge.models import ConnectorCheckpoint, PushBatch, RunState
from gemini_sync_bridge.ops_schemas import (
    ConnectorDetail,
    ConnectorHealthRow,
    OpsSnapshot,
    OpsSummary,
    RunDetail,
    RunLinks,
    RunRow,
    RunsPage,
)
from gemini_sync_bridge.services.slo import compute_slo_metrics
from gemini_sync_bridge.settings import get_settings
from gemini_sync_bridge.utils.paths import configured_connectors_dir


def _connectors_dir() -> Path:
    return configured_connectors_dir()


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _normalize_status_filter(status_filter: str | None) -> str | None:
    if not status_filter:
        return None

    normalized = status_filter.strip().upper()
    if normalized not in {"SUCCESS", "FAILED", "RUNNING"}:
        raise ValueError(f"Unsupported status filter: {status_filter}")
    return normalized


def _load_connector_catalog() -> dict[str, dict[str, str | None]]:
    catalog: dict[str, dict[str, str | None]] = {}
    for path in sorted(_connectors_dir().glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue

        metadata = raw.get("metadata", {})
        spec = raw.get("spec", {})
        source = spec.get("source", {}) if isinstance(spec, dict) else {}

        connector_id = metadata.get("name")
        if not connector_id:
            continue

        catalog[connector_id] = {
            "mode": spec.get("mode") if isinstance(spec, dict) else None,
            "schedule": spec.get("schedule") if isinstance(spec, dict) else None,
            "source_type": source.get("type") if isinstance(source, dict) else None,
        }
    return catalog


def _build_run_link(url_template: str, run_id: str) -> str | None:
    template = url_template.strip()
    if not template:
        return None

    if "{run_id}" in template:
        return template.format(run_id=run_id)

    if template.endswith("/"):
        return f"{template}{run_id}"
    return f"{template}/{run_id}"


def _build_run_links(run_id: str) -> RunLinks:
    settings = get_settings()
    return RunLinks(
        splunk_url=_build_run_link(settings.splunk_run_url_template, run_id),
        kestra_url=_build_run_link(settings.kestra_run_url_template, run_id),
    )


def _to_run_row(run: RunState) -> RunRow:
    started_at = _as_utc(run.started_at)
    finished_at = _as_utc(run.finished_at)
    duration_seconds = None
    if started_at and finished_at:
        duration_seconds = int((finished_at - started_at).total_seconds())

    return RunRow(
        run_id=run.run_id,
        connector_id=run.connector_id,
        status=run.status,
        started_at=started_at or datetime.now(tz=UTC),
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        upserts_count=run.upserts_count,
        deletes_count=run.deletes_count,
        error_class=run.error_class,
        links=_build_run_links(run.run_id),
    )


def _collect_connector_rows(
    session: Session,
    now: datetime,
    catalog: dict[str, dict[str, str | None]],
) -> list[ConnectorHealthRow]:
    runs = list(session.execute(select(RunState).order_by(desc(RunState.started_at))).scalars())

    latest_runs: dict[str, RunState] = {}
    for run in runs:
        if run.connector_id not in latest_runs:
            latest_runs[run.connector_id] = run

    checkpoints = {
        checkpoint.connector_id: checkpoint
        for checkpoint in session.execute(select(ConnectorCheckpoint)).scalars()
    }

    pending_by_connector: dict[str, int] = {
        connector_id: count
        for connector_id, count in session.execute(
            select(PushBatch.connector_id, func.count())
            .where(PushBatch.status == "PENDING")
            .group_by(PushBatch.connector_id)
        )
    }

    connector_ids = sorted(
        set(catalog.keys())
        | set(latest_runs.keys())
        | set(checkpoints.keys())
        | set(pending_by_connector.keys())
    )

    rows: list[ConnectorHealthRow] = []
    for connector_id in connector_ids:
        metadata = catalog.get(connector_id, {})
        latest = latest_runs.get(connector_id)
        checkpoint = checkpoints.get(connector_id)
        checkpoint_updated_at = _as_utc(checkpoint.updated_at) if checkpoint else None
        freshness_lag_seconds = None
        if checkpoint_updated_at:
            freshness_lag_seconds = int((now - checkpoint_updated_at).total_seconds())

        rows.append(
            ConnectorHealthRow(
                connector_id=connector_id,
                mode=metadata.get("mode"),
                schedule=metadata.get("schedule"),
                source_type=metadata.get("source_type"),
                last_run_id=latest.run_id if latest else None,
                last_status=latest.status if latest else None,
                last_started_at=_as_utc(latest.started_at) if latest else None,
                last_finished_at=_as_utc(latest.finished_at) if latest else None,
                last_error_class=latest.error_class if latest else None,
                checkpoint_watermark=checkpoint.watermark if checkpoint else None,
                checkpoint_updated_at=checkpoint_updated_at,
                freshness_lag_seconds=freshness_lag_seconds,
                pending_push_batches=pending_by_connector.get(connector_id, 0),
            )
        )

    return rows


def _run_filters(
    *,
    window_start: datetime,
    connector_id: str | None,
    status_filter: str | None,
) -> list[Any]:
    filters: list[Any] = [RunState.started_at >= window_start]
    if connector_id:
        filters.append(RunState.connector_id == connector_id)
    if status_filter:
        filters.append(RunState.status == status_filter)
    return filters


def build_ops_snapshot(
    session: Session,
    window_hours: int = 24 * 7,
    limit_runs: int = 50,
    offset_runs: int = 0,
    status_filter: str | None = None,
    connector_id: str | None = None,
    now: datetime | None = None,
) -> OpsSnapshot:
    now = now or datetime.now(tz=UTC)
    limit_runs = max(1, limit_runs)
    offset_runs = max(0, offset_runs)
    status_filter = _normalize_status_filter(status_filter)

    slo = compute_slo_metrics(session=session, now=now, window_hours=window_hours)

    window_start = now - timedelta(hours=window_hours)
    window_runs = list(
        session.execute(select(RunState).where(RunState.started_at >= window_start)).scalars()
    )
    failed_runs = sum(1 for run in window_runs if run.status == "FAILED")
    running_runs = sum(1 for run in window_runs if run.status == "RUNNING")

    pending_push_batches = int(
        session.execute(
            select(func.count()).select_from(PushBatch).where(PushBatch.status == "PENDING")
        ).scalar_one()
    )

    filters = _run_filters(
        window_start=window_start,
        connector_id=connector_id,
        status_filter=status_filter,
    )

    total_filtered_runs = int(
        session.execute(select(func.count()).select_from(RunState).where(*filters)).scalar_one()
    )

    recent_runs = [
        _to_run_row(run)
        for run in session.execute(
            select(RunState)
            .where(*filters)
            .order_by(desc(RunState.started_at))
            .offset(offset_runs)
            .limit(limit_runs)
        ).scalars()
    ]

    runs_page = RunsPage(
        limit_runs=limit_runs,
        offset_runs=offset_runs,
        total_runs=total_filtered_runs,
        has_more=offset_runs + len(recent_runs) < total_filtered_runs,
    )

    catalog = _load_connector_catalog()
    connectors = _collect_connector_rows(session=session, now=now, catalog=catalog)

    if connector_id:
        connectors = [row for row in connectors if row.connector_id == connector_id]
    if status_filter:
        connectors = [
            row for row in connectors if (row.last_status or "").upper() == status_filter
        ]

    summary = OpsSummary(
        window_hours=window_hours,
        total_runs=slo.total_runs,
        successful_runs=slo.successful_runs,
        failed_runs=failed_runs,
        running_runs=running_runs,
        success_rate_percent=slo.success_rate_percent,
        mttr_seconds=slo.mttr_seconds,
        freshness_lag_seconds_max=slo.freshness_lag_seconds_max,
        pending_push_batches=pending_push_batches,
        generated_at=now,
    )

    return OpsSnapshot(
        summary=summary,
        connectors=connectors,
        recent_runs=recent_runs,
        runs_page=runs_page,
    )


def build_connector_detail(
    session: Session,
    connector_id: str,
    limit_runs: int = 50,
    offset_runs: int = 0,
    status_filter: str | None = None,
    now: datetime | None = None,
) -> ConnectorDetail:
    now = now or datetime.now(tz=UTC)
    limit_runs = max(1, limit_runs)
    offset_runs = max(0, offset_runs)
    status_filter = _normalize_status_filter(status_filter)

    catalog = _load_connector_catalog()
    connectors = _collect_connector_rows(session=session, now=now, catalog=catalog)

    connector_row = next((row for row in connectors if row.connector_id == connector_id), None)
    if connector_row is None:
        raise KeyError(connector_id)

    filters: list[Any] = [RunState.connector_id == connector_id]
    if status_filter:
        filters.append(RunState.status == status_filter)

    total_runs = int(
        session.execute(select(func.count()).select_from(RunState).where(*filters)).scalar_one()
    )

    recent_runs = [
        _to_run_row(run)
        for run in session.execute(
            select(RunState)
            .where(*filters)
            .order_by(desc(RunState.started_at))
            .offset(offset_runs)
            .limit(limit_runs)
        ).scalars()
    ]

    runs_page = RunsPage(
        limit_runs=limit_runs,
        offset_runs=offset_runs,
        total_runs=total_runs,
        has_more=offset_runs + len(recent_runs) < total_runs,
    )

    return ConnectorDetail(
        connector=connector_row,
        recent_runs=recent_runs,
        runs_page=runs_page,
        status_filter=status_filter,
    )


def build_run_detail(session: Session, run_id: str) -> RunDetail:
    run = session.get(RunState, run_id)
    if run is None:
        raise KeyError(run_id)

    row = _to_run_row(run)
    payload: dict[str, Any] = row.model_dump(mode="python")
    payload["error_message"] = run.error_message
    return RunDetail.model_validate(payload)
