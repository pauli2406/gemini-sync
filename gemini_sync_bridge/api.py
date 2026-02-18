from __future__ import annotations

import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import yaml
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from gemini_sync_bridge.db import SessionLocal, get_session
from gemini_sync_bridge.models import IdempotencyKey, ManualRunRequest, PushBatch, PushEvent
from gemini_sync_bridge.ops_schemas import ConnectorDetail, OpsSnapshot, RunDetail
from gemini_sync_bridge.schemas import CanonicalDocument, PushResponse
from gemini_sync_bridge.security import PromptInjectionDetectedError, validate_prompt_injection_safe
from gemini_sync_bridge.services.ops import (
    build_connector_detail,
    build_ops_snapshot,
    build_run_detail,
)
from gemini_sync_bridge.services.pipeline import run_connector
from gemini_sync_bridge.services.studio import (
    build_catalog,
    enqueue_manual_run,
    get_connector_editor,
    list_secrets,
    preview_connector_draft,
    propose_connector_change,
    upsert_secret,
    validate_connector_draft,
)
from gemini_sync_bridge.settings import get_settings
from gemini_sync_bridge.studio_schemas import (
    CatalogResponse,
    ConnectorEditorResponse,
    DraftValidationResponse,
    ManagedSecretMetadata,
    PreviewDraftRequest,
    PreviewResponse,
    ProposalRequest,
    ProposalResponse,
    RunNowResponse,
    SecretsListResponse,
    UpsertSecretRequest,
    ValidateDraftRequest,
)
from gemini_sync_bridge.utils.logging import configure_logging
from gemini_sync_bridge.utils.paths import configured_connectors_dir


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


app = FastAPI(title="Gemini Sync Bridge", version="0.1.0", lifespan=lifespan)
SessionDep = Annotated[Session, Depends(get_session)]
PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")


def _connectors_dir() -> Path:
    return configured_connectors_dir()


def _load_connector_mode(connector_id: str) -> str:
    for path in _connectors_dir().glob("*.yaml"):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw.get("metadata", {}).get("name") == connector_id:
            return raw.get("spec", {}).get("mode", "")
    raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")


def _find_connector_path(connector_id: str) -> str:
    for path in _connectors_dir().glob("*.yaml"):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if raw.get("metadata", {}).get("name") == connector_id:
            return str(path)
    raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")


def _execute_manual_run(request_id: str) -> None:
    with SessionLocal() as session:
        request = session.get(ManualRunRequest, request_id)
        if request is None:
            return

        request.status = "RUNNING"
        session.commit()

        try:
            connector_path = _find_connector_path(request.connector_id)
            result = run_connector(connector_path)
            request.status = "SUCCESS"
            request.run_id = result.run_id
            request.finished_at = datetime.now(tz=UTC)
        except Exception as exc:  # noqa: BLE001
            request.status = "FAILED"
            request.error_message = str(exc)
            request.finished_at = datetime.now(tz=UTC)
        finally:
            session.commit()


def _parse_events(content_type: str | None, body: bytes) -> list[dict[str, Any]]:
    if not body:
        return []

    if content_type and "application/x-ndjson" in content_type:
        events: list[dict[str, Any]] = []
        for line in body.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
        return events

    decoded = json.loads(body)
    if isinstance(decoded, dict):
        return [decoded]
    if isinstance(decoded, list):
        return [item for item in decoded if isinstance(item, dict)]

    raise HTTPException(status_code=400, detail="Body must be a JSON object, JSON array, or NDJSON")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/studio/connectors", response_class=HTMLResponse)
def studio_connector_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="studio/connectors.html",
        context={"catalog_endpoint": "/v1/studio/catalog"},
    )


@app.get("/studio/connectors/new", response_class=HTMLResponse)
def studio_connector_new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="studio/wizard.html",
        context={
            "title": "Create Connection Profile",
            "connector_id": "",
            "mode": "create",
            "draft_endpoint": "",
            "validate_endpoint": "/v1/studio/connectors/validate",
            "preview_endpoint": "/v1/studio/connectors/preview",
            "propose_endpoint": "/v1/studio/connectors/propose",
        },
    )


