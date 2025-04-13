import json
from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer
from db import DB
from db.task_log import TaskLog
from db.task import Task
from objectbox.condition import QueryCondition


def __train_model(task_id: str):
    def on_train_epoch_end(trainer: BaseTrainer):
        """每个epoch结束时触发"""

        task_info = {
            "type": "epoch",
            "epoch": trainer.epoch,
            # 'loss': trainer.loss,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss),
            "mAP": trainer.metrics.get("mAP50-95", 0.0),
        }
        tl: TaskLog = TaskLog(task_id=task_id, content=json.dumps(task_info))
        DB.task_log_box.put(tl)

    model = YOLO("yolo11n.pt")  # 加载 YOLO 模型
    model.add_callback("on_train_epoch_end", on_train_epoch_end)  # 监听 epoch 结束
    model.train(
        data="coco8.yaml",
        epochs=1,
    )
    task = DB.task_box.query(Task.task_id.equals(task_id)).build().find()[0]
    task.status = "complete"
    DB.task_box.put(task)


def train(
    task_id: str,
    model_name: str = "yolo11n.pt",
    epochs: int = 5,
    imgsz: int = 640,
    batch_size: int = 5,
):
    task: Task = Task(task_id=task_id, status="running")
    DB.task_box.put(task)
    import threading

    threading.Thread(
        target=__train_model,
        kwargs={
            "task_id": task_id,
            # "data": "coco8.yaml",
            # "epochs": 10,
            # "imgsz": 640,
            # "device": "cpu",
        },
        daemon=True,
    ).start()
