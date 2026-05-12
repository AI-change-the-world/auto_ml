"""
训练核心逻辑
使用 RabbitMQ 发送状态更新和日志，不直接写数据库
"""
import json
import os
import shutil
import threading
import uuid
import zipfile
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from core.dataset import (
    build_training_cache_key,
    cleanup_temp_dir,
    clone_cached_dataset,
    finalize_training_cache,
    load_materialized_training_dataset,
    materialize_training_manifest,
    prepare_training_cache_dir,
    prepare_classification_dataset,
    prepare_detection_dataset,
    prepare_segmentation_dataset,
)
from utils.config import download_from_s3, get_s3_config, upload_to_s3
from utils.logger import logger
from utils.mq import (
    TaskStatus,
    publish_model_registered,
    publish_task_log,
    publish_task_status,
)

SERVICE_NAME = "model-trainer"
DEFAULT_BASE_MODEL_DIR = "./base_model"
DEFAULT_TRAIN_CACHE_ROOT = "./runs/cache/datasets"
DEFAULT_MODEL_CACHE_DIR = "./runs/cache/models"


class TaskCancelledError(RuntimeError):
    """Raised when a training task is cancelled by the control plane."""


def _resolve_base_model(model_name: str) -> tuple[str, str]:
    """Resolve base model name to a local cached file when available."""
    base_model_dir = os.getenv("BASE_MODEL_DIR", DEFAULT_BASE_MODEL_DIR)
    model_path = Path(model_name)

    if model_path.is_absolute() or model_path.parent != Path("."):
        if model_path.exists():
            return str(model_path), "path"
        return model_name, "remote"

    cached_path = Path(base_model_dir) / model_name
    if cached_path.exists():
        return str(cached_path), "base_model"

    return model_name, "remote"


def _load_yolo_model(model_name: str) -> YOLO:
    """Load a YOLO model and recover once from an interrupted local weight download."""
    model_ref, model_source = _resolve_base_model(model_name)
    logger.info(f"Resolved base model: requested={model_name}, source={model_source}, ref={model_ref}")
    try:
        return YOLO(model_ref)
    except RuntimeError as exc:
        if not _looks_like_corrupt_torch_archive(exc):
            raise
        if model_source != "remote":
            raise RuntimeError(
                f"Local base model appears corrupt: {model_ref}. "
                "Please replace the file in base_model and retry."
            ) from exc
        if not _remove_local_weight_if_present(model_ref):
            raise
        logger.warning(f"Removed corrupt local model weight and retrying download: {model_ref}")
        return YOLO(model_ref)


def _looks_like_corrupt_torch_archive(exc: Exception) -> bool:
    message = str(exc)
    return (
        "PytorchStreamReader failed reading zip archive" in message
        or "failed finding central directory" in message
        or "failed finding central directory" in repr(exc)
    )


def _remove_local_weight_if_present(model_name: str) -> bool:
    if not model_name.endswith(".pt") or os.path.isabs(model_name):
        return False
    candidates = [
        os.path.abspath(model_name),
        os.path.abspath(os.path.join(os.getcwd(), model_name)),
    ]
    removed = False
    for path in dict.fromkeys(candidates):
        if os.path.exists(path):
            os.remove(path)
            removed = True
    return removed


def _should_export_onnx(task_config: Dict[str, Any]) -> bool:
    value = task_config.get("export_onnx", False)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _detection_task_kind(label_format: str) -> str:
    return "detection_obb" if label_format == "obb" else "detection_bbox"


def _trained_model_name(model_name: str, task_kind: str, task_id: int) -> str:
    return f"{Path(model_name).stem}-{task_kind}-task-{task_id}"


def _segmentation_task_kind() -> str:
    return "segmentation"


def _resolve_dataset_cache_mode(task_config: Dict[str, Any]) -> str:
    value = str(task_config.get("dataset_cache_mode", "off") or "off").strip().lower()
    if value in {"reuse", "refresh"}:
        return value
    return "off"


def _ensure_dir(path: str) -> str:
    resolved = os.path.abspath(path)
    os.makedirs(resolved, exist_ok=True)
    return resolved


def _resolve_resume_model(task_config: Dict[str, Any]) -> Optional[dict[str, Any]]:
    resume_model = task_config.get("resume_model")
    return resume_model if isinstance(resume_model, dict) else None


def _resolve_model_name(task_config: Dict[str, Any], default_name: str) -> str:
    resume_model = _resolve_resume_model(task_config)
    if resume_model and resume_model.get("save_path"):
        return str(resume_model["save_path"])
    return str(task_config.get("name", default_name) or default_name)


