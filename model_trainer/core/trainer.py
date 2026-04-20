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
from pathlib import Path
from typing import Any, Dict, List, Optional

from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from core.dataset import (
    cleanup_temp_dir,
    download_dataset_from_s3,
    download_training_sources_from_s3,
    merge_classification_sources,
    merge_detection_sources,
    merge_segmentation_sources,
    prepare_classification_dataset,
    prepare_detection_dataset,
    prepare_segmentation_dataset,
)
from utils.config import get_s3_config, upload_to_s3
from utils.logger import logger
from utils.mq import (
    TaskStatus,
    publish_model_registered,
    publish_task_log,
    publish_task_status,
)

SERVICE_NAME = "model-trainer"
DEFAULT_BASE_MODEL_DIR = "./base_model"


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


class TrainingCallback:
    """训练回调管理器 - 通过 MQ 发送消息"""

    def __init__(self, task_id: int, cancel_event: Optional[threading.Event] = None):
        self.task_id = task_id
        self.cancel_event = cancel_event

    def _ensure_not_cancelled(self):
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise TaskCancelledError("Training cancelled by user")

    def on_train_epoch_end(self, trainer: BaseTrainer):
        """每个 epoch 结束时触发"""
        self._ensure_not_cancelled()
        task_info = {
            "type": "epoch",
            "epoch": trainer.epoch,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss) if hasattr(trainer, 'tloss') else None,
            "mAP": trainer.metrics.get("mAP50-95", 0.0) if hasattr(trainer, 'metrics') else 0.0,
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
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """内部函数：训练目标检测模型"""
    temp_folder = None
    train_dir = None
    source_downloads = None

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting detection training")
        publish_task_log(
            task_id, "[pre-train] Starting detection model training...", SERVICE_NAME)

        # 下载数据集
        publish_task_log(
            task_id, "[pre-train] Downloading dataset from S3...", SERVICE_NAME)
        if sources:
            source_downloads = download_training_sources_from_s3(sources)
            temp_folder = merge_detection_sources(source_downloads)
        else:
            temp_folder = download_dataset_from_s3(dataset_path, annotation_path)

        if not temp_folder:
            raise ValueError("Failed to download dataset")

        model_name = task_config.get("name", "yolo11n.pt")
        requested_label_format = task_config.get(
            "label_format",
            task_config.get("train_format", "auto"),
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
        epochs = task_config.get("epoch", 10)
        imgsz = task_config.get("size", 640)
        batch = task_config.get("batch", 8)
        device = task_config.get("device", "cpu")

        publish_task_log(
            task_id, f"[pre-train] Loading model {model_name}...", SERVICE_NAME)
        model = _load_yolo_model(model_name)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(
            task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)

        # 开始训练
        model.train(
            data=os.path.join(train_dir, "data.yaml"),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
        )

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
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息（让主服务写入数据库）
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": model_name,
            "trained_model_name": _trained_model_name(
                model_name,
                _detection_task_kind(prepared_dataset.label_format),
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": _detection_task_kind(prepared_dataset.label_format),
            "task_kind": _detection_task_kind(prepared_dataset.label_format),
            "label_format": prepared_dataset.label_format,
        }
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
        if source_downloads:
            for source in source_downloads:
                if os.path.exists(source.local_root):
                    cleanup_temp_dir(source.local_root)


def _train_classification_model(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """内部函数：训练分类模型"""
    temp_folder = None
    train_dir = None
    classes = task_config.get("classes") or []
    source_downloads = None

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting classification training")
        publish_task_log(
            task_id, "[pre-train] Starting classification model training...", SERVICE_NAME)

        # 下载数据集
        publish_task_log(
            task_id, "[pre-train] Downloading dataset from S3...", SERVICE_NAME)
        if sources:
            source_downloads = download_training_sources_from_s3(sources)
            temp_folder, class_info = merge_classification_sources(source_downloads)
        else:
            temp_folder = download_dataset_from_s3(dataset_path, annotation_path)

            if not temp_folder:
                raise ValueError("Failed to download dataset")

            # 加载类别信息
            classes_json_path = os.path.join(
                temp_folder, "annotations", "classes.json")
            if not os.path.exists(classes_json_path):
                raise FileNotFoundError("classes.json not found")

            with open(classes_json_path, "r", encoding="utf-8") as f:
                class_info = json.load(f)

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
        model_name = task_config.get("name", "yolo11n-cls.pt")
        epochs = task_config.get("epoch", 10)
        imgsz = task_config.get("size", 640)
        batch = task_config.get("batch", 8)
        device = task_config.get("device", "cpu")

        publish_task_log(
            task_id, f"[pre-train] Loading model {model_name}...", SERVICE_NAME)
        model = _load_yolo_model(model_name)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(
            task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)

        # 开始训练
        model.train(
            data=train_dir,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
        )

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
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": model_name,
            "trained_model_name": _trained_model_name(
                model_name,
                "classification",
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": "classification",
            "task_kind": "classification",
        }
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
        if source_downloads:
            for source in source_downloads:
                if os.path.exists(source.local_root):
                    cleanup_temp_dir(source.local_root)


def _train_segmentation_model(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    temp_folder = None
    train_dir = None
    source_downloads = None

    try:
        publish_task_status(task_id, TaskStatus.RUNNING, SERVICE_NAME, "Starting segmentation training")
        publish_task_log(task_id, "[pre-train] Starting segmentation model training...", SERVICE_NAME)

        publish_task_log(task_id, "[pre-train] Downloading dataset from S3...", SERVICE_NAME)
        if sources:
            source_downloads = download_training_sources_from_s3(sources)
            temp_folder = merge_segmentation_sources(source_downloads)
        else:
            temp_folder = download_dataset_from_s3(dataset_path, annotation_path)

        if not temp_folder:
            raise ValueError("Failed to download dataset")

        model_name = task_config.get("name", "yolo11n-seg.pt")

        publish_task_log(task_id, "[pre-train] Preparing segmentation dataset...", SERVICE_NAME)
        prepared_dataset = prepare_segmentation_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            all_labels_dir=os.path.join(temp_folder, "annotations"),
            class_names=classes,
        )
        train_dir = prepared_dataset.root_dir

        callback = TrainingCallback(task_id, cancel_event)
        epochs = task_config.get("epoch", 10)
        imgsz = task_config.get("size", 640)
        batch = task_config.get("batch", 8)
        device = task_config.get("device", "cpu")

        publish_task_log(task_id, f"[pre-train] Loading model {model_name}...", SERVICE_NAME)
        model = _load_yolo_model(model_name)
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)
        model.add_callback("on_train_batch_end", callback.on_train_batch_end)

        publish_task_log(task_id, f"[train] Starting: epochs={epochs}, imgsz={imgsz}, batch={batch}", SERVICE_NAME)
        model.train(
            data=os.path.join(train_dir, "data.yaml"),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
        )

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
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)
        onnx_name = None
        if onnx_model_path:
            onnx_name = f"{uuid.uuid4()}.onnx"
            upload_to_s3(onnx_model_path, onnx_name, s3_config.models_bucket_name)

        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "onnx_save_path": onnx_name,
            "class_names": classes,
            "base_model_name": model_name,
            "trained_model_name": _trained_model_name(
                model_name,
                _segmentation_task_kind(),
                task_id,
            ),
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": _segmentation_task_kind(),
            "task_kind": _segmentation_task_kind(),
        }
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
        if source_downloads:
            for source in source_downloads:
                if os.path.exists(source.local_root):
                    cleanup_temp_dir(source.local_root)


def train_detection(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
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
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
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
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """启动分类模型训练（异步）"""
    thread = threading.Thread(
        target=run_classification_task,
        kwargs={
            "task_id": task_id,
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
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
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """同步执行目标检测训练任务"""
    _train_detection_model(
        task_id=task_id,
        dataset_path=dataset_path,
        annotation_path=annotation_path,
        sources=sources,
        classes=classes,
        task_config=task_config,
        cancel_event=cancel_event,
    )


def run_classification_task(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    """同步执行分类训练任务"""
    _train_classification_model(
        task_id=task_id,
        dataset_path=dataset_path,
        annotation_path=annotation_path,
        sources=sources,
        task_config=task_config,
        cancel_event=cancel_event,
    )


def run_segmentation_task(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    sources: Optional[List[Dict[str, Any]]],
    classes: List[str],
    task_config: Dict[str, Any],
    cancel_event: Optional[threading.Event] = None,
):
    _train_segmentation_model(
        task_id=task_id,
        dataset_path=dataset_path,
        annotation_path=annotation_path,
        sources=sources,
        classes=classes,
        task_config=task_config,
        cancel_event=cancel_event,
    )
