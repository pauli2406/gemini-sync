from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx

from gemini_sync_bridge.adapters import extractors
from gemini_sync_bridge.schemas import SourceConfig
from gemini_sync_bridge.services import gemini_ingestion, github_pr, observability
from gemini_sync_bridge.utils.http_clients import create_httpx_client


class _NoopContextClient:
    def __init__(self, *, trust_env: bool = True) -> None:
        self.trust_env = trust_env
        self.posts: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> _NoopContextClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def post(self, url: str, **kwargs):
        self.posts.append((url, kwargs))
        request = httpx.Request("POST", url)
        return httpx.Response(status_code=200, request=request, json={})

    def get(self, url: str, **kwargs):
        request = httpx.Request("GET", url)
        payload = {"object": {"sha": "base-sha"}}
        return httpx.Response(status_code=200, request=request, json=payload)


def _oauth_source() -> SourceConfig:
    return SourceConfig(
        type="http",
        secretRef="fallback-secret",
        url="https://api.local/v1/articles",
        method="GET",
        oauth={
            "grantType": "client_credentials",
            "tokenUrl": "https://auth.local/oauth2/token",
            "clientId": "bridge-client",
            "clientSecretRef": "oauth-client-secret",
        },
    )


def test_create_httpx_client_sets_trust_env_and_preserves_kwargs() -> None:
    with create_httpx_client(timeout=12.5, base_url="https://example.local") as client:
        assert client.trust_env is True
        assert str(client.base_url).startswith("https://example.local")


def test_extract_rest_rows_static_bearer_uses_shared_httpx_client_factory(monkeypatch) -> None:
    factory_calls: list[dict[str, Any]] = []
    factory_client = _NoopContextClient(trust_env=True)

    def fake_factory(**kwargs):
        factory_calls.append(kwargs)
        return factory_client

    def fake_request(client, method, url, **kwargs):
        request = httpx.Request(method, url)
        return httpx.Response(status_code=200, request=request, json={"items": []})

    monkeypatch.setattr(extractors, "create_httpx_client", fake_factory, raising=False)
    monkeypatch.setattr(extractors.httpx, "Client", lambda *args, **kwargs: _NoopContextClient())
    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "static-token")

    source = SourceConfig(
        type="http",
        secretRef="kb-api-token",
        url="https://api.local/v1/articles",
        method="GET",
    )
    extractors.extract_rest_rows(source, None)

    assert factory_calls == [{"timeout": 30.0}]


def test_extract_rest_rows_oauth_uses_shared_client_for_token_and_api_calls(monkeypatch) -> None:
    factory_calls: list[dict[str, Any]] = []
    request_clients: list[_NoopContextClient] = []
    factory_client = _NoopContextClient(trust_env=True)

    def fake_factory(**kwargs):
        factory_calls.append(kwargs)
        return factory_client

    def fake_request(client, method, url, **kwargs):
        request_clients.append(client)
        request = httpx.Request(method, url)
        if "oauth2/token" in url:
            return httpx.Response(
                status_code=200,
                request=request,
                json={"access_token": "oauth-token", "expires_in": 3600},
            )
        return httpx.Response(status_code=200, request=request, json={"items": []})

    monkeypatch.setattr(extractors, "create_httpx_client", fake_factory, raising=False)
    monkeypatch.setattr(extractors.httpx, "Client", lambda *args, **kwargs: _NoopContextClient())
    monkeypatch.setattr(extractors, "_request_with_retry", fake_request)
    monkeypatch.setattr(extractors, "resolve_secret", lambda _: "oauth-secret")

    extractors.extract_rest_rows(_oauth_source(), None)

    assert factory_calls == [{"timeout": 30.0}]
    assert request_clients
    assert all(client is factory_client for client in request_clients)


def test_send_splunk_event_uses_shared_httpx_client_factory(monkeypatch) -> None:
    factory_calls: list[dict[str, Any]] = []
    factory_client = _NoopContextClient(trust_env=True)

    def fake_factory(**kwargs):
        factory_calls.append(kwargs)
        return factory_client

    monkeypatch.setattr(observability, "create_httpx_client", fake_factory, raising=False)

    settings = SimpleNamespace(
        splunk_hec_url="https://splunk.example/services/collector",
        splunk_hec_token="token-123",
    )
    observability.send_splunk_event(settings, {"status": "SUCCESS"})

    assert factory_calls == [{"timeout": 10}]


def test_send_teams_alert_uses_shared_httpx_client_factory(monkeypatch) -> None:
    factory_calls: list[dict[str, Any]] = []
    factory_client = _NoopContextClient(trust_env=True)

    def fake_factory(**kwargs):
        factory_calls.append(kwargs)
        return factory_client

    monkeypatch.setattr(observability, "create_httpx_client", fake_factory, raising=False)

    settings = SimpleNamespace(teams_webhook_url="https://teams.example/webhook")
    observability.send_teams_alert(
        settings,
        title="Failed run",
        message="Connector failed",
        facts={"connector": "kb-rest"},
    )

    assert factory_calls == [{"timeout": 10}]


def test_github_pr_service_uses_shared_httpx_client_factory(monkeypatch) -> None:
    factory_calls: list[dict[str, Any]] = []
    factory_client = _NoopContextClient(trust_env=True)

    def fake_factory(**kwargs):
        factory_calls.append(kwargs)
        return factory_client

    monkeypatch.setattr(github_pr, "create_httpx_client", fake_factory, raising=False)
    monkeypatch.setattr(github_pr.httpx, "Client", lambda *args, **kwargs: _NoopContextClient())

    service = github_pr.GitHubPRService(
        github_repo="acme/gemini-sync",
        github_token="github-token-test",
        github_base_branch="main",
    )

    monkeypatch.setattr(
        service,
        "_commit_file_changes",
        lambda *args, **kwargs: ["connectors/kb-rest.yaml"],
    )
    monkeypatch.setattr(
        service,
        "_create_pull_request",
        lambda *args, **kwargs: "https://github.com/acme/gemini-sync/pull/1",
    )

    result = service.create_proposal(
        action="edit",
        connector_id="kb-rest",
        changed_files=["connectors/kb-rest.yaml"],
        branch_name="studio/edit/kb-rest/20260217-100000",
        proposal_id="p-1000",
        file_changes={"connectors/kb-rest.yaml": "apiVersion: sync.gemini.io/v1alpha1\n"},
    )

    assert factory_calls == [{"base_url": "https://api.github.com", "timeout": 30.0}]
    assert result.pr_url.endswith("/pull/1")


def test_gemini_ingestion_authorized_session_explicitly_enables_trust_env(monkeypatch) -> None:
    fake_credentials = object()

    class FakeAuthorizedSession:
        def __init__(self, credentials):
            self.credentials = credentials
            self.trust_env = False

    monkeypatch.setattr(
        gemini_ingestion.google.auth,
        "default",
        lambda scopes: (fake_credentials, "test-project"),
    )
    monkeypatch.setattr(gemini_ingestion, "AuthorizedSession", FakeAuthorizedSession)

    client = gemini_ingestion.GeminiIngestionClient(
        SimpleNamespace(gemini_ingestion_dry_run=False)
    )
    session = client._ensure_session()

    assert session.credentials is fake_credentials
    assert session.trust_env is True