def _resolve_resume_display_name(task_config: Dict[str, Any], model_name: str) -> str:
    resume_model = _resolve_resume_model(task_config)
    if resume_model and resume_model.get("model_name"):
        return str(resume_model["model_name"])
    return model_name


def _download_resume_model_to_local(task_config: Dict[str, Any]) -> Optional[str]:
    resume_model = _resolve_resume_model(task_config)
    if not resume_model:
        return None

    save_path = str(resume_model.get("save_path") or "").strip()
    if not save_path:
        return None

    model_cache_dir = _ensure_dir(os.getenv("TRAINER_MODEL_CACHE_DIR", DEFAULT_MODEL_CACHE_DIR))
    model_id = int(resume_model.get("model_id") or 0)
    target_name = f"resume_model_{model_id or Path(save_path).stem}.pt"
    local_path = os.path.join(model_cache_dir, target_name)
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path

    cfg = get_s3_config()
    download_from_s3(save_path, local_path, cfg.models_bucket_name)
    return local_path


def _resolve_runtime_model_path(task_config: Dict[str, Any], default_name: str) -> str:
    local_resume_model = _download_resume_model_to_local(task_config)
    if local_resume_model:
        return local_resume_model
    return _resolve_model_name(task_config, default_name)


def _prepare_cached_materialized_dataset(
    *,
    sources: Optional[List[Dict[str, Any]]],
    task_type: str,
    classes: List[str],
    task_config: Dict[str, Any],
    label_format: Optional[str] = None,
) -> tuple[Any, Optional[Any], bool]:
    cache_mode = _resolve_dataset_cache_mode(task_config)
    cache_root = os.getenv("TRAINER_DATASET_CACHE_ROOT", DEFAULT_TRAIN_CACHE_ROOT)
    if cache_mode == "off":
        materialized = materialize_training_manifest(sources or [], task_type, classes)
        return materialized, None, False

    cache_key = build_training_cache_key(
        task_type=task_type,
        sources=sources or [],
        class_names=classes,
        label_format=label_format,
    )
    cache = prepare_training_cache_dir(cache_key, cache_root=cache_root)
    if cache_mode == "refresh" and os.path.isdir(cache.cache_dir):
        cleanup_temp_dir(cache.cache_dir)
        cache.hit = False

    if cache.hit:
        cloned_dir = clone_cached_dataset(
            cache.cache_dir,
            prefix=f"manifest_{task_type}_cached_",
        )
        return load_materialized_training_dataset(cloned_dir), cache, True

    materialized = materialize_training_manifest(sources or [], task_type, classes)
    finalize_training_cache(cache=cache, source_dir=materialized.root_dir)
    return materialized, cache, False


def _resolve_augmentation_kwargs(
    task_type: str,
    task_config: Dict[str, Any],
) -> Dict[str, Any]:
    augmentation = task_config.get("augmentation")
    if not isinstance(augmentation, dict):
        return {}

    enabled = augmentation.get("enabled", True)
    if isinstance(enabled, str):
        enabled = enabled.strip().lower() in {"1", "true", "yes", "y", "on"}
    else:
        enabled = bool(enabled)

    if task_type == "classification":
        if not enabled:
            return {
                "degrees": 0.0,
                "translate": 0.0,
                "scale": 0.0,
                "shear": 0.0,
                "perspective": 0.0,
                "fliplr": 0.0,
                "flipud": 0.0,
                "hsv_h": 0.0,
                "hsv_s": 0.0,
                "hsv_v": 0.0,
                "auto_augment": None,
                "erasing": 0.0,
            }

        kwargs: Dict[str, Any] = {}
        for key in ("degrees", "translate", "scale", "shear", "perspective", "fliplr", "flipud", "hsv_h", "hsv_s", "hsv_v"):
            if key in augmentation and augmentation.get(key) is not None:
                kwargs[key] = float(augmentation[key])
        if "auto_augment" in augmentation:
            auto_augment = augmentation.get("auto_augment")
            kwargs["auto_augment"] = None if auto_augment in {None, "", "none"} else auto_augment
        if "erasing" in augmentation and augmentation.get("erasing") is not None:
            kwargs["erasing"] = float(augmentation["erasing"])
        return kwargs

    if not enabled:
        return {
            "degrees": 0.0,
            "translate": 0.0,
            "scale": 0.0,
            "shear": 0.0,
            "perspective": 0.0,
            "fliplr": 0.0,
            "flipud": 0.0,
            "hsv_h": 0.0,
            "hsv_s": 0.0,
            "hsv_v": 0.0,
            "mosaic": 0.0,
            "mixup": 0.0,
            "copy_paste": 0.0,
            "close_mosaic": 0,
        }

    kwargs = {}
    for key in ("degrees", "translate", "scale", "shear", "perspective", "fliplr", "flipud", "hsv_h", "hsv_s", "hsv_v"):
        if key in augmentation and augmentation.get(key) is not None:
            kwargs[key] = float(augmentation[key])
    for key in ("mosaic", "mixup", "copy_paste"):
        if key in augmentation and augmentation.get(key) is not None:
            kwargs[key] = float(augmentation[key])
    if "close_mosaic" in augmentation and augmentation.get("close_mosaic") is not None:
        kwargs["close_mosaic"] = int(augmentation["close_mosaic"])
    return kwargs


