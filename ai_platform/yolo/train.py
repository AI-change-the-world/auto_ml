import json
import os
import shutil
import traceback
import uuid
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session
from ultralytics import YOLO
from ultralytics.engine.trainer import BaseTrainer

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from base.nacos_config import get_sync_db
from db.available_models.available_models_crud import create_available_model
from db.task.task_crud import get_task, update_task
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from yolo.prepare_dataset import (
    prepare_dataset_for_cls,
    prepare_temp_training_dir_split,
)
from yolo.tools import download_from_s3


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
    tlc = TaskLogCreate(
        task_id=task_id, log_content="[pre-train] create temp folder ..."
    )
    create_log(session, tlc)

    os.mkdir(f"./runs/{folder_name}")
    temp_dataset_path = f"./runs/{folder_name}" + os.sep + "dataset"
    temp_annotation_path = f"./runs/{folder_name}" + os.sep + "annotations"
    os.mkdir(temp_dataset_path)
    os.mkdir(temp_annotation_path)

    tlc = TaskLogCreate(
        task_id=task_id, log_content="[pre-train] downloading dataset from s3 ..."
    )
    create_log(session, tlc)

    for i in op.list(dataset_path):
        if Path(i.path).suffix != "":
            print(i.path)
            file_name = i.path.split("/")[-1]
            download_from_s3(op, i.path, temp_dataset_path + os.sep + file_name)

    tlc = TaskLogCreate(
        task_id=task_id, log_content="[pre-train] downloading annotation from s3 ..."
    )
    create_log(session, tlc)

    for i in op.list(annotation_path):
        if Path(i.path).suffix != "":
            file_name = i.path.split("/")[-1]
            download_from_s3(op, i.path, temp_annotation_path + os.sep + file_name)

    return f"./runs/{folder_name}"


def __train_cls_model(task_id: int, dataset_path: str, annotation_path: str):
    session = get_sync_db()
    task = get_task(session, task_id)
    task_config = task.task_config
    task_config_json = json.loads(task_config)
    # dataset = get_dataset(session, task.dataset_id)
    # annotation = get_annotation(session, task.annotation_id)

    temp_folder = __download_dataset_from_s3(
        task_id=task_id,
        session=session,
        dataset_path=dataset_path,
        annotation_path=annotation_path,
    )

    logger.info(f"download dataset from s3: {temp_folder}")

    if not os.path.exists(temp_folder + "/annotations/classes.json"):
        logger.error("classes.json not found")

        tlc = TaskLogCreate(
            task_id=task_id,
            log_content="[post-train] error : classes.json not found ...",
        )
        create_log(session, tlc)
        return

    _json = json.load(open(temp_folder + "/annotations/classes.json"))
    p: str = ""
    try:
        p = prepare_dataset_for_cls(temp_folder + os.sep + "dataset", _json)
    except Exception as e:
        traceback.print_exc()
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content="[post-train] error : dataset create failed ...",
        )
        create_log(session, tlc)
        return

    logger.info(f"prepare dataset for cls: {p}")

    tlc = TaskLogCreate(
        task_id=task_id,
        log_content="[pre-train] copying dataset to temp folder ...",
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
        update_task(session, task_id, {"status": 2})
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] train end, model saved to {save_dir}/weights/",
        )
        create_log(session, tlc)
        # upload to s3
        uploader_op = get_operator(s3_properties.models_bucket_name)
        best_pt_path = save_dir + os.sep + "weights" + os.sep + "best.pt"
        pt_name = str(uuid.uuid4()) + ".pt"
        uploader_op.write(pt_name, open(best_pt_path, "rb").read())
        # save to available model
        available_model = {
            "dataset_id": task.dataset_id,
            "annotation_id": task.annotation_id,
            "save_path": pt_name,
            "base_model_name": task_config_json["name"],
            "loss": trainer.loss.item(),
            "epoch": task_config_json["epoch"],
            "model_type": "classification",
        }
        create_available_model(session, available_model)
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] model uploaded to {pt_name}",
        )
        create_log(session, tlc)

        update_task(session, task_id, {"status": 3})

    update_task(session, task_id, {"status": 1})

    try:
        model = YOLO(task_config_json["name"])  # 加载 YOLO 模型
        model.add_callback("on_train_epoch_end", on_train_epoch_end)
        model.add_callback("on_train_end", on_train_end)
        model.train(
            data=p,
            epochs=task_config_json["epoch"],
            imgsz=task_config_json["size"],
            batch=task_config_json["batch"],
            device="cpu",
        )

    except Exception as e:
        print(e)
    finally:
        session.close()
        shutil.rmtree(p)
        shutil.rmtree(temp_folder)
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] delete temp folder and temp folder",
        )
        create_log(session, tlc)


def __train_model(
    task_id: int, dataset_path: str, annotation_path: str, classes: List[str]
):
    session = get_sync_db()

    task = get_task(session, task_id)
    """
    like:

    {"name":"yolo11n.pt","size":640,"batch":5,"epoch":5,"datasetId":5,"annotationId":7}
    """
    task_config = task.task_config
    task_config_json = json.loads(task_config)

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
        task_id=task_id,
        log_content="[pre-train] copying dataset and annotation to temp folder ...",
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
        update_task(session, task_id, {"status": 2})
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] train end, model saved to {save_dir}/weights/",
        )
        create_log(session, tlc)
        # upload to s3
        uploader_op = get_operator(s3_properties.models_bucket_name)
        best_pt_path = save_dir + os.sep + "weights" + os.sep + "best.pt"
        pt_name = str(uuid.uuid4()) + ".pt"
        uploader_op.write(pt_name, open(best_pt_path, "rb").read())
        # save to available model
        available_model = {
            "dataset_id": task.dataset_id,
            "annotation_id": task.annotation_id,
            "save_path": pt_name,
            "base_model_name": task_config_json["name"],
            "loss": trainer.loss.item(),
            "epoch": task_config_json["epoch"],
            "model_type": "detection",
        }
        create_available_model(session, available_model)
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] model uploaded to {pt_name}",
        )
        create_log(session, tlc)

        update_task(session, task_id, {"status": 3})

    update_task(session, task_id, {"status": 1})

    try:
        model = YOLO(task_config_json["name"])  # 加载 YOLO 模型
        model.add_callback("on_train_epoch_end", on_train_epoch_end)
        model.add_callback("on_train_end", on_train_end)
        model.train(
            data=p + os.sep + "data.yaml",
            epochs=task_config_json["epoch"],
            imgsz=task_config_json["size"],
            batch=task_config_json["batch"],
            device="cpu",
        )

    except Exception as e:
        print(e)
    finally:
        session.close()
        shutil.rmtree(p)
        shutil.rmtree(temp_folder)
        tlc = TaskLogCreate(
            task_id=task_id,
            log_content=f"[post-train] delete temp folder and temp folder",
        )
        create_log(session, tlc)


def train(
    task_id: int,
    classes: List[str],
    dataset_path: str,
    annotation_path: str,
):
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


def cls_train(
    task_id: int,
    dataset_path: str,
    annotation_path: str,
):
    import threading

    threading.Thread(
        target=__train_cls_model,
        kwargs={
            "task_id": task_id,
            "dataset_path": dataset_path,
            "annotation_path": annotation_path,
        },
        daemon=True,
    ).start()