def _studio_connector_page(
    request: Request,
    connector_id: str,
    page_mode: str,
    title: str,
) -> HTMLResponse:
    _find_connector_path(connector_id)
    return templates.TemplateResponse(
        request=request,
        name="studio/wizard.html",
        context={
            "title": title,
            "connector_id": connector_id,
            "mode": page_mode,
            "draft_endpoint": f"/v1/studio/connectors/{connector_id}",
            "validate_endpoint": "/v1/studio/connectors/validate",
            "preview_endpoint": "/v1/studio/connectors/preview",
            "propose_endpoint": "/v1/studio/connectors/propose",
        },
    )


@app.get("/studio/connectors/{connector_id}/edit", response_class=HTMLResponse)
def studio_connector_edit(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "edit", "Edit Connection Profile")


@app.get("/studio/connectors/{connector_id}/clone", response_class=HTMLResponse)
def studio_connector_clone(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "clone", "Clone Connection Profile")


@app.get("/studio/connectors/{connector_id}/delete", response_class=HTMLResponse)
def studio_connector_delete(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "delete", "Delete Connection Profile")


@app.get("/studio/connectors/{connector_id}/pause", response_class=HTMLResponse)
def studio_connector_pause(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "pause", "Pause Connection Profile")


@app.get("/studio/connectors/{connector_id}/resume", response_class=HTMLResponse)
def studio_connector_resume(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "resume", "Resume Connection Profile")


@app.get("/studio/connectors/{connector_id}/run", response_class=HTMLResponse)
def studio_connector_run(request: Request, connector_id: str) -> HTMLResponse:
    return _studio_connector_page(request, connector_id, "run", "Run Connection Profile")


@app.get("/v1/studio/catalog", response_model=CatalogResponse)
def studio_catalog(
    response: Response,
    session: SessionDep,
    status: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100000),
) -> CatalogResponse:
    response.headers["Cache-Control"] = "no-store"
    return build_catalog(
        session,
        status=status,
        mode=mode,
        q=q,
        limit=limit,
        offset=offset,
    )


@app.get("/v1/studio/connectors/{connector_id}", response_model=ConnectorEditorResponse)
def studio_connector_editor(connector_id: str) -> ConnectorEditorResponse:
    try:
        return get_connector_editor(connector_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_id}' not found",
        ) from exc


@app.post("/v1/studio/connectors/validate", response_model=DraftValidationResponse)
def studio_validate_draft(request: ValidateDraftRequest) -> DraftValidationResponse:
    return validate_connector_draft(request.draft)


@app.post("/v1/studio/connectors/preview", response_model=PreviewResponse)
def studio_preview_draft(request: PreviewDraftRequest) -> PreviewResponse:
    try:
        return preview_connector_draft(draft=request.draft, sample_record=request.sample_record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/studio/connectors/propose", response_model=ProposalResponse)
def studio_propose_connector_change(
    request: ProposalRequest,
    session: SessionDep,
) -> ProposalResponse:
    try:
        return propose_connector_change(session, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/v1/studio/connectors/{connector_id}/run-now",
    response_model=RunNowResponse,
    status_code=202,
)
def studio_run_now(
    connector_id: str,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> RunNowResponse:
    _find_connector_path(connector_id)
    response = enqueue_manual_run(session, connector_id)
    background_tasks.add_task(_execute_manual_run, response.request_id)
    return response


@app.get("/v1/studio/secrets", response_model=SecretsListResponse)
def studio_list_secrets(session: SessionDep) -> SecretsListResponse:
    return SecretsListResponse(items=list_secrets(session))


@app.post("/v1/studio/secrets", response_model=ManagedSecretMetadata)
def studio_upsert_secret(
    payload: UpsertSecretRequest,
    session: SessionDep,
) -> ManagedSecretMetadata:
    return upsert_secret(
        session,
        secret_ref=payload.secret_ref,
        secret_value=payload.secret_value,
    )


@app.get("/ops", response_class=HTMLResponse)
def ops_dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="ops/dashboard.html",
        context={
            "snapshot_endpoint": "/v1/ops/snapshot",
            "refresh_ms": 15000,
            "default_limit_runs": 25,
        },
    )


@app.get("/ops/connectors/{connector_id}", response_class=HTMLResponse)
def ops_connector_detail(request: Request, connector_id: str, session: SessionDep) -> HTMLResponse:
    try:
        build_connector_detail(session=session, connector_id=connector_id, limit_runs=1)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_id}' not found",
        ) from exc

    return templates.TemplateResponse(
        request=request,
        name="ops/connector_detail.html",
        context={
            "connector_id": connector_id,
            "detail_endpoint": f"/v1/ops/connectors/{connector_id}",
            "refresh_ms": 15000,
            "default_limit_runs": 25,
        },
    )


