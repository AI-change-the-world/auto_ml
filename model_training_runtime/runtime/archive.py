"""Safe extraction utilities for versioned training-code ZIP packages."""
from __future__ import annotations

import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable

from .logging_utils import logger


TRAINING_ARCHIVE_MAX_FILES = 5_000
TRAINING_ARCHIVE_MAX_UNPACKED_BYTES = 512 * 1024 * 1024
FORBIDDEN_PACKAGE_FILES = {".env", "requirements.txt", "requirements.in"}


class TrainingArchiveError(RuntimeError):
    """The package archive cannot be safely used by the training runtime."""


def validate_archive_members(
    infos: Iterable[zipfile.ZipInfo],
    *,
    max_files: int = TRAINING_ARCHIVE_MAX_FILES,
    max_unpacked_bytes: int = TRAINING_ARCHIVE_MAX_UNPACKED_BYTES,
    reject_dependency_files: bool = True,
) -> tuple[set[str], int]:
    """Validate ZIP members without extracting or importing package code."""
    info_list = list(infos)
    if len(info_list) > max_files:
        raise TrainingArchiveError(f"training package contains more than {max_files} archive members")

    files: set[str] = set()
    total_size = 0
    for info in info_list:
        _validate_member_path(info)
        if info.is_dir():
            continue
        if info.filename in files:
            raise TrainingArchiveError(f"training package contains duplicate file `{info.filename}`")
        if reject_dependency_files and PurePosixPath(info.filename).name.lower() in FORBIDDEN_PACKAGE_FILES:
            raise TrainingArchiveError(
                f"training package must not include `{info.filename}`; select a platform-managed runtime instead"
            )
        files.add(info.filename)
        total_size += info.file_size
        if total_size > max_unpacked_bytes:
            raise TrainingArchiveError(
                f"training package exceeds the {max_unpacked_bytes} byte uncompressed limit"
            )
    return files, total_size


def extract_training_package(archive_path: Path, destination: Path) -> tuple[set[str], int]:
    """Safely extract an already-validated training package into a task workspace."""
    logger.info("Extracting training package: archive=%s destination=%s", archive_path, destination)
    try:
        with zipfile.ZipFile(archive_path) as archive:
            files, total_size = validate_archive_members(archive.infolist())
            destination.mkdir(parents=True, exist_ok=True)
            root = destination.resolve()
            for info in archive.infolist():
                target = (destination / PurePosixPath(info.filename)).resolve()
                try:
                    target.relative_to(root)
                except ValueError as exc:
                    raise TrainingArchiveError("training package path escapes task directory") from exc
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as exc:
        raise TrainingArchiveError("training package must be a valid ZIP archive") from exc
    logger.info(
        "Training package extracted: archive=%s files=%s unpacked_bytes=%s",
        archive_path,
        len(files),
        total_size,
    )
    return files, total_size


def _validate_member_path(info: zipfile.ZipInfo) -> None:
    if not info.filename or "\x00" in info.filename:
        raise TrainingArchiveError("training package contains an unsafe file path")
    path = PurePosixPath(info.filename)
    mode = info.external_attr >> 16
    if path.is_absolute() or (path.parts and path.parts[0].endswith(":")) or ".." in path.parts or stat.S_ISLNK(mode):
        raise TrainingArchiveError("training package contains an unsafe file path")