def _build_train_kwargs(
    task_type: str,
    data: str,
    task_config: Dict[str, Any],
) -> Dict[str, Any]:
    train_kwargs = {
        "data": data,
        "epochs": task_config.get("epoch", 10),
        "imgsz": task_config.get("size", 640),
        "batch": task_config.get("batch", 8),
        "device": task_config.get("device", "cpu"),
    }
    train_kwargs.update(_resolve_optimizer_kwargs(task_config))
    train_kwargs.update(_resolve_augmentation_kwargs(task_type, task_config))
    return train_kwargs


def _summarize_augmentation_kwargs(train_kwargs: Dict[str, Any]) -> str:
    keys = [
        "degrees",
        "translate",
        "scale",
        "shear",
        "perspective",
        "fliplr",
        "flipud",
        "hsv_h",
        "hsv_s",
        "hsv_v",
        "mosaic",
        "mixup",
        "copy_paste",
        "close_mosaic",
        "auto_augment",
        "erasing",
    ]
    parts = [f"{key}={train_kwargs[key]}" for key in keys if key in train_kwargs]
    return ", ".join(parts) if parts else "default"


def _resolve_optimizer_kwargs(task_config: Dict[str, Any]) -> Dict[str, Any]:
    optimizer_config = task_config.get("optimizer_config")
    if not isinstance(optimizer_config, dict):
        return {}

    kwargs: Dict[str, Any] = {}
    if optimizer_config.get("optimizer"):
        kwargs["optimizer"] = str(optimizer_config["optimizer"])
    for key in ("patience",):
        if optimizer_config.get(key) is not None:
            kwargs[key] = int(optimizer_config[key])
    for key in ("lr0", "lrf", "momentum", "weight_decay", "warmup_epochs"):
        if optimizer_config.get(key) is not None:
            kwargs[key] = float(optimizer_config[key])
    if optimizer_config.get("cos_lr") is not None:
        kwargs["cos_lr"] = bool(optimizer_config["cos_lr"])
    return kwargs


def _summarize_optimizer_kwargs(train_kwargs: Dict[str, Any]) -> str:
    keys = [
        "optimizer",
        "patience",
        "lr0",
        "lrf",
        "momentum",
        "weight_decay",
        "warmup_epochs",
        "cos_lr",
    ]
    parts = [f"{key}={train_kwargs[key]}" for key in keys if key in train_kwargs]
    return ", ".join(parts) if parts else "default"


def _log_training_config(
    task_id: int,
    task_type: str,
    task_config: Dict[str, Any],
    train_kwargs: Dict[str, Any],
):
    lines = [
        f"[train] Task type: {task_type}",
        f"[train] Task config: {json.dumps(task_config, ensure_ascii=False, sort_keys=True)}",
        f"[train] Train kwargs: {json.dumps(train_kwargs, ensure_ascii=False, sort_keys=True, default=str)}",
    ]
    for line in lines:
        logger.info(f"Task {task_id} - {line}")
        publish_task_log(
            task_id,
            line,
            SERVICE_NAME,
        )


