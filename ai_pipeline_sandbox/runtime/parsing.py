"""Package parsing helpers retained under the legacy runtime boundary."""
from __future__ import annotations

from pathlib import Path

from .archive import load_bundle_dotenv


def load_package_environment(package_root: Path) -> dict[str, str]:
    """Load the optional package-local .env file without changing host variables."""
    return load_bundle_dotenv(package_root)
