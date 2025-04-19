from typing import List

from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from base.nacos_config import get_sync_db
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from yolo.custom_trainer import MyCustomTrainer


def __train_model(
    task_id: int, dataset_path: str, annotation_path: str, classes: List[str]
):

    session = get_sync_db()

    data_cfg = {
        "train": dataset_path,
        "labels": annotation_path,
        "names": classes,
        "save_dir": "./runs/",
    }

    def on_train_epoch_end(trainer: BaseTrainer):
        """每个epoch结束时触发"""

        task_info = {
            "type": "epoch",
            "epoch": trainer.epoch,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss),
            "mAP": trainer.metrics.get("mAP50-95", 0.0),
        }

        tlc = TaskLogCreate(task_id=task_id, content=str(task_info))
        create_log(session, tlc)
    
    def on_train_end(trainer: BaseTrainer):
        """训练结束"""

    model = YOLO("yolo11n.pt")  # 加载 YOLO 模型
    # model.add_callback("on_train_epoch_end", on_train_epoch_end)  # 监听 epoch 结束
    trainer = MyCustomTrainer(
        overrides={
            "model": "yolo11n.pt",
            "epochs": 1,
            "imgsz": 640,
            "save_dir": "./runs/",
        },
        custom_data=data_cfg,
    )
    trainer.add_callback("on_train_epoch_end", on_train_epoch_end)
    trainer.add_callback("on_train_end", on_train_end)
    trainer.train()


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
