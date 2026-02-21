from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ingest_relay.models import ConnectorCheckpoint, RunState


@dataclass
class SLOMetrics:
    window_hours: int
    total_runs: int
    successful_runs: int
    success_rate_percent: float
    mttr_seconds: int
    freshness_lag_seconds_max: int

    def to_dict(self) -> dict:
        return asdict(self)


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _compute_mttr_seconds(runs: list[RunState]) -> int:
    if not runs:
        return 0

    by_connector: dict[str, list[RunState]] = {}
    for run in runs:
        by_connector.setdefault(run.connector_id, []).append(run)

    recovery_durations: list[int] = []

    for connector_runs in by_connector.values():
        ordered = sorted(connector_runs, key=lambda run: _as_utc(run.started_at))
        for index, run in enumerate(ordered):
            if run.status != "FAILED" or run.finished_at is None:
                continue

            next_success = None
            for candidate in ordered[index + 1 :]:
                if candidate.status == "SUCCESS":
                    next_success = candidate
                    break

            if not next_success:
                continue

            delta = _as_utc(next_success.started_at) - _as_utc(run.finished_at)
            recovery_durations.append(int(delta.total_seconds()))

    if not recovery_durations:
        return 0

    return int(sum(recovery_durations) / len(recovery_durations))


def compute_slo_metrics(
    session: Session,
    now: datetime | None = None,
    window_hours: int = 24 * 7,
) -> SLOMetrics:
    now = now or datetime.now(tz=UTC)
    window_start = now - timedelta(hours=window_hours)

    runs = list(
        session.execute(
            select(RunState).where(RunState.started_at >= window_start)
        ).scalars()
    )

    total_runs = len(runs)
    successful_runs = sum(1 for run in runs if run.status == "SUCCESS")
    success_rate_percent = (successful_runs / total_runs * 100) if total_runs else 100.0

    mttr_seconds = _compute_mttr_seconds(runs)

    checkpoints = list(session.execute(select(ConnectorCheckpoint)).scalars())
    if checkpoints:
        freshness_lag_seconds_max = max(
            int((now - _as_utc(checkpoint.updated_at)).total_seconds())
            for checkpoint in checkpoints
        )
    else:
        freshness_lag_seconds_max = 0

    return SLOMetrics(
        window_hours=window_hours,
        total_runs=total_runs,
        successful_runs=successful_runs,
        success_rate_percent=success_rate_percent,
        mttr_seconds=mttr_seconds,
        freshness_lag_seconds_max=freshness_lag_seconds_max,
    )