def _export_onnx_model(
    task_id: int,
    best_pt_path: str,
    task_config: Dict[str, Any],
) -> Optional[str]:
    if not _should_export_onnx(task_config):
        return None

    publish_task_log(task_id, "[post-train] Exporting ONNX model...", SERVICE_NAME)
    export_kwargs = {
        "format": "onnx",
        "dynamic": bool(task_config.get("onnx_dynamic", False)),
        "simplify": bool(task_config.get("onnx_simplify", False)),
    }
    imgsz = task_config.get("size")
    if imgsz:
        export_kwargs["imgsz"] = imgsz

    export_model = YOLO(best_pt_path)
    exported = export_model.export(**export_kwargs)
    exported_path = str(exported) if exported else os.path.splitext(best_pt_path)[0] + ".onnx"
    if not os.path.exists(exported_path):
        fallback_path = os.path.splitext(best_pt_path)[0] + ".onnx"
        if os.path.exists(fallback_path):
            exported_path = fallback_path
        else:
            raise FileNotFoundError(f"ONNX export file not found: {exported_path}")
    return exported_path


def _file_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _file_size_bytes(file_path: str) -> int:
    return int(os.path.getsize(file_path))


def _log_model_artifact_summary(
    task_id: int,
    *,
    artifact_type: str,
    local_path: str,
    s3_key: str | None,
    class_names: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    if not local_path or not os.path.exists(local_path):
        return

    payload = {
        "artifact_type": artifact_type,
        "local_path": local_path,
        "file_size_bytes": _file_size_bytes(local_path),
        "sha256": _file_sha256(local_path),
        "s3_key": s3_key,
    }
    if class_names is not None:
        payload["class_names"] = list(class_names)
        payload["class_count"] = len(class_names)
    if extra:
        payload.update(extra)

    message = f"[artifact] {json.dumps(payload, ensure_ascii=False, sort_keys=True)}"
    logger.info(f"Task {task_id} - {message}")
    publish_task_log(task_id, message, SERVICE_NAME)


class TrainingCallback:
    """训练回调管理器 - 通过 MQ 发送消息"""

    def __init__(self, task_id: int, cancel_event: Optional[threading.Event] = None):
        self.task_id = task_id
        self.cancel_event = cancel_event

    def _ensure_not_cancelled(self):
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise TaskCancelledError("Training cancelled by user")

    def _extract_epoch_metrics(self, trainer: BaseTrainer) -> Dict[str, Optional[float]]:
        metrics_candidates: list[Dict[str, Any]] = []
        trainer_metrics = getattr(trainer, "metrics", None)
        if isinstance(trainer_metrics, dict):
            metrics_candidates.append(trainer_metrics)

        validator = getattr(trainer, "validator", None)
        validator_metrics = getattr(validator, "metrics", None) if validator is not None else None
        results_dict = getattr(validator_metrics, "results_dict", None) if validator_metrics is not None else None
        if isinstance(results_dict, dict):
            metrics_candidates.append(results_dict)

        def _to_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def _lookup(keys: List[str]) -> Optional[float]:
            for metrics in metrics_candidates:
                for key in keys:
                    if key in metrics:
                        converted = _to_float(metrics.get(key))
                        if converted is not None:
                            return converted
            return None

        return {
            "precision": _lookup(["metrics/precision(B)", "precision", "P"]),
            "recall": _lookup(["metrics/recall(B)", "recall", "R"]),
            "mAP50": _lookup(["metrics/mAP50(B)", "mAP50", "map50"]),
            "mAP50_95": _lookup(["metrics/mAP50-95(B)", "mAP50-95", "map", "map50-95"]),
        }

    def on_train_epoch_end(self, trainer: BaseTrainer):
        """每个 epoch 结束时触发"""
        self._ensure_not_cancelled()
        epoch_metrics = self._extract_epoch_metrics(trainer)
        task_info = {
            "type": "epoch",
            "epoch": trainer.epoch,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss) if hasattr(trainer, 'tloss') else None,
            "precision": epoch_metrics["precision"],
            "recall": epoch_metrics["recall"],
            "mAP50": epoch_metrics["mAP50"],
            "mAP50_95": epoch_metrics["mAP50_95"],
            "mAP": epoch_metrics["mAP50_95"] if epoch_metrics["mAP50_95"] is not None else epoch_metrics["mAP50"],
        }
        # 通过 MQ 发送日志
        publish_task_log(
            task_id=self.task_id,
            log_content=f"[epoch] {json.dumps(task_info)}",
            service_name=SERVICE_NAME,
        )
        logger.info(f"Task {self.task_id} - Epoch {trainer.epoch} completed")

    def on_train_end(self, trainer: BaseTrainer):
        """训练结束时触发"""
        logger.info(f"Task {self.task_id} - Training completed")

    def on_train_batch_end(self, trainer: BaseTrainer):
        """每个 batch 结束时检查取消信号，缩短停止延迟。"""
        self._ensure_not_cancelled()