@app.get("/ops/runs/{run_id}", response_class=HTMLResponse)
def ops_run_detail(request: Request, run_id: str, session: SessionDep) -> HTMLResponse:
    try:
        build_run_detail(session=session, run_id=run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc

    return templates.TemplateResponse(
        request=request,
        name="ops/run_detail.html",
        context={
            "run_id": run_id,
            "detail_endpoint": f"/v1/ops/runs/{run_id}",
            "refresh_ms": 15000,
        },
    )


@app.get("/v1/ops/snapshot", response_model=OpsSnapshot)
def ops_snapshot(
    response: Response,
    session: SessionDep,
    window_hours: int = Query(default=168, ge=1, le=24 * 30),
    limit_runs: int = Query(default=50, ge=1, le=500),
    offset_runs: int = Query(default=0, ge=0, le=100000),
    status: str | None = Query(default=None),
    connector_id: str | None = Query(default=None),
) -> OpsSnapshot:
    response.headers["Cache-Control"] = "no-store"
    try:
        return build_ops_snapshot(
            session=session,
            window_hours=window_hours,
            limit_runs=limit_runs,
            offset_runs=offset_runs,
            status_filter=status,
            connector_id=connector_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/ops/connectors/{connector_id}", response_model=ConnectorDetail)
def ops_connector_snapshot(
    connector_id: str,
    response: Response,
    session: SessionDep,
    limit_runs: int = Query(default=50, ge=1, le=500),
    offset_runs: int = Query(default=0, ge=0, le=100000),
    status: str | None = Query(default=None),
) -> ConnectorDetail:
    response.headers["Cache-Control"] = "no-store"
    try:
        return build_connector_detail(
            session=session,
            connector_id=connector_id,
            limit_runs=limit_runs,
            offset_runs=offset_runs,
            status_filter=status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Connector '{connector_id}' not found",
        ) from exc


@app.get("/v1/ops/runs/{run_id}", response_model=RunDetail)
def ops_run_snapshot(run_id: str, response: Response, session: SessionDep) -> RunDetail:
    response.headers["Cache-Control"] = "no-store"
    try:
        return build_run_detail(session=session, run_id=run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found") from exc


@app.post("/v1/connectors/{connector_id}/events", response_model=PushResponse)
async def push_events(
    connector_id: str,
    request: Request,
    session: SessionDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PushResponse:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    mode = _load_connector_mode(connector_id)
    if mode != "rest_push":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connector '{connector_id}' is not configured for rest_push mode",
        )

    body = await request.body()
    request_hash = hashlib.sha256(body).hexdigest()

    existing = session.get(IdempotencyKey, idempotency_key)
    if existing:
        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key already used with a different request payload",
            )
        return PushResponse.model_validate(existing.response_json)

    events = _parse_events(request.headers.get("content-type"), body)
    accepted = 0
    rejected = 0
    valid_docs: list[CanonicalDocument] = []

    for raw in events:
        try:
            document = CanonicalDocument.model_validate(raw)
            validate_prompt_injection_safe(document.title, document.content)
            valid_docs.append(document)
            accepted += 1
        except PromptInjectionDetectedError:
            rejected += 1
        except Exception:
            rejected += 1

    run_id = uuid.uuid4().hex
    batch = PushBatch(
        run_id=run_id,
        connector_id=connector_id,
        idempotency_key=idempotency_key,
        status="PENDING",
        accepted=accepted,
        rejected=rejected,
    )
    session.add(batch)

    for doc in valid_docs:
        session.add(
            PushEvent(
                run_id=run_id,
                connector_id=connector_id,
                payload=doc.model_dump(mode="json"),
                processed=False,
            )
        )

    response = PushResponse(accepted=accepted, rejected=rejected, run_id=run_id)
    session.add(
        IdempotencyKey(
            key=idempotency_key,
            connector_id=connector_id,
            request_hash=request_hash,
            response_json=response.model_dump(mode="json"),
        )
    )
    session.commit()

    return response
