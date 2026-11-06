"""Secure, tenant-isolated artifact storage service (Phase 2G).

Provides safe filesystem storage and retrieval for generated report artifacts
(PDFs, Markdown, JSON) with strict path traversal protections.
"""

from pathlib import Path
import re
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import ResearchError
from app.core.logging import get_logger

logger = get_logger("app.services.artifact_storage")

# Strict ID validation to prevent directory traversal
_SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


class ArtifactStorageService:
    """Manages file artifacts with organization-scoped tenant isolation."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            settings = get_settings()
            # Use configurable storage or safe local directory
            configured = getattr(settings, "artifact_storage_path", None)
            if configured:
                self._base_dir = Path(configured).resolve()
            else:
                self._base_dir = (Path.cwd() / "data" / "artifacts").resolve()
        else:
            self._base_dir = Path(base_dir).resolve()

        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _get_tenant_dir(self, organization_id: str) -> Path:
        """Resolve and validate the tenant directory path."""
        if not _SAFE_ID_PATTERN.match(organization_id):
            raise ResearchError("Invalid organization identifier for storage.")
        tenant_dir = (self._base_dir / organization_id).resolve()
        if not tenant_dir.is_relative_to(self._base_dir):
            raise ResearchError("Path traversal violation detected.")
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir

    def _resolve_artifact_path(
        self, organization_id: str, artifact_name: str
    ) -> Path:
        """Resolve a specific artifact path safely within the tenant directory."""
        if not _SAFE_ID_PATTERN.match(artifact_name.split(".")[0]):
            raise ResearchError("Invalid artifact identifier.")
        tenant_dir = self._get_tenant_dir(organization_id)
        artifact_path = (tenant_dir / artifact_name).resolve()
        if not artifact_path.is_relative_to(tenant_dir):
            raise ResearchError("Artifact path traversal violation detected.")
        return artifact_path

    def save_bytes(
        self, organization_id: str, artifact_name: str, content: bytes
    ) -> str:
        """Save binary artifact (e.g. PDF) securely. Returns relative artifact key."""
        target_path = self._resolve_artifact_path(organization_id, artifact_name)
        target_path.write_bytes(content)
        logger.debug(
            "Saved binary artifact org=%s artifact=%s size=%d",
            organization_id,
            artifact_name,
            len(content),
        )
        return f"{organization_id}/{artifact_name}"

    def save_text(
        self, organization_id: str, artifact_name: str, text: str, encoding: str = "utf-8"
    ) -> str:
        """Save text artifact (e.g. Markdown). Returns relative artifact key."""
        target_path = self._resolve_artifact_path(organization_id, artifact_name)
        target_path.write_text(text, encoding=encoding)
        logger.debug(
            "Saved text artifact org=%s artifact=%s length=%d",
            organization_id,
            artifact_name,
            len(text),
        )
        return f"{organization_id}/{artifact_name}"

    def read_bytes(self, organization_id: str, artifact_name: str) -> Optional[bytes]:
        """Read binary artifact safely."""
        try:
            target_path = self._resolve_artifact_path(organization_id, artifact_name)
            if not target_path.exists() or not target_path.is_file():
                return None
            return target_path.read_bytes()
        except Exception as exc:
            logger.warning(
                "Failed to read artifact org=%s artifact=%s error=%s",
                organization_id,
                artifact_name,
                exc,
            )
            return None

    def read_text(
        self, organization_id: str, artifact_name: str, encoding: str = "utf-8"
    ) -> Optional[str]:
        """Read text artifact safely."""
        try:
            target_path = self._resolve_artifact_path(organization_id, artifact_name)
            if not target_path.exists() or not target_path.is_file():
                return None
            return target_path.write_text if False else target_path.read_text(encoding=encoding)
        except Exception as exc:
            logger.warning(
                "Failed to read text artifact org=%s artifact=%s error=%s",
                organization_id,
                artifact_name,
                exc,
            )
            return None

    def delete_artifact(self, organization_id: str, artifact_name: str) -> bool:
        """Delete an artifact safely."""
        try:
            target_path = self._resolve_artifact_path(organization_id, artifact_name)
            if target_path.exists():
                target_path.unlink()
                return True
            return False
        except Exception:
            return False


_default_artifact_storage: Optional[ArtifactStorageService] = None


def get_artifact_storage() -> ArtifactStorageService:
    global _default_artifact_storage
    if _default_artifact_storage is None:
        _default_artifact_storage = ArtifactStorageService()
    return _default_artifact_storage


__all__ = ["ArtifactStorageService", "get_artifact_storage"]
