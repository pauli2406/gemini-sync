from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from google.cloud import storage


@dataclass
class ObjectLocation:
    uri: str


class ObjectStoreError(RuntimeError):
    pass


class ObjectStore:
    def upload_text(
        self,
        uri: str,
        data: str,
        content_type: str = "application/json",
    ) -> ObjectLocation:
        raise NotImplementedError


class GCSObjectStore(ObjectStore):
    def __init__(self) -> None:
        self.client = storage.Client()

    def upload_text(
        self,
        uri: str,
        data: str,
        content_type: str = "application/json",
    ) -> ObjectLocation:
        if not uri.startswith("gs://"):
            raise ObjectStoreError(f"GCS URI must start with gs://, got {uri}")

        without_scheme = uri.removeprefix("gs://")
        bucket_name, _, object_name = without_scheme.partition("/")
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(data=data, content_type=content_type)
        return ObjectLocation(uri=uri)


class LocalObjectStore(ObjectStore):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)

    def upload_text(
        self,
        uri: str,
        data: str,
        content_type: str = "application/json",
    ) -> ObjectLocation:
        # URI format for local mode: file://relative/path/to/object
        if not uri.startswith("file://"):
            raise ObjectStoreError(f"Local URI must start with file://, got {uri}")

        relative = uri.removeprefix("file://")
        file_path = self.base_dir / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(data, encoding="utf-8")
        return ObjectLocation(uri=uri)