def _train_detection_model(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """内部函数：训练目标检测模型"""
    temp_folder = None
    train_dir = None
    cache_hit = False

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting detection training")
        publish_task_log(
            task_id, "[pre-train] Starting detection model training...", SERVICE_NAME)

        publish_task_log(
            task_id, "[pre-train] Materializing samples from training manifest...", SERVICE_NAME)
        requested_label_format = task_config.get(
            "label_format",
            task_config.get("train_format", "auto"),
        )
        materialized, _, cache_hit = _prepare_cached_materialized_dataset(
            sources=sources,
            task_type="detection",
            classes=classes,
            task_config=task_config,
            label_format=requested_label_format,
        )
        temp_folder = materialized.root_dir
        publish_task_log(
            task_id,
            f"[pre-train] Dataset cache: mode={_resolve_dataset_cache_mode(task_config)}, hit={'yes' if cache_hit else 'no'}",
            SERVICE_NAME,
        )

        model_name = _resolve_model_name(task_config, "yolo11n.pt")
        runtime_model_path = _resolve_runtime_model_path(task_config, "yolo11n.pt")
        resume_display_name = _resolve_resume_display_name(task_config, model_name)
        if runtime_model_path != model_name:
            publish_task_log(
                task_id,
                f"[pre-train] Resume training from previous model: {resume_display_name}",
                SERVICE_NAME,
            )

        # 准备训练数据
        publish_task_log(
            task_id, "[pre-train] Preparing training dataset...", SERVICE_NAME)
        prepared_dataset = prepare_detection_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            all_labels_dir=os.path.join(temp_folder, "annotations"),
            class_names=classes,
            label_format=requested_label_format,
            model_name=model_name,
        )
        train_dir = prepared_dataset.root_dir
        stats = prepared_dataset.stats
        publish_task_log(
            task_id,
            (
                "[pre-train] Detection labels normalized: "
                f"target={prepared_dataset.label_format}, "
                f"images={stats.images}, "
                f"bbox={stats.bbox_labels}, "
                f"obb={stats.obb_labels}, "
                f"to_bbox={stats.converted_to_bbox}, "
                f"to_obb={stats.converted_to_obb}"
            ),
            SERVICE_NAME,
        )

        # 创建回调
        callback = TrainingCallback(task_id, cancel_event)

        # 加载模型并开始训练
        train_kwargs = _build_train_kwargs(
            task_type="detection",
            data=os.path.join(train_dir, "data.yaml"),
            task_config=task_config,
        )
        epochs = int(train_kwargs["epochs"])
        imgsz = int(train_kwargs["imgsz"])
        batch = int(train_kwargs["batch"])

        publish_task_log(
            task_id, f"[pre-train] Loading model {resume_display_name}...", SERVICE_NAME)
        model = _load_yolo_model(runtime_model_path)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(
            task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)
        _log_training_config(
            task_id=task_id,
            task_type="detection",
            task_config=task_config,
            train_kwargs=train_kwargs,
        )
        publish_task_log(
            task_id,
            f"[train] Augmentation: {_summarize_augmentation_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )
        publish_task_log(
            task_id,
            f"[train] Optimizer: {_summarize_optimizer_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )

        # 开始训练
        model.train(**train_kwargs)

        # 获取训练结果
        save_dir = str(model.trainer.save_dir.absolute())
        best_pt_path = os.path.join(save_dir, "weights", "best.pt")

        if not os.path.exists(best_pt_path):
            raise FileNotFoundError(f"Model file not found: {best_pt_path}")

        # 上传模型到 S3
        publish_task_status(
            task_id,
            TaskStatus.POST_PROCESS,
            SERVICE_NAME,
            "Uploading model artifacts and registering model",
        )
        onnx_model_path = _export_onnx_model(
            task_id=task_id,
            best_pt_path=best_pt_path,
            task_config=task_config,
        )
        publish_task_log(
            task_id, "[post-train] Uploading model to S3...", SERVICE_NAME)
        s3_config = get_s3_config()
        pt_name = f"{uuid.uuid4()}.pt"
        _log_model_artifact_summary(
            task_id,
            artifact_type="pt",
            local_path=best_pt_path,
            s3_key=pt_name,
            class_names=classes,
            extra={
                "task_kind": _detection_task_kind(prepared_dataset.label_format),
                "label_format": prepared_dataset.label_format,
            },
        )
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            _log_model_artifact_summary(
                task_id,
                artifact_type="onnx",
                local_path=onnx_model_path,
                s3_key=onnx_name,
                class_names=classes,
                extra={
                    "task_kind": _detection_task_kind(prepared_dataset.label_format),
                    "label_format": prepared_dataset.label_format,
                },
            )
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息（让主服务写入数据库）
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": resume_display_name,
            "trained_model_name": _trained_model_name(
                resume_display_name,
                _detection_task_kind(prepared_dataset.label_format),
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": _detection_task_kind(prepared_dataset.label_format),
            "task_kind": _detection_task_kind(prepared_dataset.label_format),
            "label_format": prepared_dataset.label_format,
        }
        publish_task_log(
            task_id,
            f"[artifact] register_model_info={json.dumps(model_info, ensure_ascii=False, sort_keys=True)}",
            SERVICE_NAME,
        )
        publish_model_registered(task_id, model_info, SERVICE_NAME)

        # 更新任务状态为完成
        publish_task_status(task_id, TaskStatus.COMPLETED,
                            SERVICE_NAME, f"Model saved to {pt_name}")
        publish_task_log(
            task_id, f"[post-train] Training completed. Model: {pt_name}", SERVICE_NAME)

    except TaskCancelledError as e:
        logger.warning(f"Training cancelled for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(
            task_id, f"[cancel] {str(e)}", SERVICE_NAME, "WARNING")
    except Exception as e:
        logger.error(f"Training failed for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(
            task_id, f"[error] Training failed: {str(e)}", SERVICE_NAME, "ERROR")
    finally:
        # 清理临时目录
        if train_dir and os.path.exists(train_dir):
            cleanup_temp_dir(train_dir)
        if temp_folder and os.path.exists(temp_folder):
            cleanup_temp_dir(temp_folder)


def _train_classification_model(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """内部函数：训练分类模型"""
    temp_folder = None
    train_dir = None
    classes = task_config.get("classes") or []
    cache_hit = False

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting classification training")
        publish_task_log(
            task_id, "[pre-train] Starting classification model training...", SERVICE_NAME)

        publish_task_log(
            task_id, "[pre-train] Materializing samples from training manifest...", SERVICE_NAME)
        materialized, _, cache_hit = _prepare_cached_materialized_dataset(
            sources=sources,
            task_type="classification",
            classes=classes,
            task_config=task_config,
        )
        temp_folder = materialized.root_dir
        class_info = materialized.class_info
        publish_task_log(
            task_id,
            f"[pre-train] Dataset cache: mode={_resolve_dataset_cache_mode(task_config)}, hit={'yes' if cache_hit else 'no'}",
            SERVICE_NAME,
        )

        # 准备训练数据
        publish_task_log(
            task_id, "[pre-train] Preparing training dataset...", SERVICE_NAME)
        train_dir = prepare_classification_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            class_info=class_info,
        )

        # 创建回调
        callback = TrainingCallback(task_id, cancel_event)

        # 加载模型并开始训练
        model_name = _resolve_model_name(task_config, "yolo11n-cls.pt")
        runtime_model_path = _resolve_runtime_model_path(task_config, "yolo11n-cls.pt")
        resume_display_name = _resolve_resume_display_name(task_config, model_name)
        train_kwargs = _build_train_kwargs(
            task_type="classification",
            data=train_dir,
            task_config=task_config,
        )
        epochs = int(train_kwargs["epochs"])
        imgsz = int(train_kwargs["imgsz"])
        batch = int(train_kwargs["batch"])

        publish_task_log(
            task_id, f"[pre-train] Loading model {resume_display_name}...", SERVICE_NAME)
        if runtime_model_path != model_name:
            publish_task_log(
                task_id,
                f"[pre-train] Resume training from previous model: {resume_display_name}",
                SERVICE_NAME,
            )
        model = _load_yolo_model(runtime_model_path)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(
            task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)
        _log_training_config(
            task_id=task_id,
            task_type="classification",
            task_config=task_config,
            train_kwargs=train_kwargs,
        )
        publish_task_log(
            task_id,
            f"[train] Augmentation: {_summarize_augmentation_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )
        publish_task_log(
            task_id,
            f"[train] Optimizer: {_summarize_optimizer_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )

        # 开始训练
        model.train(**train_kwargs)

        # 获取训练结果
        save_dir = str(model.trainer.save_dir.absolute())
        best_pt_path = os.path.join(save_dir, "weights", "best.pt")

        if not os.path.exists(best_pt_path):
            raise FileNotFoundError(f"Model file not found: {best_pt_path}")

        # 上传模型到 S3
        publish_task_status(
            task_id,
            TaskStatus.POST_PROCESS,
            SERVICE_NAME,
            "Uploading model artifacts and registering model",
        )
        onnx_model_path = _export_onnx_model(
            task_id=task_id,
            best_pt_path=best_pt_path,
            task_config=task_config,
        )
        publish_task_log(
            task_id, "[post-train] Uploading model to S3...", SERVICE_NAME)
        s3_config = get_s3_config()
        pt_name = f"{uuid.uuid4()}.pt"
        _log_model_artifact_summary(
            task_id,
            artifact_type="pt",
            local_path=best_pt_path,
            s3_key=pt_name,
            class_names=classes,
            extra={"task_kind": "classification"},
        )
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            _log_model_artifact_summary(
                task_id,
                artifact_type="onnx",
                local_path=onnx_model_path,
                s3_key=onnx_name,
                class_names=classes,
                extra={"task_kind": "classification"},
            )
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": resume_display_name,
            "trained_model_name": _trained_model_name(
                resume_display_name,
                "classification",
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": "classification",
            "task_kind": "classification",
        }
        publish_task_log(
            task_id,
            f"[artifact] register_model_info={json.dumps(model_info, ensure_ascii=False, sort_keys=True)}",
            SERVICE_NAME,
        )
        publish_model_registered(task_id, model_info, SERVICE_NAME)

        # 更新任务状态为完成
        publish_task_status(task_id, TaskStatus.COMPLETED,
                            SERVICE_NAME, f"Model saved to {pt_name}")
        publish_task_log(
            task_id, f"[post-train] Training completed. Model: {pt_name}", SERVICE_NAME)

    except TaskCancelledError as e:
        logger.warning(f"Classification training cancelled for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(
            task_id, f"[cancel] {str(e)}", SERVICE_NAME, "WARNING")
    except Exception as e:
        logger.error(f"Classification training failed for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(
            task_id, f"[error] Training failed: {str(e)}", SERVICE_NAME, "ERROR")
    finally:
        # 清理临时目录
        if train_dir and os.path.exists(train_dir):
            cleanup_temp_dir(train_dir)
        if temp_folder and os.path.exists(temp_folder):
            cleanup_temp_dir(temp_folder)


def _train_segmentation_model(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    temp_folder = None
    train_dir = None
    cache_hit = False

    try:
        publish_task_status(task_id, TaskStatus.RUNNING, SERVICE_NAME, "Starting segmentation training")
        publish_task_log(task_id, "[pre-train] Starting segmentation model training...", SERVICE_NAME)

        publish_task_log(task_id, "[pre-train] Materializing samples from training manifest...", SERVICE_NAME)
        materialized, _, cache_hit = _prepare_cached_materialized_dataset(
            sources=sources,
            task_type="segmentation",
            classes=classes,
            task_config=task_config,
        )
        temp_folder = materialized.root_dir
        publish_task_log(
            task_id,
            f"[pre-train] Dataset cache: mode={_resolve_dataset_cache_mode(task_config)}, hit={'yes' if cache_hit else 'no'}",
            SERVICE_NAME,
        )

        model_name = _resolve_model_name(task_config, "yolo11n-seg.pt")
        runtime_model_path = _resolve_runtime_model_path(task_config, "yolo11n-seg.pt")
        resume_display_name = _resolve_resume_display_name(task_config, model_name)

        publish_task_log(task_id, "[pre-train] Preparing segmentation dataset...", SERVICE_NAME)
        prepared_dataset = prepare_segmentation_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            all_labels_dir=os.path.join(temp_folder, "annotations"),
            class_names=classes,
        )
        train_dir = prepared_dataset.root_dir

        callback = TrainingCallback(task_id, cancel_event)
        train_kwargs = _build_train_kwargs(
            task_type="segmentation",
            data=os.path.join(train_dir, "data.yaml"),
            task_config=task_config,
        )
        epochs = int(train_kwargs["epochs"])
        imgsz = int(train_kwargs["imgsz"])
        batch = int(train_kwargs["batch"])

        publish_task_log(task_id, f"[pre-train] Loading model {resume_display_name}...", SERVICE_NAME)
        if runtime_model_path != model_name:
            publish_task_log(
                task_id,
                f"[pre-train] Resume training from previous model: {resume_display_name}",
                SERVICE_NAME,
            )
        model = _load_yolo_model(runtime_model_path)
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)
        _log_training_config(
            task_id=task_id,
            task_type="segmentation",
            task_config=task_config,
            train_kwargs=train_kwargs,
        )
        publish_task_log(
            task_id,
            f"[train] Augmentation: {_summarize_augmentation_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )
        publish_task_log(
            task_id,
            f"[train] Optimizer: {_summarize_optimizer_kwargs(train_kwargs)}",
            SERVICE_NAME,
        )
        model.train(**train_kwargs)

        save_dir = str(model.trainer.save_dir.absolute())
        best_pt_path = os.path.join(save_dir, "weights", "best.pt")
        if not os.path.exists(best_pt_path):
            raise FileNotFoundError(f"Model file not found: {best_pt_path}")

        publish_task_status(
            task_id,
            TaskStatus.POST_PROCESS,
            SERVICE_NAME,
            "Uploading model artifacts and registering model",
        )
        onnx_model_path = _export_onnx_model(
            task_id=task_id,
            best_pt_path=best_pt_path,
            task_config=task_config,
        )
        publish_task_log(task_id, "[post-train] Uploading model to S3...", SERVICE_NAME)
        s3_config = get_s3_config()
        pt_name = f"{uuid.uuid4()}.pt"
        _log_model_artifact_summary(
            task_id,
            artifact_type="pt",
            local_path=best_pt_path,
            s3_key=pt_name,
            class_names=classes,
            extra={"task_kind": _segmentation_task_kind()},
        )
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            _log_model_artifact_summary(
                task_id,
                artifact_type="onnx",
                local_path=onnx_model_path,
                s3_key=onnx_name,
                class_names=classes,
                extra={"task_kind": _segmentation_task_kind()},
            )
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": resume_display_name,
            "trained_model_name": _trained_model_name(
                resume_display_name,
                _segmentation_task_kind(),
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": _segmentation_task_kind(),
            "task_kind": _segmentation_task_kind(),
        }
        publish_task_log(
            task_id,
            f"[artifact] register_model_info={json.dumps(model_info, ensure_ascii=False, sort_keys=True)}",
            SERVICE_NAME,
        )
        publish_model_registered(task_id, model_info, SERVICE_NAME)

        publish_task_status(task_id, TaskStatus.COMPLETED, SERVICE_NAME, f"Model saved to {pt_name}")
        publish_task_log(task_id, f"[post-train] Training completed. Model: {pt_name}", SERVICE_NAME)

    except TaskCancelledError as e:
        logger.warning(f"Segmentation training cancelled for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(task_id, f"[cancel] {str(e)}", SERVICE_NAME, "WARNING")
    except Exception as e:
        logger.error(f"Segmentation training failed for task {task_id}: {e}")
        publish_task_status(task_id, TaskStatus.FAILED, SERVICE_NAME, str(e))
        publish_task_log(task_id, f"[error] Training failed: {str(e)}", SERVICE_NAME, "ERROR")
    finally:
        if train_dir and os.path.exists(train_dir):
            cleanup_temp_dir(train_dir)
        if temp_folder and os.path.exists(temp_folder):
            cleanup_temp_dir(temp_folder)


def train_detection(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """启动目标检测模型训练（异步）"""
    thread = threading.Thread(
        target=run_detection_task,
        kwargs={
            "task_id": task_id,
            "sources": sources,
            "classes": classes,
            "task_config": task_config,
            "cancel_event": cancel_event,
        },
        daemon=True,
    )
    thread.start()
    return thread


def train_classification(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """启动分类模型训练（异步）"""
    thread = threading.Thread(
        target=run_classification_task,
        kwargs={
            "task_id": task_id,
            "sources": sources,
            "task_config": task_config,
            "cancel_event": cancel_event,
        },
        daemon=True,
    )
    thread.start()
    return thread


def run_detection_task(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """同步执行目标检测训练任务"""
    _train_detection_model(
        task_id=task_id,
        sources=sources,
        classes=classes,
        task_config=task_config,
        cancel_event=cancel_event,
    )


def run_classification_task(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """同步执行分类训练任务"""
    _train_classification_model(
        task_id=task_id,
        sources=sources,
        task_config=task_config,
        cancel_event=cancel_event,
    )


def run_segmentation_task(
    task_id: int,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    _train_segmentation_model(
        task_id=task_id,
        sources=sources,
        classes=classes,
        task_config=task_config,
        cancel_event=cancel_event,
    )
