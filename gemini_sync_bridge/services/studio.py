from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, Template, TemplateError, meta
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from gemini_sync_bridge.models import ManualRunRequest, ProposalHistory, RunState
from gemini_sync_bridge.schemas import CanonicalDocument, ConnectorConfig
from gemini_sync_bridge.services.github_pr import GitHubPRService, build_branch_name
from gemini_sync_bridge.services.secrets_registry import ManagedSecretsRegistry
from gemini_sync_bridge.settings import get_settings
from gemini_sync_bridge.studio_schemas import (
    CatalogItem,
    CatalogResponse,
    ConnectorDraft,
    ConnectorEditorResponse,
    DraftValidationResponse,
    ManagedSecretMetadata,
    PreviewResponse,
    ProposalRequest,
    ProposalResponse,
    RunNowResponse,
)


def _repo_root() -> Path:
    return Path.cwd()


def _connectors_dir() -> Path:
    return _repo_root() / "connectors"


def _helm_values_path() -> Path:
    return _repo_root() / "infra/helm/gemini-sync-bridge/values.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_connector_documents(connectors_root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = connectors_root or _connectors_dir()
    docs: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.yaml")):
        payload = _load_yaml(path)
        connector_id = payload.get("metadata", {}).get("name")
        if connector_id:
            docs[connector_id] = payload
    return docs


def _find_connector_document(
    connector_id: str,
    connectors_root: Path | None = None,
) -> dict[str, Any]:
    documents = _load_connector_documents(connectors_root)
    payload = documents.get(connector_id)
    if not payload:
        raise KeyError(connector_id)
    return payload


