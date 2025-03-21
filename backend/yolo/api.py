from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from base import create_response
from yolo.request import YOLORequest
import uuid

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"],
)


class YOLONewTrainTaskResponse(BaseModel):
    task_id: str


class YoloTrainLogs(BaseModel):
    logs: list[str]


@router.post("/predict")
async def predict(req: YOLORequest):
    from yolo.predict import predict

    return EventSourceResponse(
        predict(model_name=req.model, imgs=req.files), media_type="text/event-stream"
    )


@router.post("/train")
async def train(req: YOLORequest):
    y: YOLONewTrainTaskResponse = YOLONewTrainTaskResponse(task_id=str(uuid.uuid4()))
    from yolo.train import train

    train(task_id=y.task_id, model_name=req.model, epochs=req.epoch, imgsz=req.size)

    return create_response(
        status=200,
        message="OK",
        data=y,
    )


@router.get("/train/status/{uuid}")
async def train_status(uuid: str):
    from db.task_log import TaskLog
    from db import DB

    task_logs = DB.task_log_box.query(TaskLog.task_id == uuid).build().find()
    logs = YoloTrainLogs(logs=[])
    for task_log in task_logs:
        logs.logs.append(task_log.content)

    return create_response(
        status=200,
        message="OK",
        data=logs,
    )
