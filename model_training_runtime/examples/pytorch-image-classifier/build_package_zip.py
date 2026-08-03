"""Build a deterministic ZIP for the runnable PyTorch classifier example."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PACKAGE_DIR = Path(__file__).resolve().parent
PACKAGE_FILES = ("training_package.json", "train.py")


def build(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (PACKAGE_DIR / name).read_bytes())
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="destination ZIP path")
    args = parser.parse_args()
    print(build(args.output))
