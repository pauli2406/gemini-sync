from __future__ import annotations

from ingest_relay.services.secrets_registry import ManagedSecretsRegistry


def test_managed_secret_create_and_list_and_resolve(db_session_factory) -> None:
    registry = ManagedSecretsRegistry(encryption_key="test-key")

    with db_session_factory() as session:
        registry.put_secret(session, secret_ref="hr-db-credentials", secret_value="postgres://user:pw")
        session.commit()

        listed = registry.list_secrets(session)
        assert listed[0].secret_ref == "hr-db-credentials"
        assert listed[0].source == "managed"

        value = registry.get_secret_value(session, secret_ref="hr-db-credentials")
        assert value == "postgres://user:pw"
