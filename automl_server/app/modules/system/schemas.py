"""系统能力响应模型"""
from typing import Dict, Optional

from pydantic import BaseModel


class CapabilityActionState(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class CapabilityModuleState(BaseModel):
    available: bool
    reason: Optional[str] = None
    actions: Dict[str, CapabilityActionState]


class CapabilityServiceHealth(BaseModel):
    key: str
    label: str
    available: bool
    reason: Optional[str] = None
    raw_status: Optional[str] = None


class CapabilitySnapshotResponse(BaseModel):
    modules: Dict[str, CapabilityModuleState]
    services: Dict[str, CapabilityServiceHealth]
    version: int = 0
    updated_at: Optional[str] = None
