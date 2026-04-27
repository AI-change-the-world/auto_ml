"""
数据集 Pydantic Schema
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============ 请求 Schema ============

class DatasetCreate(BaseModel):
    """创建数据集请求"""
    name: str = Field(..., min_length=1, max_length=255, description="数据集名称")
    storage_type: int = Field(
        default=1, description="存储类型: 0=本地, 1=S3, 2=WebDAV")
    data_type: int = Field(
        default=0, description="数据类型: 0=图像, 1=文本, 2=视频, 3=音频")
    scenario_type: int = Field(
        default=0, description="场景类型: 0=普通, 1=无人机航拍/拼接, 2=LLM对话标注, 3=MLLM对话标注")
    scenario_config: Optional[Dict[str, Any]] = Field(
        default=None, description="场景配置 JSON")
    description: Optional[str] = Field(default=None, description="描述")


class DatasetUpdate(BaseModel):
    """更新数据集请求"""
    name: Optional[str] = Field(default=None, max_length=255)
    scenario_type: Optional[int] = None
    scenario_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


# ============ 响应 Schema ============

class DatasetResponse(BaseModel):
    """数据集响应"""
    id: int
    name: str
    storage_type: int
    data_type: int
    scenario_type: int = 0
    scenario_config: Optional[Dict[str, Any]] = None
    save_path: Optional[str]
    count: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetFileResponse(BaseModel):
    """数据集文件响应"""
    id: int
    dataset_id: int
    file_name: str
    save_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetDetailResponse(DatasetResponse):
    """数据集详情响应（包含文件列表）"""
    files: List[DatasetFileResponse] = []


class FilePreviewResponse(BaseModel):
    """文件预览响应"""
    file_name: str
    presigned_url: str


class FileContentResponse(BaseModel):
    """文本文件内容响应"""
    file_name: str
    content: str


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    file_ids: List[int] = Field(..., min_length=1, description="要删除的文件ID列表")
