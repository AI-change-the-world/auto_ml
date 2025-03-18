from fastapi import APIRouter
from pydantic import BaseModel
from utils.yolo_model import YOLOModel
from base import create_response


class VRAMUsageRequest(BaseModel):
    model_name: str
    batch_size: int


class VRAMUsageModel(BaseModel):
    total_memory: float


router = APIRouter(
    prefix="/utils",
    tags=["utils"],
)

YOLO_MODELS = [
    YOLOModel("YOLOv3", 62, 106, 1024, (416, 416)),
    YOLOModel("YOLOv4", 64, 137, 1024, (416, 416)),
    YOLOModel("YOLOv5s", 7.0, 140, 512, (640, 640)),
    YOLOModel("YOLOv5m", 21.2, 280, 768, (640, 640)),
    YOLOModel("YOLOv5l", 46.5, 420, 1024, (640, 640)),
    YOLOModel("YOLOv5x", 86.7, 560, 1280, (640, 640)),
    YOLOModel("YOLOv6s", 18.3, 230, 768, (640, 640)),
    YOLOModel("YOLOv6m", 34.3, 280, 1024, (640, 640)),
    YOLOModel("YOLOv6l", 58.6, 330, 1280, (640, 640)),
    YOLOModel("YOLOv7", 36.9, 314, 1024, (640, 640)),
    YOLOModel("YOLOv8n", 3.2, 90, 256, (640, 640)),
    YOLOModel("YOLOv8s", 11.2, 160, 512, (640, 640)),
    YOLOModel("YOLOv8m", 25.9, 240, 768, (640, 640)),
    YOLOModel("YOLOv8l", 43.7, 320, 1024, (640, 640)),
    YOLOModel("YOLOv8x", 68.2, 400, 1280, (640, 640)),
]


@router.post("/vram_usage")
async def vram_usage(req: VRAMUsageRequest):
    match req.model_name:
        case "YOLOv3":
            model = YOLO_MODELS[0]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv4":
            model = YOLO_MODELS[1]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv5s":
            model = YOLO_MODELS[2]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv5m":
            model = YOLO_MODELS[3]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv5l":
            model = YOLO_MODELS[4]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv5x":
            model = YOLO_MODELS[5]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv6s":
            model = YOLO_MODELS[6]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv6m":
            model = YOLO_MODELS[7]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv6l":
            model = YOLO_MODELS[8]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv7":
            model = YOLO_MODELS[9]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv8n":
            model = YOLO_MODELS[10]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv8s":
            model = YOLO_MODELS[11]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv8m":
            model = YOLO_MODELS[12]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv8l":
            model = YOLO_MODELS[13]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
        case "YOLOv8x":
            model = YOLO_MODELS[14]
            return create_response(
                status=200,
                message="OK",
                data=VRAMUsageModel(total_memory= model.estimate_vram(batch_size=req.batch_size)),
            )
    return create_response(status=400, message="Model not found")
