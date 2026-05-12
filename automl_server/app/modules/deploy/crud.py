"""部署 CRUD"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AvailableModel, ModelInferenceLog


async def get_available_models(db: AsyncSession, offset: int = 0, limit: int = 10, deployed_only: bool = None) -> tuple[List[AvailableModel], int]:
    conditions = [AvailableModel.is_deleted == False]
    if deployed_only is not None:
        conditions.append(AvailableModel.is_deployed == deployed_only)

    count_stmt = select(func.count()).select_from(
        AvailableModel).where(*conditions)
    total = (await db.execute(count_stmt)).scalar()

    stmt = select(AvailableModel).where(
        *conditions).order_by(AvailableModel.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_model_by_id(db: AsyncSession, model_id: int) -> Optional[AvailableModel]:
    stmt = select(AvailableModel).where(AvailableModel.id ==
                                        model_id, AvailableModel.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_model_name(
    db: AsyncSession,
    model: AvailableModel,
    name: str,
) -> AvailableModel:
    model.name = name
    await db.commit()
    await db.refresh(model)
    return model


async def create_uploaded_onnx_model(
    db: AsyncSession,
    *,
    name: str,
    onnx_model_path: str,
    model_type: str,
    runtime_template: str,
    class_names: str | None,
    onnx_input_signature: str | None,
    onnx_output_signature: str | None,
) -> AvailableModel:
    model = AvailableModel(
        name=name,
        onnx_model_path=onnx_model_path,
        model_type=model_type,
        runtime_template=runtime_template,
        class_names=class_names,
        onnx_input_signature=onnx_input_signature,
        onnx_output_signature=onnx_output_signature,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


async def update_model_deployment_state(
    db: AsyncSession,
    model: AvailableModel,
    *,
    is_deployed: bool,
    deployment_id: str | int | None = None,
    deployment_port: int | None = None,
    deployment_version: str | None = None,
    deployment_device: str | None = None,
    deployed_at: datetime | None = None,
) -> AvailableModel:
    model.is_deployed = is_deployed
    model.deployment_id = str(deployment_id) if deployment_id not in (None, "") else None
    model.deployment_port = deployment_port
    model.deployment_version = deployment_version
    model.deployment_device = deployment_device
    if deployed_at is not None or is_deployed:
        model.deployed_at = deployed_at or datetime.now()
    await db.commit()
    await db.refresh(model)
    return model


async def mark_model_inference(db: AsyncSession, model_id: int) -> None:
    stmt = (
        update(AvailableModel)
        .where(AvailableModel.id == model_id)
        .where(AvailableModel.is_deleted == False)
        .values(
            inference_count=func.coalesce(AvailableModel.inference_count, 0) + 1,
            last_inference_at=datetime.now(),
        )
    )
    await db.execute(stmt)


async def create_inference_log(
    db: AsyncSession,
    *,
    model_id: int,
    request_type: str | None,
    success: bool,
    duration_ms: int | None,
    result_count: int,
    image_width: int | None,
    image_height: int | None,
    error_message: str | None,
    client_ip: str | None,
) -> ModelInferenceLog:
    log = ModelInferenceLog(
        model_id=model_id,
        request_type=request_type,
        success=success,
        duration_ms=duration_ms,
        result_count=result_count,
        image_width=image_width,
        image_height=image_height,
        error_message=error_message,
        client_ip=client_ip,
    )
    db.add(log)
    await db.flush()
    return log


async def list_inference_logs(
    db: AsyncSession,
    model_id: int,
    offset: int = 0,
    limit: int = 20,
) -> tuple[List[ModelInferenceLog], int]:
    conditions = [
        ModelInferenceLog.model_id == model_id,
        ModelInferenceLog.is_deleted == False,
    ]
    count_stmt = select(func.count()).select_from(ModelInferenceLog).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(ModelInferenceLog)
        .where(*conditions)
        .order_by(ModelInferenceLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total
