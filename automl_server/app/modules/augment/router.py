"""数据增强 API"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.common import Result
from app.utils.http_client import HttpClient

router = APIRouter(prefix="/augment", tags=["数据增强"])


class AugmentRequest(BaseModel):
    dataset_id: int
    augment_type: str  # cv, gan, sd
    config: Optional[dict] = None


@router.get("/capabilities", response_model=Result, summary="获取增强能力列表")
async def get_capabilities():
    """获取可用的增强能力"""
    capabilities = [
        {"id": "cv", "name": "传统CV增强", "description": "旋转、翻转、裁剪、颜色变换等"},
        {"id": "gan", "name": "GAN增强", "description": "使用GAN生成增强图像"},
        {"id": "sd", "name": "Stable Diffusion", "description": "使用SD进行图像编辑和生成"},
    ]
    return Result.ok(capabilities)


@router.post("/process", response_model=Result, summary="执行数据增强")
async def process_augment(data: AugmentRequest):
    """执行数据增强"""
    # TODO: 调用 auto_augment_pipeline 服务
    # http_client = HttpClient(base_url="http://auto-augment:45682")
    
    return Result.ok({
        "status": "submitted",
        "dataset_id": data.dataset_id,
        "augment_type": data.augment_type,
    }, "Augment task submitted")
