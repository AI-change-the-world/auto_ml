from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskLogCreate(BaseModel):
    task_id: int
    log_content: Optional[str] = None
    created_at: datetime = datetime.now()


class TaskLogOut(BaseModel):
    task_id: int
    log_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
