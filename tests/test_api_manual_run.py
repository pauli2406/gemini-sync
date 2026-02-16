from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from gemini_sync_bridge import api
from gemini_sync_bridge.models import Base, ManualRunRequest


def _session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    return engine, session_local


def test_find_connector_path_raises_for_unknown_connector() -> None:
    with pytest.raises(HTTPException) as exc:
        api._find_connector_path("does-not-exist")

    assert exc.value.status_code == 404


def test_execute_manual_run_success_updates_request(monkeypatch) -> None:
    engine, session_local = _session_factory()
    with session_local() as session:
        session.add(
            ManualRunRequest(
                request_id="req-1",
                connector_id="support-push",
                status="QUEUED",
            )
        )
        session.commit()

    monkeypatch.setattr(api, "SessionLocal", session_local)
    monkeypatch.setattr(api, "_find_connector_path", lambda _: "connectors/support-push.yaml")
    monkeypatch.setattr(api, "run_connector", lambda _: SimpleNamespace(run_id="run-1"))

    api._execute_manual_run("req-1")

    with session_local() as session:
        row = session.get(ManualRunRequest, "req-1")
        assert row is not None
        assert row.status == "SUCCESS"
        assert row.run_id == "run-1"
        assert row.finished_at is not None

    engine.dispose()


def test_execute_manual_run_failure_marks_request_failed(monkeypatch) -> None:
    engine, session_local = _session_factory()
    with session_local() as session:
        session.add(
            ManualRunRequest(
                request_id="req-2",
                connector_id="support-push",
                status="QUEUED",
            )
        )
        session.commit()

    monkeypatch.setattr(api, "SessionLocal", session_local)
    monkeypatch.setattr(api, "_find_connector_path", lambda _: "connectors/support-push.yaml")

    def _raise(_: str):
        raise RuntimeError("ingest failed")

    monkeypatch.setattr(api, "run_connector", _raise)
    api._execute_manual_run("req-2")

    with session_local() as session:
        row = session.get(ManualRunRequest, "req-2")
        assert row is not None
        assert row.status == "FAILED"
        assert row.error_message == "ingest failed"
        assert row.finished_at is not None

    engine.dispose()


def test_execute_manual_run_ignores_unknown_request(monkeypatch) -> None:
    engine, session_local = _session_factory()
    monkeypatch.setattr(api, "SessionLocal", session_local)

    api._execute_manual_run("missing")

    with session_local() as session:
        row = session.get(ManualRunRequest, "missing")
        assert row is None

    engine.dispose()
