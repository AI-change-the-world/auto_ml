from typing import List

from pydantic import BaseModel
from supervision import Detections


# 定义 Box 模型
class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    def __str__(self):
        return f"x1: {self.x1}, y1: {self.y1}, x2: {self.x2}, y2: {self.y2}"


# 定义主模型
class PredictResult(BaseModel):
    name: str
    obj_class: int
    confidence: float
    box: Box

    def __str__(self):
        return f"name: {self.name}, obj_class: {self.obj_class}, confidence: {self.confidence}, box: {self.box}"

    @classmethod
    def from_dict(cls, data):
        new_dict: dict = {}
        for key, value in data.items():
            if key == "class":
                # new_dict[key] = Box(**value)
                new_dict["obj_class"] = value
            else:
                new_dict[key] = value
        return cls(**new_dict)


class RunningModelsResponse(BaseModel):
    running_models: List[int] = []


def predict_result_from_detections(detections: Detections) -> List[PredictResult]:
    results = []
    for detection in detections:
        results.append(
            PredictResult(
                name=detection[5]["class_name"],
                obj_class=detection[3],
                confidence=detection[2],
                box=Box(
                    x1=detection[0][0],
                    y1=detection[0][1],
                    x2=detection[0][2],
                    y2=detection[0][3],
                ),
            )
        )
    return results


class ClsPredictResults(BaseModel):
    image_id: str
    class_id: int
    name: str
    confidence: float


class PredictResults(BaseModel):
    image_id: str
    results: list[PredictResult]
    image_width: int
    image_height: int

    def __str__(self):
        return str(self.results)

    @classmethod
    def from_data(cls, data: list, img: str, image_width: int, image_height: int):
        p: PredictResults = PredictResults(
            image_id=img, results=[], image_width=image_width, image_height=image_height
        )
        for r in data:
            p.results.append(PredictResult.from_dict(r))

        return p
