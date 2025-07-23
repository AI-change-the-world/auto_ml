from typing import List

from pydantic import BaseModel


class LabelModel(BaseModel):
    label: str
    x_center: float
    y_center: float
    width: float
    height: float
    confidence: float = 0.0


class ImageModel(BaseModel):
    # image_path: str
    labels: List[LabelModel]
