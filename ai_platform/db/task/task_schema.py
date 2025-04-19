from datetime import datetime

from pydantic import BaseModel


class TaskOut(BaseModel):
    task_id: int
    task_type: int
    dataset_id: int
    annotation_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
