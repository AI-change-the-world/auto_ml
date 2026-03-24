"""
训练核心逻辑
使用 RabbitMQ 发送状态更新和日志，不直接写数据库
"""
import json
import os
import shutil
import threading
import uuid
from typing import Any, Dict, List, Optional

from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from core.dataset import (
    cleanup_temp_dir,
    download_dataset_from_s3,
    prepare_classification_dataset,
    prepare_detection_dataset,
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


class TrainingCallback:
    """训练回调管理器 - 通过 MQ 发送消息"""

    def __init__(self, task_id: int):
        self.task_id = task_id

    def on_train_epoch_end(self, trainer: BaseTrainer):
        """每个 epoch 结束时触发"""
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


def _train_detection_model(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    classes: List[str],
    task_config: Dict[str, Any],
):
    """内部函数：训练目标检测模型"""
    temp_folder = None
    train_dir = None

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting detection training")
        publish_task_log(
            task_id, "[pre-train] Starting detection model training...", SERVICE_NAME)

        # 下载数据集
        publish_task_log(
            task_id, "[pre-train] Downloading dataset from S3...", SERVICE_NAME)
        temp_folder = download_dataset_from_s3(dataset_path, annotation_path)

        if not temp_folder:
            raise ValueError("Failed to download dataset")

        # 准备训练数据
        publish_task_log(
            task_id, "[pre-train] Preparing training dataset...", SERVICE_NAME)
        train_dir = prepare_detection_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            all_labels_dir=os.path.join(temp_folder, "annotations"),
            class_names=classes,
        )

        # 创建回调
        callback = TrainingCallback(task_id)

        # 加载模型并开始训练
        model_name = task_config.get("name", "yolo11n.pt")
        epochs = task_config.get("epoch", 10)
        imgsz = task_config.get("size", 640)
        batch = task_config.get("batch", 8)
        device = task_config.get("device", "cpu")

        publish_task_log(
            task_id, f"[pre-train] Loading model {model_name}...", SERVICE_NAME)
        model = YOLO(model_name)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)

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
        publish_task_log(
            task_id, "[post-train] Uploading model to S3...", SERVICE_NAME)
        s3_config = get_s3_config()
        pt_name = f"{uuid.uuid4()}.pt"
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息（让主服务写入数据库）
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "base_model_name": model_name,
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": "detection",
        }
        publish_model_registered(task_id, model_info, SERVICE_NAME)

        # 更新任务状态为完成
        publish_task_status(task_id, TaskStatus.COMPLETED,
                            SERVICE_NAME, f"Model saved to {pt_name}")
        publish_task_log(
            task_id, f"[post-train] Training completed. Model: {pt_name}", SERVICE_NAME)

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
    dataset_path: str,
    annotation_path: str,
    task_config: Dict[str, Any],
):
    """内部函数：训练分类模型"""
    temp_folder = None
    train_dir = None

    try:
        # 更新任务状态为进行中
        publish_task_status(task_id, TaskStatus.RUNNING,
                            SERVICE_NAME, "Starting classification training")
        publish_task_log(
            task_id, "[pre-train] Starting classification model training...", SERVICE_NAME)

        # 下载数据集
        publish_task_log(
            task_id, "[pre-train] Downloading dataset from S3...", SERVICE_NAME)
        temp_folder = download_dataset_from_s3(dataset_path, annotation_path)

        if not temp_folder:
            raise ValueError("Failed to download dataset")

        # 加载类别信息
        classes_json_path = os.path.join(
            temp_folder, "annotations", "classes.json")
        if not os.path.exists(classes_json_path):
            raise FileNotFoundError("classes.json not found")

        with open(classes_json_path, "r") as f:
            class_info = json.load(f)

        # 准备训练数据
        publish_task_log(
            task_id, "[pre-train] Preparing training dataset...", SERVICE_NAME)
        train_dir = prepare_classification_dataset(
            all_images_dir=os.path.join(temp_folder, "dataset"),
            class_info=class_info,
        )

        # 创建回调
        callback = TrainingCallback(task_id)

        # 加载模型并开始训练
        model_name = task_config.get("name", "yolo11n-cls.pt")
        epochs = task_config.get("epoch", 10)
        imgsz = task_config.get("size", 640)
        batch = task_config.get("batch", 8)
        device = task_config.get("device", "cpu")

        publish_task_log(
            task_id, f"[pre-train] Loading model {model_name}...", SERVICE_NAME)
        model = YOLO(model_name)

        # 添加回调
        model.add_callback("on_train_epoch_end", callback.on_train_epoch_end)
        model.add_callback("on_train_end", callback.on_train_end)

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
        publish_task_log(
            task_id, "[post-train] Uploading model to S3...", SERVICE_NAME)
        s3_config = get_s3_config()
        pt_name = f"{uuid.uuid4()}.pt"
        upload_to_s3(best_pt_path, pt_name, s3_config.models_bucket_name)

        # 通过 MQ 发送模型注册消息
        model_info = {
            "dataset_id": task_config.get("dataset_id"),
            "annotation_id": task_config.get("annotation_id"),
            "save_path": pt_name,
            "base_model_name": model_name,
            "loss": float(model.trainer.loss) if hasattr(model.trainer, 'loss') else 0.0,
            "epoch": epochs,
            "model_type": "classification",
        }
        publish_model_registered(task_id, model_info, SERVICE_NAME)

        # 更新任务状态为完成
        publish_task_status(task_id, TaskStatus.COMPLETED,
                            SERVICE_NAME, f"Model saved to {pt_name}")
        publish_task_log(
            task_id, f"[post-train] Training completed. Model: {pt_name}", SERVICE_NAME)

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


def train_detection(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    classes: List[str],
    task_config: Dict[str, Any],
):
    """启动目标检测模型训练（异步）"""
    thread = threading.Thread(
        target=_train_detection_model,
        kwargs={
            "task_id": task_id,
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
            "classes": classes,
            "task_config": task_config,
        },
        daemon=True,
    )
    thread.start()
    return thread


def train_classification(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
    task_config: Dict[str, Any],
):
    """启动分类模型训练（异步）"""
    thread = threading.Thread(
        target=_train_classification_model,
        kwargs={
            "task_id": task_id,
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
            "task_config": task_config,
        },
        daemon=True,
    )
    thread.start()
    return thread
