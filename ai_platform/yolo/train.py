import os
import shutil
from typing import List

from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from base.nacos_config import get_sync_db
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from yolo.prepare_dataset import prepare_temp_training_dir_split


def __train_model(
    task_id: int, dataset_path: str, annotation_path: str, classes: List[str]
):
    session = get_sync_db()
    p: str = prepare_temp_training_dir_split(
        all_images_dir=dataset_path,
        all_labels_dir=annotation_path,
        class_names=classes,
    )

    tlc = TaskLogCreate(
        task_id=task_id, log_content="copying dataset and annotation to temp folder ..."
    )
    create_log(session, tlc)

    def on_train_epoch_end(trainer: BaseTrainer):
        """每个epoch结束时触发"""

        task_info = {
            "type": "epoch",
            "epoch": trainer.epoch,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss),
            "mAP": trainer.metrics.get("mAP50-95", 0.0),
        }

        tlc = TaskLogCreate(task_id=task_id, log_content=str(task_info))
        create_log(session, tlc)

    def on_train_end(trainer: BaseTrainer):
        """训练结束"""
        global train_context
        save_dir = str(trainer.save_dir.absolute())
        print(f"save_dir  {save_dir}")
        tlc = TaskLogCreate(
            task_id=task_id, log_content=f"task end, model saved to {save_dir}/weights/"
        )
        create_log(session, tlc)

    try:
        model = YOLO("yolo11n.pt")  # 加载 YOLO 模型
        model.add_callback("on_train_epoch_end", on_train_epoch_end)
        model.add_callback("on_train_end", on_train_end)
        model.train(
            data=p + os.sep + "data.yaml",
            epochs=2,
            imgsz=640,
            batch=5,
            device="cpu",
        )
    except Exception as e:
        print(e)
    finally:
        session.close()
        shutil.rmtree(p)


def train(
    task_id: int,
    model_name: str = "yolo11n.pt",
    epochs: int = 5,
    imgsz: int = 640,
    batch_size: int = 5,
    classes: List[str] = [],
    dataset_path: str = "",
    annotation_path: str = "",
):
    if len(classes) == 0:
        return
    if dataset_path == "":
        return
    if annotation_path == "":
        return
    # task: Task = Task(task_id=task_id, status="running")
    # DB.task_box.put(task)
    import threading

    threading.Thread(
        target=__train_model,
        kwargs={
            "task_id": task_id,
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
            "classes": classes,
            # "data": "coco8.yaml",
            # "epochs": 10,
            # "imgsz": 640,
            # "device": "cpu",
        },
        daemon=True,
    ).start()
