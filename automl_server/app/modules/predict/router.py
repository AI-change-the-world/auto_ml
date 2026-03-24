"""预测模块 - 含 SSE 支持"""
import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.common import Result, PageResult
from app.config.database import get_db, AsyncSessionLocal
from app.db.models import PredictTask, PredictData
from app.utils.http_client import HttpClient

router = APIRouter(prefix="/predict", tags=["预测"])


class PredictRequest(BaseModel):
    source: str
    model_id: int
    task_type: str = "image"


class PredictTaskResponse(BaseModel):
    id: int
    task_type: Optional[str]
    source: Optional[str]
    result: Optional[str]
    status: int
    model_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/image", response_model=Result, summary="图像预测")
async def predict_image(
    data: PredictRequest,
    db: AsyncSession = Depends(get_db),
):
    """图像预测"""
    # 创建预测任务
    task = PredictTask(
        task_type=data.task_type,
        source=data.source,
        model_id=data.model_id,
        status=0,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    
    # TODO: 调用部署的模型进行推理
    
    return Result.ok({"task_id": task.id}, "Prediction task created")


@router.get("/video", summary="视频处理（SSE）")
async def predict_video_sse(
    source: str = Query(...),
    model_id: int = Query(...),
):
    """视频处理 - 使用 SSE 推送进度"""
    
    async def event_generator():
        try:
            yield f"data: {json.dumps({'status': 'started', 'progress': 0})}\n\n"
            
            # 模拟处理进度
            for i in range(1, 101):
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'status': 'processing', 'progress': i})}\n\n"
            
            yield f"data: {json.dumps({'status': 'completed', 'progress': 100, 'result': 'ok'})}\n\n"
            
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/list", response_model=Result[PageResult[PredictTaskResponse]], summary="预测任务列表")
async def list_predict_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = [PredictTask.is_deleted == False]
    count_stmt = select(func.count()).select_from(PredictTask).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()
    
    offset = (page - 1) * page_size
    stmt = select(PredictTask).where(*conditions).order_by(PredictTask.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    items = [PredictTaskResponse.model_validate(t) for t in result.scalars().all()]
    
    return Result.ok(PageResult.create(items, total, page, page_size))


@router.get("/{task_id}/result", response_model=Result, summary="获取预测结果")
async def get_predict_result(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PredictTask).where(PredictTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        return Result.not_found("Predict task not found")
    
    return Result.ok({
        "task_id": task.id,
        "status": task.status,
        "result": task.result,
    })
