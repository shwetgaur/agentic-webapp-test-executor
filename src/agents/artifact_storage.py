"""Persistent artifact storage — local disk or Google Cloud Storage."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from src.common.settings import settings

logger = logging.getLogger(__name__)


class ArtifactBackend(Protocol):
    def read_text(self, key: str) -> str | None: ...

    def write_text(self, key: str, content: str) -> None: ...

    def exists(self, key: str) -> bool: ...


class LocalArtifactBackend:
    """Store under data/ with keys like locators/foo.json."""

    def __init__(self, base_dir: str | Path = "data") -> None:
        self.base_dir = Path(base_dir)

    def _path(self, key: str) -> Path:
        safe = key.replace("\\", "/").lstrip("/")
        if ".." in safe.split("/"):
            raise ValueError("Invalid artifact key")
        path = self.base_dir / safe
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def read_text(self, key: str) -> str | None:
        path = self._path(key)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def write_text(self, key: str, content: str) -> None:
        path = self._path(key)
        path.write_text(content, encoding="utf-8")

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()


class GcsArtifactBackend:
    """Persist artifacts in a GCS bucket (survives Cloud Run redeploy)."""

    def __init__(self, bucket_name: str, prefix: str = "") -> None:
        from google.cloud import storage

        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def _blob_name(self, key: str) -> str:
        safe = key.replace("\\", "/").lstrip("/")
        if ".." in safe.split("/"):
            raise ValueError("Invalid artifact key")
        if self.prefix:
            return f"{self.prefix}/{safe}"
        return safe

    def read_text(self, key: str) -> str | None:
        blob = self._bucket.blob(self._blob_name(key))
        if not blob.exists():
            return None
        return blob.download_as_text(encoding="utf-8")

    def write_text(self, key: str, content: str) -> None:
        blob = self._bucket.blob(self._blob_name(key))
        blob.upload_from_string(content, content_type="application/json; charset=utf-8")

    def exists(self, key: str) -> bool:
        return self._bucket.blob(self._blob_name(key)).exists()


def get_artifact_backend() -> ArtifactBackend:
    mode = (settings.artifact_storage or "local").strip().lower()
    if mode == "gcs":
        if not settings.gcs_bucket:
            raise ValueError("ARTIFACT_STORAGE=gcs requires GCS_BUCKET")
        logger.info("Artifact storage: GCS bucket=%s prefix=%s", settings.gcs_bucket, settings.gcs_prefix)
        return GcsArtifactBackend(settings.gcs_bucket, settings.gcs_prefix or "")
    return LocalArtifactBackend("data")


_backend: ArtifactBackend | None = None


def artifact_backend() -> ArtifactBackend:
    global _backend
    if _backend is None:
        _backend = get_artifact_backend()
    return _backend


def reset_artifact_backend_for_tests() -> None:
    global _backend
    _backend = None
