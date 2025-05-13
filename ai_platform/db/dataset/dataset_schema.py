from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: int
    name: Optional[str]
    description: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    type: Optional[int]
    ranking: Optional[float]
    storage_type: Optional[int]
    url: Optional[str]
    username: Optional[str]
    password: Optional[str]
    scan_status: Optional[int]
    file_count: Optional[int]
    sample_file_path: Optional[str]

    class Config:
        from_attributes = True
