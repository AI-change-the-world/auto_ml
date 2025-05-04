import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

import opendal
from sqlalchemy.orm import Session
from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from base.file_delegate import get_operator, s3_properties
from base.nacos_config import get_sync_db
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from yolo.prepare_dataset import prepare_temp_training_dir_split


def __download_from_s3(op: opendal.Operator, s3_path: str, local_path: str):
    data = op.read(s3_path)
    with open(local_path, "wb") as f:
        f.write(data)


def __download_dataset_from_s3(
    task_id: int, session: Session, dataset_path: str, annotation_path: str
) -> Optional[str]:
    op = get_operator(s3_properties.datasets_bucket_name)
    if op is None:
        return None
    if dataset_path == "" or annotation_path == "":
        return None
    # 创建临时的工作空间
    folder_name = str(uuid.uuid4())
    tlc = TaskLogCreate(task_id=task_id, log_content="create temp folder ...")
    create_log(session, tlc)

    os.mkdir(f"./runs/{folder_name}")
    temp_dataset_path = f"./runs/{folder_name}" + os.sep + "dataset"
    temp_annotation_path = f"./runs/{folder_name}" + os.sep + "annotations"
    os.mkdir(temp_dataset_path)
    os.mkdir(temp_annotation_path)

    tlc = TaskLogCreate(task_id=task_id, log_content="downloading dataset from s3 ...")
    create_log(session, tlc)

    for i in op.list(dataset_path):
        if Path(i.path).suffix != "":
            print(i.path)
            file_name = i.path.split("/")[-1]
            __download_from_s3(op, i.path, temp_dataset_path + os.sep + file_name)

    tlc = TaskLogCreate(
        task_id=task_id, log_content="downloading annotation from s3 ..."
    )
    create_log(session, tlc)

    for i in op.list(annotation_path):
        if Path(i.path).suffix != "":
            file_name = i.path.split("/")[-1]
            __download_from_s3(op, i.path, temp_annotation_path + os.sep + file_name)

    return f"./runs/{folder_name}"


def __train_model(
    task_id: int, dataset_path: str, annotation_path: str, classes: List[str]
):
    session = get_sync_db()

    temp_folder = __download_dataset_from_s3(
        task_id=task_id,
        session=session,
        dataset_path=dataset_path,
        annotation_path=annotation_path,
    )


    p: str = prepare_temp_training_dir_split(
        all_images_dir=temp_folder + os.sep + "dataset",
        all_labels_dir=temp_folder + os.sep + "annotations",
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
        shutil.rmtree(temp_folder)


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
    if dataset_path == "" or dataset_path is None:
        return
    if annotation_path == "" or annotation_path is None:
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
