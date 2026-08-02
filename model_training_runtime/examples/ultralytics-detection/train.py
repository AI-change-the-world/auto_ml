"""Ultralytics detection package for model_training_runtime.

The platform runtime image supplies Ultralytics and PyTorch. This package only
adapts the materialized framework-neutral dataset manifest to the Ultralytics
directory layout and returns immutable model/checkpoint artifacts.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any, Callable


ULTRALYTICS_VERSION = "8.3.0"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def train(context: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    from ultralytics import YOLO

    if context["task"]["task_kind"] != "detection":
        raise ValueError("ultralytics-detection only supports task_kind=detection")

    input_dir = Path(context["workspace"]["input_dir"]).resolve()
    output_dir = Path(context["workspace"]["output_dir"]).resolve()
    class_names = [str(name) for name in context["dataset"]["class_names"]]
    parameters = context.get("parameters") or {}
    model_input_path = context.get("model_input_path")
    if not isinstance(model_input_path, str) or not model_input_path.strip():
        raise ValueError("ultralytics-detection requires a materialized .pt model input")

    report(event_type="phase", phase="prepare", message="building Ultralytics dataset layout")
    data_yaml, sample_count = _prepare_dataset(
        context["dataset"],
        input_dir=input_dir,
        output_dir=output_dir,
        val_fraction=float(parameters.get("val_fraction", 0.2)),
    )
    report(
        event_type="log",
        level="info",
        message=f"prepared {sample_count} detection samples for Ultralytics",
    )

    model_path = Path(model_input_path).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"materialized model input does not exist: {model_path}")
    model = YOLO(str(model_path))
    input_mode = (context.get("model_input") or {}).get("mode", "initialize")
    device = _ultralytics_device(context["resources"])
    train_kwargs: dict[str, Any] = {
        "data": str(data_yaml),
        "epochs": int(parameters.get("epochs", 10)),
        "imgsz": int(parameters.get("imgsz", 640)),
        "batch": int(parameters.get("batch", 8)),
        "workers": int(parameters.get("workers", 0)),
        "device": device,
        "project": str(output_dir / "_ultralytics_runs"),
        "name": "detection",
        "exist_ok": True,
        "seed": int(parameters.get("seed", 0)),
        "verbose": False,
    }
    for key in ("optimizer", "patience", "lr0", "weight_decay"):
        if key in parameters:
            train_kwargs[key] = parameters[key]
    if input_mode == "resume":
        train_kwargs["resume"] = True

    def on_epoch_end(trainer: Any) -> None:
        epoch = max(int(getattr(trainer, "epoch", 0)), 0)
        metrics = _numeric_metrics(getattr(trainer, "metrics", {}))
        report(
            event_type="metric",
            split="train",
            epoch=epoch,
            metrics=metrics or {"epoch": float(epoch)},
        )

    model.add_callback("on_train_epoch_end", on_epoch_end)
    report(event_type="phase", phase="train", message=f"starting Ultralytics {input_mode} training")
    model.train(**train_kwargs)

    save_dir = Path(model.trainer.save_dir).resolve()
    best_source = save_dir / "weights" / "best.pt"
    last_source = save_dir / "weights" / "last.pt"
    if not best_source.is_file() or not last_source.is_file():
        raise FileNotFoundError("Ultralytics did not produce both weights/best.pt and weights/last.pt")
    shutil.copy2(best_source, output_dir / "best.pt")
    shutil.copy2(last_source, output_dir / "last.pt")

    artifacts: list[dict[str, Any]] = [
        {"path": "best.pt", "role": "model", "format": "pt", "deployable": True},
        {"path": "last.pt", "role": "checkpoint", "format": "pt", "deployable": False},
    ]
    if bool(parameters.get("export_onnx", False)):
        report(event_type="phase", phase="export", message="exporting best.pt to ONNX")
        exported = YOLO(str(best_source)).export(
            format="onnx",
            imgsz=int(parameters.get("imgsz", 640)),
            dynamic=bool(parameters.get("onnx_dynamic", False)),
            simplify=bool(parameters.get("onnx_simplify", False)),
        )
        exported_path = Path(str(exported)) if exported else best_source.with_suffix(".onnx")
        if not exported_path.is_file():
            raise FileNotFoundError(f"Ultralytics did not produce ONNX output: {exported_path}")
        shutil.copy2(exported_path, output_dir / "best.onnx")
        artifacts.append({"path": "best.onnx", "role": "model", "format": "onnx", "deployable": False})

    report(event_type="phase", phase="export", message="writing model and resumable checkpoint artifacts")
    return {
        "summary": f"Ultralytics detection completed with {sample_count} samples",
        "metrics": _numeric_metrics(getattr(model.trainer, "metrics", {})),
        "artifacts": artifacts,
        "model": {
            "task_kind": "detection",
            "class_names": class_names,
            "framework": {"id": "ultralytics", "version": ULTRALYTICS_VERSION},
            "resume_checkpoint_path": "last.pt",
        },
    }


def _prepare_dataset(
    dataset: dict[str, Any],
    *,
    input_dir: Path,
    output_dir: Path,
    val_fraction: float,
) -> tuple[Path, int]:
    if not 0 <= val_fraction <= 0.5:
        raise ValueError("val_fraction must be between 0 and 0.5")
    work_dir = output_dir / "_ultralytics_dataset"
    train_images = work_dir / "images" / "train"
    val_images = work_dir / "images" / "val"
    train_labels = work_dir / "labels" / "train"
    val_labels = work_dir / "labels" / "val"
    for directory in (train_images, val_images, train_labels, val_labels):
        directory.mkdir(parents=True, exist_ok=True)

    train_count = 0
    val_count = 0
    copied: list[tuple[Path, Path, Path, str]] = []
    for index, item in enumerate(dataset.get("items", [])):
        media_source = _input_file(input_dir, item.get("media_path"), "media")
        annotation_source = _input_file(input_dir, item.get("annotation_path"), "annotation")
        if media_source.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError(f"unsupported detection image format: {media_source.name}")
        stem = f"{index:08d}_{media_source.stem}"
        split = _split_for_item(item, val_fraction)
        if split == "test":
            continue
        if split == "val":
            image_target, label_target = val_images / f"{stem}{media_source.suffix.lower()}", val_labels / f"{stem}.txt"
            val_count += 1
        else:
            image_target, label_target = train_images / f"{stem}{media_source.suffix.lower()}", train_labels / f"{stem}.txt"
            train_count += 1
        copied.append((media_source, annotation_source, image_target, label_target.name))

    if not copied:
        raise ValueError("dataset contains no detection samples")
    if train_count == 0 or val_count == 0:
        # Match the legacy trainer's small-dataset behavior: use all available
        # samples in both folds so one-sample smoke tests remain executable.
        train_count = val_count = 0
        for media_source, annotation_source, _, label_name in copied:
            stem = Path(label_name).stem
            train_target = train_images / f"{stem}{media_source.suffix.lower()}"
            val_target = val_images / f"{stem}{media_source.suffix.lower()}"
            shutil.copy2(media_source, train_target)
            shutil.copy2(media_source, val_target)
            (train_labels / label_name).write_text(annotation_source.read_text(encoding="utf-8"), encoding="utf-8")
            (val_labels / label_name).write_text(annotation_source.read_text(encoding="utf-8"), encoding="utf-8")
            train_count += 1
            val_count += 1
    else:
        for media_source, annotation_source, image_target, label_name in copied:
            shutil.copy2(media_source, image_target)
            label_dir = train_labels if image_target.parent == train_images else val_labels
            label_dir.joinpath(label_name).write_text(annotation_source.read_text(encoding="utf-8"), encoding="utf-8")

    names = "\n".join(f"  {index}: {json.dumps(str(name), ensure_ascii=False)}" for index, name in enumerate(dataset["class_names"]))
    data_yaml = work_dir / "data.yaml"
    data_yaml.write_text(
        f"path: {json.dumps(str(work_dir).replace(chr(92), '/'))}\ntrain: images/train\nval: images/val\nnames:\n{names}\n",
        encoding="utf-8",
    )
    return data_yaml, len(copied)


def _input_file(input_dir: Path, relative_path: Any, label: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError(f"detection item requires {label} path")
    input_root = input_dir.resolve()
    path = (input_root / relative_path).resolve()
    try:
        path.relative_to(input_root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes input directory") from exc
    if not path.is_file():
        raise FileNotFoundError(f"{label} file does not exist: {relative_path}")
    return path


def _split_for_item(item: dict[str, Any], val_fraction: float) -> str:
    split = str(item.get("split") or "unspecified").lower()
    if split in {"train", "val", "test"}:
        return split
    digest = hashlib.sha256(str(item.get("item_id", "")).encode("utf-8")).digest()
    return "val" if int.from_bytes(digest[:4], "big") / 2**32 < val_fraction else "train"


def _ultralytics_device(resources: dict[str, Any]) -> Any:
    device = resources.get("device", "cpu")
    if device == "cuda":
        count = max(int(resources.get("gpu_count", 1)), 1)
        return 0 if count == 1 else list(range(count))
    return device


def _numeric_metrics(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    metrics: dict[str, float] = {}
    for key, raw in value.items():
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            metrics[str(key)] = number
    return metrics
