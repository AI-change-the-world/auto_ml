from datetime import datetime

from pydantic import BaseModel


class ToolModelOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    type: int
    is_embedded: int
    created_at: datetime
    updated_at: datetime
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    model_save_path: str | None = None

    class Config:
        from_attributes = True
