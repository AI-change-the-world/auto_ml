"""Safe ZIP extraction and package-local environment loading."""
from __future__ import annotations

import shutil
import stat
import zipfile
from pathlib import Path


SCRIPT_ARCHIVE_MAX_FILES = 512
SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES = 512 * 1024 * 1024
DOTENV_MAX_BYTES = 256 * 1024


def extract_script_package(archive_path: Path, destination: Path) -> None:
    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as exc:
        raise RuntimeError("downloaded script package is not a ZIP archive") from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > SCRIPT_ARCHIVE_MAX_FILES:
            raise RuntimeError("script package contains too many files")
        total_size = 0
        destination.mkdir(parents=True, exist_ok=True)
        destination_root = destination.resolve()
        for info in infos:
            if "\x00" in info.filename:
                raise RuntimeError("script package contains an unsafe file path")
            member_path = Path(info.filename)
            mode = info.external_attr >> 16
            if member_path.is_absolute() or ".." in member_path.parts or stat.S_ISLNK(mode):
                raise RuntimeError("script package contains an unsafe file path")
            target = (destination / member_path).resolve()
            try:
                target.relative_to(destination_root)
            except ValueError as exc:
                raise RuntimeError("script package path escapes task directory") from exc
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            total_size += info.file_size
            if total_size > SCRIPT_ARCHIVE_MAX_UNPACKED_BYTES:
                raise RuntimeError("script package exceeds extraction limit")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def load_bundle_dotenv(bundle_root: Path) -> dict[str, str]:
    dotenv_path = bundle_root / ".env"
    if not dotenv_path.is_file():
        return {}
    if dotenv_path.stat().st_size > DOTENV_MAX_BYTES:
        raise RuntimeError("script package .env exceeds the 256 KB limit")
    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError("script package .env must be UTF-8") from exc

    values: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or "\x00" in key or "\x00" in value:
            raise RuntimeError("script package .env contains an invalid variable")
        values[key] = _parse_dotenv_value(value)
    return values


def _parse_dotenv_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    comment_start = value.find(" #")
    if comment_start >= 0:
        value = value[:comment_start].rstrip()
    return value
