from __future__ import annotations

import os

from gemini_sync_bridge.db import SessionLocal
from gemini_sync_bridge.services.secrets_registry import ManagedSecretsRegistry
from gemini_sync_bridge.settings import get_settings


class SecretResolutionError(RuntimeError):
    pass


def secret_env_var_name(secret_ref: str) -> str:
    normalized = secret_ref.replace("-", "_").replace(".", "_").upper()
    return f"SECRET_{normalized}"


def resolve_secret(secret_ref: str) -> str:
    settings = get_settings()
    registry = ManagedSecretsRegistry(settings.managed_secret_encryption_key)
    with SessionLocal() as session:
        managed = registry.get_secret_value(session, secret_ref=secret_ref)
    if managed:
        return managed

    env_key = secret_env_var_name(secret_ref)
    value = os.getenv(env_key)
    if not value:
        raise SecretResolutionError(
            f"Missing secret for '{secret_ref}'. Expected environment variable {env_key}."
        )
    return value
