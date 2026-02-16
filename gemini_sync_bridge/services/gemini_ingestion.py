from __future__ import annotations

import time
from urllib.parse import quote

import google.auth
from google.auth.transport.requests import AuthorizedSession
from tenacity import retry, stop_after_attempt, wait_exponential

from gemini_sync_bridge.schemas import CanonicalDocument, GeminiConfig, RunManifest
from gemini_sync_bridge.settings import Settings
from gemini_sync_bridge.utils.doc_ids import to_discovery_doc_id


class GeminiIngestionError(RuntimeError):
    pass


class GeminiIngestionClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: AuthorizedSession | None = None

    def _ensure_session(self) -> AuthorizedSession:
        if self._session:
            return self._session
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self._session = AuthorizedSession(credentials)
        return self._session

    @staticmethod
    def _api_host(location: str) -> str:
        if location == "global":
            return "discoveryengine.googleapis.com"
        return f"{location}-discoveryengine.googleapis.com"

    def _documents_base(self, gemini: GeminiConfig) -> str:
        host = self._api_host(gemini.location)
        return (
            f"https://{host}/v1/projects/{gemini.project_id}"
            f"/locations/{gemini.location}/collections/default_collection"
            f"/dataStores/{gemini.data_store_id}/branches/default_branch/documents"
        )

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3), reraise=True)
    def _request(self, method: str, url: str, **kwargs):
        session = self._ensure_session()
        response = session.request(method, url, timeout=60, **kwargs)
        if response.status_code >= 400:
            raise GeminiIngestionError(
                f"Gemini API request failed ({response.status_code}): {response.text}"
            )
        return response

    def import_documents(self, gemini: GeminiConfig, manifest: RunManifest) -> None:
        if self.settings.gemini_ingestion_dry_run:
            return
        import_uri = manifest.import_upserts_path or manifest.upserts_path
        if import_uri.startswith("file://"):
            return

        endpoint = f"{self._documents_base(gemini)}:import"
        if manifest.import_upserts_path:
            payload = {
                "gcsSource": {"inputUris": [import_uri], "dataSchema": "document"},
                "reconciliationMode": "INCREMENTAL",
            }
        else:
            payload = {
                "gcsSource": {"inputUris": [import_uri], "dataSchema": "custom"},
                "idField": "_id",
                "reconciliationMode": "INCREMENTAL",
            }
        operation = self._request("POST", endpoint, json=payload).json()

        operation_name = operation.get("name")
        if operation_name:
            self._wait_for_operation(operation_name, gemini.location)

    def delete_documents(self, gemini: GeminiConfig, deletes: list[CanonicalDocument]) -> None:
        if self.settings.gemini_ingestion_dry_run:
            return

        base = self._documents_base(gemini)
        for doc in deletes:
            doc_id = quote(to_discovery_doc_id(doc.doc_id), safe="")
            url = f"{base}/{doc_id}"
            # Discovery Engine can return 404 if already deleted; treat as successful.
            try:
                self._request("DELETE", url)
            except GeminiIngestionError as exc:
                if "404" not in str(exc):
                    raise
            time.sleep(0.05)

    def _wait_for_operation(
        self,
        operation_name: str,
        location: str = "global",
        timeout_seconds: int = 600,
    ) -> None:
        if self.settings.gemini_ingestion_dry_run:
            return

        session = self._ensure_session()
        deadline = time.time() + timeout_seconds
        host = self._api_host(location)
        url = f"https://{host}/v1/{operation_name}"

        while time.time() < deadline:
            response = session.get(url, timeout=30)
            if response.status_code >= 400:
                raise GeminiIngestionError(
                    "Failed to poll operation "
                    f"{operation_name}: {response.status_code} {response.text}"
                )
            payload = response.json()
            if payload.get("done"):
                if "error" in payload:
                    raise GeminiIngestionError(
                        f"Operation {operation_name} failed: {payload['error']}"
                    )
                return
            time.sleep(5)

        raise GeminiIngestionError(f"Operation {operation_name} timed out after {timeout_seconds}s")