def _deep_merge_dict(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(current, value)
        else:
            merged[key] = value
    return merged


def _load_schedule_jobs(values_path: Path | None = None) -> list[dict[str, Any]]:
    target = values_path or _helm_values_path()
    payload = _load_yaml(target)
    jobs = payload.get("scheduleJobs", [])
    if isinstance(jobs, list):
        return [job for job in jobs if isinstance(job, dict)]
    return []


def _write_schedule_jobs(values_path: Path, jobs: list[dict[str, Any]]) -> str:
    payload = _load_yaml(values_path)
    payload["scheduleJobs"] = jobs
    return yaml.safe_dump(payload, sort_keys=False)


def _normalize_secret_ref(secret_ref: str) -> str:
    return secret_ref.strip()


def _connector_runtime_payload(draft: ConnectorDraft) -> dict[str, Any]:
    spec = dict(draft.spec)
    mode = spec.get("mode")
    if mode in {"sql_pull", "rest_pull"}:
        spec["schedule"] = draft.schedule.cron
    elif "schedule" in spec:
        spec.pop("schedule")

    return {
        "apiVersion": "sync.gemini.io/v1alpha1",
        "kind": "Connector",
        "metadata": {"name": draft.metadata.name},
        "spec": spec,
    }


def validate_connector_draft(
    draft_payload: dict[str, Any] | ConnectorDraft,
) -> DraftValidationResponse:
    try:
        draft = (
            draft_payload
            if isinstance(draft_payload, ConnectorDraft)
            else ConnectorDraft.model_validate(draft_payload)
        )
    except Exception as exc:  # noqa: BLE001
        return DraftValidationResponse(valid=False, errors=[str(exc)])

    raw = _connector_runtime_payload(draft)
    if not re.match(r"^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$", draft.metadata.name):
        return DraftValidationResponse(
            valid=False,
            errors=["metadata.name must match ^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$"],
        )

    try:
        normalized = ConnectorConfig.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        return DraftValidationResponse(valid=False, errors=[str(exc)])

    warnings: list[str] = []
    if draft.spec.get("reconciliation", {}).get("deletePolicy") == "never_delete":
        warnings.append("Delete reconciliation is disabled (never_delete).")

    return DraftValidationResponse(
        valid=True,
        errors=[],
        warnings=warnings,
        normalized=normalized.model_dump(mode="json", by_alias=True),
    )


def preview_connector_draft(
    *,
    draft: dict[str, Any] | ConnectorDraft,
    sample_record: dict[str, Any] | None = None,
) -> PreviewResponse:
    parsed = draft if isinstance(draft, ConnectorDraft) else ConnectorDraft.model_validate(draft)

    validation = validate_connector_draft(parsed)
    if not validation.valid:
        raise ValueError("Draft is invalid")

    mapping = parsed.spec.get("mapping", {})
    source = parsed.spec.get("source", {})

    row = dict(sample_record or {})
    id_field = mapping.get("idField", "id")
    title_field = mapping.get("titleField", "title")
    watermark_field = source.get("watermarkField") or "updated_at"

    row.setdefault(id_field, "sample-1")
    row.setdefault(title_field, "Sample Document")
    row.setdefault("body", "Sample body")
    row.setdefault(watermark_field, "2026-02-16T08:30:00Z")

    template_env = Environment()
    content_template_text = mapping.get("contentTemplate", "{{ title }}")
    content_ast = template_env.parse(content_template_text)
    for variable in sorted(meta.find_undeclared_variables(content_ast)):
        row.setdefault(variable, f"sample-{variable}")

    uri_template = mapping.get("uriTemplate")
    if uri_template:
        uri_ast = template_env.parse(uri_template)
        for variable in sorted(meta.find_undeclared_variables(uri_ast)):
            row.setdefault(variable, f"sample-{variable}")

    content_template = Template(
        content_template_text,
        undefined=StrictUndefined,
    )
    try:
        content = content_template.render(**row)
    except TemplateError as exc:
        raise ValueError(f"Unable to render content template: {exc}") from exc

    uri = None
    if uri_template:
        try:
            uri = Template(uri_template, undefined=StrictUndefined).render(**row)
        except TemplateError as exc:
            raise ValueError(f"Unable to render URI template: {exc}") from exc

    doc_id = f"{parsed.metadata.name}:{row[id_field]}"
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

    document = CanonicalDocument(
        doc_id=doc_id,
        title=str(row[title_field]),
        content=content,
        uri=uri,
        mime_type="text/plain",
        updated_at=row[watermark_field],
        acl_users=[],
        acl_groups=[],
        metadata={"connector_id": parsed.metadata.name},
        checksum=f"sha256:{checksum}",
        op="UPSERT",
    )
    return PreviewResponse(preview_document=document)


def _target_connector_id(action: str, connector_id: str, draft: ConnectorDraft | None) -> str:
    if action in {"create", "edit", "clone"}:
        if draft is None:
            raise ValueError("draft is required for create/edit/clone")
        return draft.metadata.name
    return connector_id


def _find_job(jobs: list[dict[str, Any]], connector_id: str) -> dict[str, Any] | None:
    for job in jobs:
        name = job.get("name")
        connector_path = job.get("connectorPath")
        if name == connector_id or connector_path == f"connectors/{connector_id}.yaml":
            return job
    return None


def build_proposed_file_changes(
    *,
    action: str,
    connector_id: str,
    draft: dict[str, Any] | ConnectorDraft | None,
    connectors_dir: Path | None = None,
    helm_values_path: Path | None = None,
) -> dict[str, str | None]:
    connectors_root = connectors_dir or _connectors_dir()
    helm_path = helm_values_path or _helm_values_path()
    parsed_draft = None
    if draft is not None:
        parsed_draft = (
            draft
            if isinstance(draft, ConnectorDraft)
            else ConnectorDraft.model_validate(draft)
        )
    if action in {"edit", "clone"} and parsed_draft is not None:
        try:
            existing_payload = _find_connector_document(connector_id, connectors_root)
        except KeyError as exc:
            raise ValueError(f"Connector '{connector_id}' not found") from exc

        existing_spec = existing_payload.get("spec", {})
        if not isinstance(existing_spec, dict):
            existing_spec = {}
        merged_spec = _deep_merge_dict(existing_spec, dict(parsed_draft.spec))
        parsed_draft = ConnectorDraft.model_validate(
            {
                "metadata": {"name": parsed_draft.metadata.name},
                "spec": merged_spec,
                "schedule": {
                    "cron": parsed_draft.schedule.cron,
                    "enabled": parsed_draft.schedule.enabled,
                },
            }
        )

    target_id = _target_connector_id(action, connector_id, parsed_draft)
    changes: dict[str, str | None] = {}

    jobs = _load_schedule_jobs(helm_path)

    if action in {"create", "edit", "clone"}:
        if parsed_draft is None:
            raise ValueError("draft is required")

        connector_payload = _connector_runtime_payload(parsed_draft)
        connector_path = f"connectors/{target_id}.yaml"
        try:
            existing_target_payload = _find_connector_document(target_id, connectors_root)
        except KeyError:
            existing_target_payload = None

        if existing_target_payload != connector_payload:
            changes[connector_path] = yaml.safe_dump(connector_payload, sort_keys=False)

        existing = _find_job(jobs, target_id)
        job_payload = {
            "name": target_id,
            "schedule": parsed_draft.schedule.cron,
            "connectorPath": f"connectors/{target_id}.yaml",
            "enabled": bool(parsed_draft.schedule.enabled),
        }
        if existing:
            existing.update(job_payload)
        else:
            jobs.append(job_payload)

    elif action == "delete":
        changes[f"connectors/{connector_id}.yaml"] = None
        jobs = [
            job
            for job in jobs
            if job.get("name") != connector_id
            and job.get("connectorPath") != f"connectors/{connector_id}.yaml"
        ]

    elif action in {"pause", "resume"}:
        existing = _find_job(jobs, connector_id)
        if not existing:
            raise ValueError(f"No schedule job found for connector '{connector_id}'")
        existing["enabled"] = action == "resume"

    else:
        raise ValueError(f"Unsupported action: {action}")

    current_values_payload = _load_yaml(helm_path)
    rendered_values = _write_schedule_jobs(helm_path, jobs)
    rendered_payload = yaml.safe_load(rendered_values)
    normalized_rendered = rendered_payload if isinstance(rendered_payload, dict) else {}
    if current_values_payload != normalized_rendered:
        changes["infra/helm/gemini-sync-bridge/values.yaml"] = rendered_values

    if not changes:
        raise ValueError("No effective changes detected for proposal")

    return changes


def _read_connector_draft(connector_id: str) -> ConnectorDraft:
    docs = _load_connector_documents()
    payload = docs.get(connector_id)
    if not payload:
        raise KeyError(connector_id)

    spec = dict(payload.get("spec", {}))
    mode = spec.get("mode", "")
    cron = spec.get("schedule") or "*/30 * * * *"
    if mode == "rest_push":
        cron = "*/5 * * * *"

    schedule_enabled = True
    job = _find_job(_load_schedule_jobs(), connector_id)
    if job is not None:
        cron = job.get("schedule", cron)
        schedule_enabled = bool(job.get("enabled", True))

    return ConnectorDraft.model_validate(
        {
            "metadata": {"name": connector_id},
            "spec": spec,
            "schedule": {"cron": cron, "enabled": schedule_enabled},
        }
    )


def get_connector_editor(connector_id: str) -> ConnectorEditorResponse:
    return ConnectorEditorResponse(draft=_read_connector_draft(connector_id))


def build_catalog(
    session: Session,
    *,
    status: str | None = None,
    mode: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> CatalogResponse:
    connector_docs = _load_connector_documents()
    jobs = _load_schedule_jobs()

    latest_runs: dict[str, RunState] = {}
    for run in session.execute(select(RunState).order_by(desc(RunState.started_at))).scalars():
        if run.connector_id not in latest_runs:
            latest_runs[run.connector_id] = run

    items: list[CatalogItem] = []
    for connector_id, payload in connector_docs.items():
        spec = payload.get("spec", {})
        job = _find_job(jobs, connector_id)
        run = latest_runs.get(connector_id)

        items.append(
            CatalogItem(
                connector_id=connector_id,
                mode=str(spec.get("mode", "")),
                schedule=(job or {}).get("schedule") or spec.get("schedule"),
                schedule_enabled=bool((job or {}).get("enabled", True)),
                source_type=(spec.get("source") or {}).get("type"),
                last_status=run.status if run else None,
                last_run_id=run.run_id if run else None,
                last_started_at=run.started_at if run else None,
            )
        )

    filtered: list[CatalogItem] = []
    for item in items:
        if status and (item.last_status or "").upper() != status.upper():
            continue
        if mode and item.mode != mode:
            continue
        if q and q.lower() not in item.connector_id.lower():
            continue
        filtered.append(item)

    total = len(filtered)
    sliced = filtered[offset : offset + limit]
    return CatalogResponse(items=sliced, total=total, limit=limit, offset=offset)


def list_secrets(session: Session) -> list[ManagedSecretMetadata]:
    settings = get_settings()
    registry = ManagedSecretsRegistry(settings.managed_secret_encryption_key)
    managed = registry.list_secrets(session)

    env_refs = []
    for key in sorted(os.environ):
        if key.startswith("SECRET_"):
            env_refs.append(
                ManagedSecretMetadata(
                    secret_ref=key.removeprefix("SECRET_").lower().replace("_", "-"),
                    source="env",
                )
            )

    managed_refs = {row.secret_ref for row in managed}
    merged = managed + [row for row in env_refs if row.secret_ref not in managed_refs]
    return merged


def upsert_secret(session: Session, *, secret_ref: str, secret_value: str) -> ManagedSecretMetadata:
    settings = get_settings()
    registry = ManagedSecretsRegistry(settings.managed_secret_encryption_key)
    metadata = registry.put_secret(
        session,
        secret_ref=_normalize_secret_ref(secret_ref),
        secret_value=secret_value,
    )
    session.commit()
    return metadata


def propose_connector_change(session: Session, request: ProposalRequest) -> ProposalResponse:
    settings = get_settings()
    changes = build_proposed_file_changes(
        action=request.action,
        connector_id=request.connector_id,
        draft=request.draft,
    )

    target_connector_id = request.draft.metadata.name if request.draft else request.connector_id
    branch_name = build_branch_name(action=request.action, connector_id=target_connector_id)
    proposal_id = uuid.uuid4().hex

    github = GitHubPRService(
        settings.github_repo,
        github_token=settings.github_token,
        github_base_branch=settings.github_base_branch,
    )
    response = github.create_proposal(
        action=request.action,
        connector_id=target_connector_id,
        changed_files=list(changes.keys()),
        branch_name=branch_name,
        proposal_id=proposal_id,
        file_changes=changes,
        commit_message=request.commit_message,
        pr_title=request.pr_title,
        pr_body=request.pr_body,
    )

    session.add(
        ProposalHistory(
            proposal_id=response.proposal_id,
            action=request.action,
            connector_id=target_connector_id,
            branch_name=response.branch_name,
            pr_url=response.pr_url,
            status="PROPOSED",
        )
    )
    session.commit()
    return response


def enqueue_manual_run(session: Session, connector_id: str) -> RunNowResponse:
    request_id = uuid.uuid4().hex
    row = ManualRunRequest(
        request_id=request_id,
        connector_id=connector_id,
        status="QUEUED",
        created_at=datetime.now(tz=UTC),
    )
    session.add(row)
    session.commit()

    return RunNowResponse(request_id=request_id, connector_id=connector_id, status=row.status)
