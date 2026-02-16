from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OpsSummary(BaseModel):
    window_hours: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    running_runs: int
    success_rate_percent: float
    mttr_seconds: int
    freshness_lag_seconds_max: int
    pending_push_batches: int
    generated_at: datetime


class ConnectorHealthRow(BaseModel):
    connector_id: str
    mode: str | None = None
    schedule: str | None = None
    source_type: str | None = None
    last_run_id: str | None = None
    last_status: str | None = None
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_error_class: str | None = None
    checkpoint_watermark: str | None = None
    checkpoint_updated_at: datetime | None = None
    freshness_lag_seconds: int | None = None
    pending_push_batches: int = 0


class RunLinks(BaseModel):
    splunk_url: str | None = None
    kestra_url: str | None = None


class RunRow(BaseModel):
    run_id: str
    connector_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: int | None = None
    upserts_count: int
    deletes_count: int
    error_class: str | None = None
    links: RunLinks = Field(default_factory=RunLinks)


class RunDetail(RunRow):
    error_message: str | None = None


class RunsPage(BaseModel):
    limit_runs: int
    offset_runs: int
    total_runs: int
    has_more: bool


class ConnectorDetail(BaseModel):
    connector: ConnectorHealthRow
    recent_runs: list[RunRow]
    runs_page: RunsPage
    status_filter: str | None = None


class OpsSnapshot(BaseModel):
    summary: OpsSummary
    connectors: list[ConnectorHealthRow]
    recent_runs: list[RunRow]
    runs_page: RunsPage
