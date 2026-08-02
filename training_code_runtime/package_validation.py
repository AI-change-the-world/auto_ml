"""Non-executing validation for uploaded training code archives."""
from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass

from pydantic import ValidationError

from contracts import TrainingPackageManifest
from runtime.archive import TrainingArchiveError, validate_archive_members


MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_FILES = 5_000
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MANIFEST_FILE = "training_package.json"


class PackageArchiveValidationError(ValueError):
    """The archive is malformed or does not meet the package contract."""


@dataclass(frozen=True)
class ArchiveValidationReport:
    sha256: str
    file_count: int
    uncompressed_bytes: int
    manifest: TrainingPackageManifest

    def as_dict(self) -> dict:
        return {
            "sha256": self.sha256,
            "file_count": self.file_count,
            "uncompressed_bytes": self.uncompressed_bytes,
            "manifest": self.manifest.model_dump(mode="json"),
        }


def validate_package_archive(archive: bytes) -> ArchiveValidationReport:
    """Validate ZIP structure and manifest without importing or running package code."""
    if not archive:
        raise PackageArchiveValidationError("package archive is empty")
    if len(archive) > MAX_ARCHIVE_BYTES:
        raise PackageArchiveValidationError(
            f"package archive exceeds the {MAX_ARCHIVE_BYTES} byte limit"
        )

    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            try:
                file_names, total_size = validate_archive_members(
                    bundle.infolist(),
                    max_files=MAX_ARCHIVE_FILES,
                    max_unpacked_bytes=MAX_UNCOMPRESSED_BYTES,
                )
            except TrainingArchiveError as exc:
                raise PackageArchiveValidationError(str(exc)) from exc

            if MANIFEST_FILE not in file_names:
                raise PackageArchiveValidationError(
                    f"package archive must contain root `{MANIFEST_FILE}`"
                )

            try:
                manifest = TrainingPackageManifest.model_validate_json(
                    bundle.read(MANIFEST_FILE)
                )
            except (ValidationError, UnicodeDecodeError) as exc:
                raise PackageArchiveValidationError(
                    f"invalid `{MANIFEST_FILE}`: {exc}"
                ) from exc

            if manifest.entrypoint not in file_names:
                raise PackageArchiveValidationError(
                    f"manifest entrypoint `{manifest.entrypoint}` is not a regular file in the archive"
                )

            return ArchiveValidationReport(
                sha256=hashlib.sha256(archive).hexdigest(),
                file_count=len(file_names),
                uncompressed_bytes=total_size,
                manifest=manifest,
            )
    except zipfile.BadZipFile as exc:
        raise PackageArchiveValidationError("package archive must be a valid ZIP file") from exc
