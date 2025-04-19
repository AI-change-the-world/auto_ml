from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnnotationOut(BaseModel):
    id: int
    dataset_id: Optional[int]
    annotation_type: Optional[int]
    updated_at: Optional[datetime]
    is_deleted: Optional[int]
    created_at: Optional[datetime]
    class_items: Optional[str]
    annotation_path: Optional[str]
    storage_type: Optional[int]

    class Config:
        orm_mode = True
