"""Aether 工作流 API"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime

from app.common import Result, PageResult
from app.config.database import get_db
from app.db.models import Agent

router = APIRouter(prefix="/aether", tags=["Aether 工作流"])


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    pipeline_content: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    pipeline_content: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutePipelineRequest(BaseModel):
    agent_id: int
    input_data: dict = {}


@router.get("/agents", response_model=Result[PageResult[AgentResponse]], summary="获取 Agent 列表")
async def list_agents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Agent.is_deleted == False]
    count_stmt = select(func.count()).select_from(Agent).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    offset = (page - 1) * page_size
    stmt = select(Agent).where(*conditions).order_by(Agent.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = [AgentResponse.model_validate(a) for a in result.scalars().all()]
    
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.post("/agent", response_model=Result[AgentResponse], summary="创建 Agent")
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    agent = Agent(
        name=data.name,
        description=data.description,
        pipeline_content=data.pipeline_content,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    
    return Result.ok(AgentResponse.model_validate(agent), "Agent created")


@router.get("/agent/{agent_id}", response_model=Result[AgentResponse], summary="获取 Agent 详情")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Agent).where(Agent.id == agent_id, Agent.is_deleted == False)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        return Result.not_found("Agent not found")
    
    return Result.ok(AgentResponse.model_validate(agent))


@router.post("/execute", response_model=Result, summary="执行工作流")
async def execute_pipeline(
    data: ExecutePipelineRequest,
    db: AsyncSession = Depends(get_db),
):
    """执行工作流 Pipeline"""
    stmt = select(Agent).where(Agent.id == data.agent_id, Agent.is_deleted == False)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        return Result.not_found("Agent not found")
    
    # TODO: 实现工作流引擎执行逻辑
    # 这里需要解析 pipeline_content 并执行各个步骤
    
    return Result.ok({"status": "submitted", "agent_id": data.agent_id}, "Pipeline execution started")
