"""工作台智能助手 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import Result
from app.common.sse import create_sse_response
from app.config.database import get_db

from .schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantConfigResponse,
    AssistantConfigUpdate,
)
from .service import AssistantService, get_assistant_service


router = APIRouter(prefix="/assistant", tags=["智能助手"])


@router.get("/config", response_model=Result[AssistantConfigResponse], summary="获取智能助手配置")
async def get_config(
    db: AsyncSession = Depends(get_db),
    service: AssistantService = Depends(get_assistant_service),
):
    return Result.ok(await service.get_config(db))


@router.put("/config", response_model=Result[AssistantConfigResponse], summary="保存智能助手配置")
async def update_config(
    data: AssistantConfigUpdate,
    db: AsyncSession = Depends(get_db),
    service: AssistantService = Depends(get_assistant_service),
):
    return Result.ok(await service.update_config(db, data), "Assistant configuration saved")


@router.post("/chat", response_model=Result[AssistantChatResponse], summary="向智能助手提问")
async def chat(
    data: AssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    service: AssistantService = Depends(get_assistant_service),
):
    return Result.ok(await service.chat(db, data))


@router.post("/chat/stream", summary="流式向智能助手提问")
async def stream_chat(
    data: AssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    service: AssistantService = Depends(get_assistant_service),
):
    return create_sse_response(service.stream_chat(db, data))
