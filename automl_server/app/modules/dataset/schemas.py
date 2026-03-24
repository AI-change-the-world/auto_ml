"""
数据集 Pydantic Schema
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ============ 请求 Schema ============

class DatasetCreate(BaseModel):
    """创建数据集请求"""
    name: str = Field(..., min_length=1, max_length=255, description="数据集名称")
    storage_type: int = Field(
        default=1, description="存储类型: 0=本地, 1=S3, 2=WebDAV")
    data_type: int = Field(
        default=0, description="数据类型: 0=图像, 1=文本, 2=视频, 3=音频")
    description: Optional[str] = Field(default=None, description="描述")


class DatasetUpdate(BaseModel):
    """更新数据集请求"""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None


# ============ 响应 Schema ============

class DatasetResponse(BaseModel):
    """数据集响应"""
    id: int
    name: str
    storage_type: int
    data_type: int
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
