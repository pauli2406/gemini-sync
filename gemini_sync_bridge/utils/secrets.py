from __future__ import annotations

import os


class SecretResolutionError(RuntimeError):
    pass


def secret_env_var_name(secret_ref: str) -> str:
    normalized = secret_ref.replace("-", "_").replace(".", "_").upper()
    return f"SECRET_{normalized}"


def resolve_secret(secret_ref: str) -> str:
    env_key = secret_env_var_name(secret_ref)
    value = os.getenv(env_key)
    if not value:
        raise SecretResolutionError(
            f"Missing secret for '{secret_ref}'. Expected environment variable {env_key}."
        )
    return value
