from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Mode = Literal["sql_pull", "rest_pull", "rest_push"]
SourceType = Literal["postgres", "mssql", "mysql", "oracle", "http"]
DeletePolicy = Literal["auto_delete_missing", "soft_delete_only", "never_delete"]
OAuthClientAuthMethod = Literal["client_secret_post", "client_secret_basic"]


class Metadata(BaseModel):
    name: str


class OAuthConfig(BaseModel):
    grant_type: Literal["client_credentials"] = Field(
        default="client_credentials",
        alias="grantType",
    )
    token_url: str = Field(alias="tokenUrl")
    client_id: str = Field(alias="clientId")
    client_secret_ref: str | None = Field(default=None, alias="clientSecretRef")
    scopes: list[str] = Field(default_factory=list)
    audience: str | None = None
    client_auth_method: OAuthClientAuthMethod = Field(
        default="client_secret_post",
        alias="clientAuthMethod",
    )


class SourceConfig(BaseModel):
    type: SourceType
    secret_ref: str = Field(alias="secretRef")
    query: str | None = None
    watermark_field: str | None = Field(default=None, alias="watermarkField")
    url: str | None = None
    method: str = "GET"
    payload: dict[str, Any] | None = None
    pagination_cursor_field: str | None = Field(default=None, alias="paginationCursorField")
    pagination_next_cursor_json_path: str | None = Field(
        default=None, alias="paginationNextCursorJsonPath"
    )
    headers: dict[str, str] = Field(default_factory=dict)
    oauth: OAuthConfig | None = None


class MappingConfig(BaseModel):
    id_field: str = Field(alias="idField")
    title_field: str = Field(alias="titleField")
    content_template: str = Field(alias="contentTemplate")
    uri_template: str | None = Field(default=None, alias="uriTemplate")
    mime_type: str = Field(default="text/plain", alias="mimeType")
    acl_users_field: str | None = Field(default=None, alias="aclUsersField")
    acl_groups_field: str | None = Field(default=None, alias="aclGroupsField")
    metadata_fields: list[str] = Field(default_factory=list, alias="metadataFields")


class OutputConfig(BaseModel):
    bucket: str
    prefix: str
    format: Literal["ndjson"] = "ndjson"


class GeminiConfig(BaseModel):
    project_id: str = Field(alias="projectId")
    location: str
    data_store_id: str = Field(alias="dataStoreId")


class ReconciliationConfig(BaseModel):
    delete_policy: DeletePolicy = Field(default="auto_delete_missing", alias="deletePolicy")


class ConnectorSpec(BaseModel):
    mode: Mode
    schedule: str | None = None
    source: SourceConfig
    mapping: MappingConfig
    output: OutputConfig
    gemini: GeminiConfig
    reconciliation: ReconciliationConfig = Field(default_factory=ReconciliationConfig)

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: str | None, info):
        mode = info.data.get("mode")
        if mode in {"sql_pull", "rest_pull"} and not v:
            raise ValueError("schedule is required for pull connectors")
        return v

    @model_validator(mode="after")
    def validate_mode_source_contract(self) -> ConnectorSpec:
        mode = self.mode
        source_type = self.source.type

        if mode == "sql_pull":
            if source_type not in {"postgres", "mssql", "mysql", "oracle"}:
                raise ValueError(
                    "source.type must be one of postgres/mssql/mysql/oracle for sql_pull mode"
                )
            if not self.source.query:
                raise ValueError("source.query is required for sql_pull mode")

        if mode == "rest_pull":
            if source_type != "http":
                raise ValueError("source.type must be http for rest_pull mode")
            if not self.source.url:
                raise ValueError("source.url is required for rest_pull mode")

        if mode == "rest_push" and source_type != "http":
            raise ValueError("source.type must be http for rest_push mode")

        return self


class ConnectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    api_version: str = Field(alias="apiVersion")
    kind: Literal["Connector"]
    metadata: Metadata
    spec: ConnectorSpec


class CanonicalDocument(BaseModel):
    doc_id: str
    title: str
    content: str
    uri: str | None = None
    mime_type: str = "text/plain"
    updated_at: datetime
    acl_users: list[str] = Field(default_factory=list)
    acl_groups: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    checksum: str
    op: Literal["UPSERT", "DELETE"]


class RunManifest(BaseModel):
    run_id: str
    connector_id: str
    started_at: datetime
    completed_at: datetime
    manifest_path: str
    upserts_path: str
    import_upserts_path: str | None = None
    deletes_path: str
    upserts_count: int
    deletes_count: int
    watermark: str | None = None


class PushResponse(BaseModel):
    accepted: int
    rejected: int
    run_id: str
