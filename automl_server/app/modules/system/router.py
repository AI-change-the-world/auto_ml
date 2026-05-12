"""系统能力 API"""
from fastapi import APIRouter, Depends

from app.common import Result

from .schemas import CapabilitySnapshotResponse
from .service import (
    SystemCapabilityService,
    get_system_capability_service,
)


router = APIRouter(prefix="/system", tags=["系统能力"])


@router.get(
    "/capabilities",
    response_model=Result[CapabilitySnapshotResponse],
    summary="获取系统能力快照",
)
async def get_capabilities(
    service: SystemCapabilityService = Depends(get_system_capability_service),
):
    snapshot = await service.get_capability_snapshot()
    return Result.ok(snapshot)
