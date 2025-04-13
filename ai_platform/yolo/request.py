from pydantic import BaseModel, Field
from typing import Optional


class YOLORequest(BaseModel):
    task: str = Field(
        ..., pattern="^(train|predict)$", description="Task type: 'train' or 'predict'"
    )
    model: str = Field(..., description="Model name, e.g., 'yolo_v3'")
    device: str = Field(
        default="cpu",
        description="Device identifier, e.g., '0', 'cpu', or '0,1'",
    )
    size: int = Field(default=640, gt=0, description="Input size for the model")
    epoch: Optional[int] = Field(
        None, ge=1, description="Number of training epochs, can be null"
    )
    config: Optional[str] = Field(None, description="Path to the YOLO config file")
    weights: Optional[str] = Field(None, description="Path to the pre-trained weights")
    files: Optional[list[str]] = Field(None, description="List of image files")
