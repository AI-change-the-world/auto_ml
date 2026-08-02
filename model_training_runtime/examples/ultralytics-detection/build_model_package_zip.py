"""Package an approved Ultralytics .pt file for initialize/resume input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PROTOCOL_VERSION = "training-model-package/v1"


def build(
    weights_path: Path,
    output_path: Path,
    *,
    name: str,
    class_names: list[str],
    task_kind: str = "detection",
    resume_checkpoint: Path | None = None,
) -> Path:
    if not weights_path.is_file():
        raise FileNotFoundError(weights_path)
    if weights_path.suffix.lower() != ".pt":
        raise ValueError("Ultralytics model packages must use a .pt initialization artifact")
    class_names = [item.strip() for item in class_names]
    if not class_names or any(not item for item in class_names) or len(class_names) != len(set(class_names)):
        raise ValueError("class_names must be non-empty and unique")
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "name": name,
        "task_kind": task_kind,
        "class_names": class_names,
        "framework": {"id": "ultralytics", "version": "8.3.0"},
        "artifact_path": "weights/model.pt",
        "format": "pt",
        "metadata": {"source": "ultralytics-pytorch-cu124-runtime"},
    }
    if resume_checkpoint is not None:
        if not resume_checkpoint.is_file() or resume_checkpoint.suffix.lower() != ".pt":
            raise ValueError("resume checkpoint must be an existing .pt file")
        manifest["resume_checkpoint_path"] = "checkpoints/last.pt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        _write(archive, "training_model_package.json", json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode())
        _write(archive, "weights/model.pt", weights_path.read_bytes())
        if resume_checkpoint is not None:
            _write(archive, "checkpoints/last.pt", resume_checkpoint.read_bytes())
    return output_path


def _write(archive: ZipFile, name: str, content: bytes) -> None:
    info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("weights", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--name", default="Ultralytics Detection Base")
    parser.add_argument("--classes", required=True, help="comma-separated class names")
    parser.add_argument("--resume-checkpoint", type=Path)
    args = parser.parse_args()
    build(
        args.weights,
        args.output,
        name=args.name,
        class_names=[value.strip() for value in args.classes.split(",") if value.strip()],
        resume_checkpoint=args.resume_checkpoint,
    )
    print(args.output)
