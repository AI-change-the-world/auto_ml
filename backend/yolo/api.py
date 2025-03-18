from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from yolo.request import YOLORequest

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"],
)


@router.post("/predict")
async def predict(req: YOLORequest):
    from yolo.predict import predict

    return EventSourceResponse(
        predict(model_name=req.model, imgs=req.files), media_type="text/event-stream"
    )
