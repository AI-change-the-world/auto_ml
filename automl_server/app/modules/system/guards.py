"""系统 capability 守卫"""
from collections.abc import Awaitable, Callable

from fastapi import Depends

from app.common.exceptions import AppException

from .service import SystemCapabilityService, get_system_capability_service


def require_capability(module_key: str, action_key: str):
    """FastAPI dependency factory，用于在路由层校验系统 capability。

    后续接入用户权限时，可以在这里继续叠加 authz 校验，扩成统一 access guard。
    """

    async def _guard(
        service: SystemCapabilityService = Depends(get_system_capability_service),
    ) -> None:
        snapshot = await service.get_capability_snapshot()
        module_state = snapshot.modules.get(module_key)
        action_state = module_state.actions.get(action_key) if module_state else None

        if action_state and action_state.allowed:
            return

        reason = (
            (action_state.reason if action_state else None)
            or (module_state.reason if module_state else None)
            or f"{module_key}.{action_key} is unavailable"
        )
        raise AppException(
            code=503,
            error_code="CAPABILITY_UNAVAILABLE",
            message=reason,
            detail={
                "module": module_key,
                "action": action_key,
            },
        )

    return _guard
