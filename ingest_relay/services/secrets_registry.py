from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ingest_relay.models import ManagedSecret
from ingest_relay.studio_schemas import ManagedSecretMetadata


class SecretEncryptionError(RuntimeError):
    pass


def _keystream(secret_key: str, nonce: bytes, length: int) -> bytes:
    seed = hashlib.sha256(secret_key.encode("utf-8") + nonce).digest()
    chunks = bytearray()
    material = seed
    while len(chunks) < length:
        material = hashlib.sha256(material + seed).digest()
        chunks.extend(material)
    return bytes(chunks[:length])


def encrypt_secret(secret_key: str, plaintext: str) -> str:
    if not secret_key:
        raise SecretEncryptionError("MANAGED_SECRET_ENCRYPTION_KEY must be set")

    nonce = hashlib.sha256(f"{plaintext}:{secret_key}".encode()).digest()[:12]
    payload = plaintext.encode("utf-8")
    stream = _keystream(secret_key, nonce, len(payload))
    ciphertext = bytes(a ^ b for a, b in zip(payload, stream, strict=True))
    packed = nonce + ciphertext
    return base64.urlsafe_b64encode(packed).decode("ascii")


def decrypt_secret(secret_key: str, encrypted_value: str) -> str:
    if not secret_key:
        raise SecretEncryptionError("MANAGED_SECRET_ENCRYPTION_KEY must be set")

    packed = base64.urlsafe_b64decode(encrypted_value.encode("ascii"))
    nonce = packed[:12]
    ciphertext = packed[12:]
    stream = _keystream(secret_key, nonce, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, stream, strict=True))
    return plaintext.decode("utf-8")


class ManagedSecretsRegistry:
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key

    def put_secret(
        self,
        session: Session,
        *,
        secret_ref: str,
        secret_value: str,
    ) -> ManagedSecretMetadata:
        encrypted_value = encrypt_secret(self.encryption_key, secret_value)
        existing = session.get(ManagedSecret, secret_ref)
        now = datetime.now(tz=UTC)
        if existing:
            existing.encrypted_value = encrypted_value
            existing.updated_at = now
            record = existing
        else:
            record = ManagedSecret(
                secret_ref=secret_ref,
                encrypted_value=encrypted_value,
                created_at=now,
                updated_at=now,
            )
            session.add(record)

        return ManagedSecretMetadata(
            secret_ref=record.secret_ref,
            source="managed",
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def list_secrets(self, session: Session) -> list[ManagedSecretMetadata]:
        rows = list(
            session.execute(
                select(ManagedSecret).order_by(ManagedSecret.secret_ref),
            ).scalars(),
        )
        return [
            ManagedSecretMetadata(
                secret_ref=row.secret_ref,
                source="managed",
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]

    def get_secret_value(self, session: Session, *, secret_ref: str) -> str | None:
        row = session.get(ManagedSecret, secret_ref)
        if not row:
            return None
        return decrypt_secret(self.encryption_key, row.encrypted_value)
