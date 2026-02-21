from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from ingest_relay.schemas import CanonicalDocument

ProposalAction = Literal["create", "edit", "clone", "delete", "pause", "resume"]


class ScheduleConfig(BaseModel):
    cron: str
    enabled: bool = True


class ConnectorDraftMetadata(BaseModel):
    name: str


class ConnectorDraft(BaseModel):
    metadata: ConnectorDraftMetadata
    spec: dict[str, Any]
    schedule: ScheduleConfig


class CatalogItem(BaseModel):
    connector_id: str
    mode: str
    schedule: str | None = None
    schedule_enabled: bool = True
    source_type: str | None = None
    last_status: str | None = None
    last_run_id: str | None = None
    last_started_at: datetime | None = None


class CatalogResponse(BaseModel):
    items: list[CatalogItem]
    total: int
    limit: int
    offset: int


class DraftValidationResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    normalized: dict[str, Any] | None = None


class PreviewResponse(BaseModel):
    preview_document: CanonicalDocument


class ProposalRequest(BaseModel):
    action: ProposalAction
    connector_id: str
    new_connector_id: str | None = None
    draft: ConnectorDraft | None = None
    commit_message: str | None = None
    pr_title: str | None = None
    pr_body: str | None = None


class ProposalResponse(BaseModel):
    proposal_id: str
    branch_name: str
    pr_url: str
    changed_files: list[str]
    connector_id: str
    action: ProposalAction


class ManagedSecretMetadata(BaseModel):
    secret_ref: str
    source: Literal["managed", "env"]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SecretsListResponse(BaseModel):
    items: list[ManagedSecretMetadata]


class UpsertSecretRequest(BaseModel):
    secret_ref: str
    secret_value: str


class RunNowResponse(BaseModel):
    request_id: str
    connector_id: str
    status: str


class ConnectorEditorResponse(BaseModel):
    draft: ConnectorDraft


class ValidateDraftRequest(BaseModel):
    draft: ConnectorDraft


class PreviewDraftRequest(BaseModel):
    draft: ConnectorDraft
    sample_record: dict[str, Any] | None = None
