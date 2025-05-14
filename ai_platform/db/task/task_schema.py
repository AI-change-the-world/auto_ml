from datetime import datetime

from pydantic import BaseModel


class TaskOut(BaseModel):
    task_id: int
    task_type: str
    dataset_id: int
    annotation_id: int
    created_at: datetime
    updated_at: datetime
    status: int

    class Config:
        from_attributes = True
