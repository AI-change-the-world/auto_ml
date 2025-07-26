from typing import Optional

from pydantic import BaseModel


class Response(BaseModel):
    status: int
    message: str
    data: Optional[dict] = None


def create_response(status: int, message: str, data: Optional[BaseModel] = None):
    return Response(
        status=status, message=message, data=data.model_dump() if data else None
    )
