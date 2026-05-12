"""
自定义异常
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常"""

    def __init__(
        self,
        code: int = 500,
        error_code: str | None = None,
        message: str = "Internal Server Error",
        data: Any = None,
        detail: Any = None,
    ):
        self.code = code
        self.error_code = error_code or self._default_error_code(code)
        self.message = message
        self.data = data
        self.detail = detail
        super().__init__(self.message)

    @staticmethod
    def _default_error_code(code: int) -> str:
        mapping = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "TOO_MANY_REQUESTS",
            503: "SERVICE_UNAVAILABLE",
        }
        return mapping.get(code, "INTERNAL_ERROR")


class NotFoundException(AppException):
    """资源未找到"""

    def __init__(
        self,
        message: str = "Resource not found",
        data: Any = None,
        detail: Any = None,
        error_code: str = "NOT_FOUND",
    ):
        super().__init__(
            code=404,
            error_code=error_code,
            message=message,
            data=data,
            detail=detail,
        )


class BadRequestException(AppException):
    """请求错误"""

    def __init__(
        self,
        message: str = "Bad request",
        data: Any = None,
        detail: Any = None,
        error_code: str = "BAD_REQUEST",
    ):
        super().__init__(
            code=400,
            error_code=error_code,
            message=message,
            data=data,
            detail=detail,
        )


class UnauthorizedException(AppException):
    """未授权"""

    def __init__(
        self,
        message: str = "Unauthorized",
        data: Any = None,
        detail: Any = None,
        error_code: str = "UNAUTHORIZED",
    ):
        super().__init__(
            code=401,
            error_code=error_code,
            message=message,
            data=data,
            detail=detail,
        )


class ForbiddenException(AppException):
    """禁止访问"""

    def __init__(
        self,
        message: str = "Forbidden",
        data: Any = None,
        detail: Any = None,
        error_code: str = "FORBIDDEN",
    ):
        super().__init__(
            code=403,
            error_code=error_code,
            message=message,
            data=data,
            detail=detail,
        )
