"""
数据集 Pydantic Schema
"""
from datetime import datetime
from typing import Any, Dict, Optional

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


class AssetResponse(BaseModel):
    """原始资源响应"""
    id: int
    dataset_id: int
    asset_type: str
    file_name: str
    save_path: Optional[str]
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    meta_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SampleItemCreate(BaseModel):
    """创建无文件样本请求"""
    item_type: str = Field(..., min_length=1, max_length=32)
    item_key: str = Field(..., min_length=1, max_length=255)
    locator: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None


class SampleItemUpdate(BaseModel):
    item_key: Optional[str] = Field(default=None, min_length=1, max_length=255)
    locator: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None


class SampleItemResponse(BaseModel):
    """数据集样本响应"""
    id: int
    dataset_id: int
    asset_id: Optional[int]
    item_type: str
    item_key: str
    locator: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
    asset: Optional[AssetResponse] = None


class FilePreviewResponse(BaseModel):
    """文件预览响应"""
    file_name: str
    presigned_url: str


class FileContentResponse(BaseModel):
    """文本文件内容响应"""
    file_name: str
    content: str


class PreferenceImportResponse(BaseModel):
    """DPO 偏好样本导入结果"""
    imported: int

