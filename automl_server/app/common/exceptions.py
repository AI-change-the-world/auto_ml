"""
自定义异常
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常"""
    
    def __init__(
        self,
        code: int = 500,
        message: str = "Internal Server Error",
        data: Any = None
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源未找到"""
    
    def __init__(self, message: str = "Resource not found", data: Any = None):
        super().__init__(code=404, message=message, data=data)


class BadRequestException(AppException):
    """请求错误"""
    
    def __init__(self, message: str = "Bad request", data: Any = None):
        super().__init__(code=400, message=message, data=data)


class UnauthorizedException(AppException):
    """未授权"""
    
    def __init__(self, message: str = "Unauthorized", data: Any = None):
        super().__init__(code=401, message=message, data=data)


class ForbiddenException(AppException):
    """禁止访问"""
    
    def __init__(self, message: str = "Forbidden", data: Any = None):
        super().__init__(code=403, message=message, data=data)
