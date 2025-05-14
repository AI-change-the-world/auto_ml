from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

# from pydantic.generics import GenericModel

T = TypeVar("T")


class Input(BaseModel):
    data: str
    data_type: str = Field(..., alias="data_type")


class RequestMeta(BaseModel):
    task_id: Optional[int] = Field(None, alias="task_id")
    sync: bool


class AetherRequest(BaseModel, Generic[T]):
    task: str
    model_id: int = Field(..., alias="model_id")
    input: Input
    meta: RequestMeta
    extra: Optional[T] = None


class ResponseMeta(BaseModel):
    time_cost_ms: int = Field(..., alias="time_cost_ms")
    task_id: Optional[int] = Field(None, alias="task_id")


class AetherResponse(BaseModel, Generic[T]):
    success: bool
    output: Optional[T] = None
    meta: ResponseMeta
    error: Optional[str] = None
