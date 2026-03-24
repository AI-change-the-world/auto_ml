"""
统一响应格式
"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    success: bool = True
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def ok(cls, data: T = None, message: str = "success") -> "Result[T]":
        """成功响应"""
        return cls(success=True, code=200, message=message, data=data)
    
    @classmethod
    def fail(cls, code: int = 500, message: str = "error", data: T = None) -> "Result[T]":
        """失败响应"""
        return cls(success=False, code=code, message=message, data=data)
    
    @classmethod
    def not_found(cls, message: str = "Resource not found") -> "Result[None]":
        """404 响应"""
        return cls(success=False, code=404, message=message)
    
    @classmethod
    def bad_request(cls, message: str = "Bad request") -> "Result[None]":
        """400 响应"""
        return cls(success=False, code=400, message=message)


class PageResult(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    pages: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PageResult[T]":
        """创建分页结果"""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
