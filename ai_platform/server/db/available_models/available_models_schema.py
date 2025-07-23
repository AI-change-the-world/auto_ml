from datetime import datetime

from pydantic import BaseModel


class AvailableModelOut(BaseModel):
    available_model_id: int
    save_path: str
    base_model_name: str
    loss: float
    epoch: int
    dataset_id: int
    annotation_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
