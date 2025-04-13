import json
from typing import List
from ultralytics import YOLO

from yolo.response import PredictResults


def __predict(model: YOLO, img: str) -> PredictResults:
    result = model.predict(img, stream=False)
    if len(result) == 0:
        return PredictResults.from_data([], img)
    return PredictResults.from_data(json.loads(result[0].to_json()), img=img)


async def predict(model_name: str, imgs: List[str]):
    model = YOLO(model_name)

    # 异步生成推理结果
    for item in imgs:
        yield __predict(model, item).model_dump_json()

    yield "[DONE]"
