from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from gemini_sync_bridge.models import Base
from gemini_sync_bridge.services.secrets_registry import ManagedSecretsRegistry
from gemini_sync_bridge.utils import secrets as secrets_utils


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


def test_resolve_secret_prefers_managed_secret(monkeypatch) -> None:
    engine, session_local = _session_factory()
    registry = ManagedSecretsRegistry(encryption_key="test-key")
    with session_local() as session:
        registry.put_secret(
            session,
            secret_ref="hr-db-credentials",
            secret_value="managed://secret",
        )
        session.commit()

    monkeypatch.setattr(secrets_utils, "SessionLocal", session_local)
    monkeypatch.setattr(
        secrets_utils,
        "get_settings",
        lambda: SimpleNamespace(managed_secret_encryption_key="test-key"),
    )
    monkeypatch.setenv("SECRET_HR_DB_CREDENTIALS", "env://fallback")

    assert secrets_utils.resolve_secret("hr-db-credentials") == "managed://secret"
    engine.dispose()


def test_resolve_secret_falls_back_to_env(monkeypatch) -> None:
    engine, session_local = _session_factory()
    monkeypatch.setattr(secrets_utils, "SessionLocal", session_local)
    monkeypatch.setattr(
        secrets_utils,
        "get_settings",
        lambda: SimpleNamespace(managed_secret_encryption_key="test-key"),
    )
    monkeypatch.setenv("SECRET_API_TOKEN", "env-token")

    assert secrets_utils.resolve_secret("api-token") == "env-token"
    engine.dispose()


def test_resolve_secret_raises_when_secret_missing(monkeypatch) -> None:
    engine, session_local = _session_factory()
    monkeypatch.setattr(secrets_utils, "SessionLocal", session_local)
    monkeypatch.setattr(
        secrets_utils,
        "get_settings",
        lambda: SimpleNamespace(managed_secret_encryption_key="test-key"),
    )
    monkeypatch.delenv("SECRET_UNKNOWN", raising=False)

    with pytest.raises(secrets_utils.SecretResolutionError):
        secrets_utils.resolve_secret("unknown")

    engine.dispose()
