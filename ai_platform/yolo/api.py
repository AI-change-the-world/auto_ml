from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from base import create_response
from base.deprecated import deprecated
from base.logger import logger
from base.nacos_config import get_db
from yolo.eval_dataset import YoloDatasetAnalyzer
from yolo.request import TrainRequest, YOLORequest
from yolo.response import RunningModelsResponse

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"],
)


class YOLONewTrainTaskResponse(BaseModel):
    task_id: str


class YoloTrainLogs(BaseModel):
    logs: list[str]


class PredictSingleImageRequest(BaseModel):
    data: str
    model_id: int


class EvalDatasetRequest(BaseModel):
    dataset_id: int
    annotation_id: int
    task_id: int


@router.post("/eval/dataset")
def eval_dataset(req: EvalDatasetRequest):
    a = YoloDatasetAnalyzer(
        dataset_id=req.dataset_id, annotation_id=req.annotation_id, task_id=req.task_id
    )
    res = a.analyze()
    logger.info(f"res: {res}")
    return create_response(
        status=200,
        data=None,
        message="OK",
    )


@router.post("/eval")
async def deploy_eval(req: PredictSingleImageRequest, db: Session = Depends(get_db)):
    from yolo.predict import predict_with_certain_model

    return create_response(
        status=200,
        message="OK",
        data=predict_with_certain_model(
            model_id=req.model_id,
            img=req.data,
            db=db,
        ),
    )


@router.get("/start/{id}")
async def start_model(id: int, db: Session = Depends(get_db)):
    from yolo.predict import start_model

    if start_model(id, db) == 0:
        return create_response(
            status=200,
            message="OK",
            data=None,
        )
    else:
        return create_response(
            status=400,
            message="model not found",
            data=None,
        )


@router.get("/stop/{id}")
async def stop_model(id: int):
    from yolo.predict import stop_model

    stop_model(id)
    return create_response(
        status=200,
        message="OK",
        data=None,
    )


@router.get("/models/running")
async def running_models():
    from yolo.predict import get_running_models

    return create_response(
        status=200,
        message="OK",
        data=RunningModelsResponse(running_models=get_running_models()),
    )


## TODO rewrite this function
@router.post("/predict")
async def predict(req: YOLORequest):
    from yolo.predict import predict

    return EventSourceResponse(
        predict(model_name=req.model, imgs=req.files), media_type="text/event-stream"
    )


@router.post("/train")
async def train(req: TrainRequest, db: Session = Depends(get_db)):
    from db.annotation.annotation_crud import get_annotation
    from db.dataset.dataset_crud import get_dataset
    from db.task.task_crud import get_task
    from yolo.train import train

    task = get_task(db, req.task_id)
    dataset = get_dataset(db, task.dataset_id)
    annotation = get_annotation(db, task.annotation_id)

    train(
        task_id=req.task_id,
        dataset_path=dataset.local_s3_storage_path,
        annotation_path=annotation.annotation_save_path,
        classes=annotation.class_items.split(";"),
    )

    return create_response(
        status=200,
        message="OK",
    )


@router.get("/train/status/{uuid}")
@deprecated("train status is deprecated, use java backend instead")
async def train_status(uuid: str):
    # task_logs = DB.task_log_box.query(TaskLog.task_id.equals(uuid)).build().find()
    # logs = YoloTrainLogs(logs=[])
    # for task_log in task_logs:
    #     logs.logs.append(task_log.content)

    return create_response(
        status=200,
        message="OK",
        data=[],
    )
