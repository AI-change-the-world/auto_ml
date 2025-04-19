from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from base import create_response
from base.deprecated import deprecated
from base.nacos_config import get_db
from yolo.request import TrainRequest, YOLORequest

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"],
)


class YOLONewTrainTaskResponse(BaseModel):
    task_id: str


class YoloTrainLogs(BaseModel):
    logs: list[str]


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
        dataset_path=dataset.url,
        annotation_path=annotation.annotation_path,
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
