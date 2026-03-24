"""工具模型 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime

from app.common import Result, PageResult
from app.config.database import get_db
from app.db.models import ToolModel

router = APIRouter(prefix="/tool", tags=["工具模型"])


class ToolModelCreate(BaseModel):
    name: str
    model_type: Optional[str] = None
    endpoint: Optional[str] = None
    config: Optional[str] = None


class ToolModelResponse(BaseModel):
    id: int
    name: str
    model_type: Optional[str]
    endpoint: Optional[str]
    config: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/list", response_model=Result[PageResult[ToolModelResponse]], summary="获取工具模型列表")
async def list_tool_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = [ToolModel.is_deleted == False]
    count_stmt = select(func.count()).select_from(ToolModel).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    offset = (page - 1) * page_size
    stmt = select(ToolModel).where(
        *conditions).order_by(ToolModel.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = [ToolModelResponse.model_validate(
        t) for t in result.scalars().all()]

    return Result.ok(PageResult.create(items, total, page, page_size))


@router.post("/new", response_model=Result[ToolModelResponse], summary="创建工具模型")
async def create_tool_model(
    data: ToolModelCreate,
    db: AsyncSession = Depends(get_db),
):
    model = ToolModel(
        name=data.name,
        model_type=data.model_type,
        endpoint=data.endpoint,
        config=data.config,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)

    return Result.ok(ToolModelResponse.model_validate(model), "Tool model created")
