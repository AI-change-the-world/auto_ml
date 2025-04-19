from typing import Optional

from pydantic import BaseModel


class TaskLogCreate(BaseModel):
    task_id: int
    log_content: Optional[str] = None


class TaskLogOut(BaseModel):
    task_id: int
    log_content: Optional[str] = None

    class Config:
        orm_mode = True
