"""AI Pipeline CRUD"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AssistantConfig,
    AiPipelineBinding,
    AiPipelineProviderResource,
    AiPipelineTemplate,
    AiPipelineTemplateVersion,
    AvailableModel,
)


ASSISTANT_CONFIG_KEY = "workbench"


def _dump_json(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _load_json(value):
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


async def list_templates(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 20,
    scene_type: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
):
    conditions = [AiPipelineTemplate.is_deleted == False]
    if scene_type:
        conditions.append(AiPipelineTemplate.scene_type == scene_type)
    if status:
        conditions.append(AiPipelineTemplate.status == status)
    if keyword:
        conditions.append(AiPipelineTemplate.name.ilike(f"%{keyword.strip()}%"))

    count_stmt = select(func.count()).select_from(AiPipelineTemplate).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(AiPipelineTemplate)
        .where(*conditions)
        .order_by(AiPipelineTemplate.updated_at.desc(), AiPipelineTemplate.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def get_template_by_id(db: AsyncSession, template_id: int) -> Optional[AiPipelineTemplate]:
    stmt = select(AiPipelineTemplate).where(
        AiPipelineTemplate.id == template_id,
        AiPipelineTemplate.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_template_by_key(db: AsyncSession, template_key: str) -> Optional[AiPipelineTemplate]:
    stmt = select(AiPipelineTemplate).where(
        AiPipelineTemplate.template_key == template_key,
        AiPipelineTemplate.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_template(db: AsyncSession, **kwargs) -> AiPipelineTemplate:
    item = AiPipelineTemplate(**kwargs)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_template(db: AsyncSession, template: AiPipelineTemplate, **kwargs) -> AiPipelineTemplate:
    for key, value in kwargs.items():
        setattr(template, key, value)
    await db.flush()
    await db.refresh(template)
    return template


async def delete_template(
    db: AsyncSession,
    template: AiPipelineTemplate,
) -> None:
    template.is_deleted = True
    await db.flush()


async def publish_template_version(
    db: AsyncSession,
    *,
    template_id: int,
    version: int,
) -> None:
    stmt = (
        update(AiPipelineTemplateVersion)
        .where(
            AiPipelineTemplateVersion.template_id == template_id,
            AiPipelineTemplateVersion.is_deleted == False,
        )
        .values(is_published=False)
    )
    await db.execute(stmt)

    target_stmt = (
        update(AiPipelineTemplateVersion)
        .where(
            AiPipelineTemplateVersion.template_id == template_id,
            AiPipelineTemplateVersion.version == version,
            AiPipelineTemplateVersion.is_deleted == False,
        )
        .values(is_published=True)
    )
    await db.execute(target_stmt)


async def get_template_version(
    db: AsyncSession,
    *,
    template_id: int,
    version: Optional[int] = None,
) -> Optional[AiPipelineTemplateVersion]:
    stmt = select(AiPipelineTemplateVersion).where(
        AiPipelineTemplateVersion.template_id == template_id,
        AiPipelineTemplateVersion.is_deleted == False,
    )
    if version is not None:
        stmt = stmt.where(AiPipelineTemplateVersion.version == version)
    else:
        stmt = stmt.order_by(AiPipelineTemplateVersion.version.desc())
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


async def create_template_version(db: AsyncSession, **kwargs) -> AiPipelineTemplateVersion:
    payload = dict(kwargs)
    payload["definition_json"] = _dump_json(payload.get("definition_json"))
    payload["form_schema_json"] = _dump_json(payload.get("form_schema_json"))
    item = AiPipelineTemplateVersion(**payload)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_template_version(
    db: AsyncSession,
    version: AiPipelineTemplateVersion,
    **kwargs,
) -> AiPipelineTemplateVersion:
    payload = dict(kwargs)
    if "definition_json" in payload:
        payload["definition_json"] = _dump_json(payload.get("definition_json"))
    if "form_schema_json" in payload:
        payload["form_schema_json"] = _dump_json(payload.get("form_schema_json"))
    for key, value in payload.items():
        setattr(version, key, value)
    await db.flush()
    await db.refresh(version)
    return version


async def list_template_versions(
    db: AsyncSession,
    *,
    template_id: int,
) -> list[AiPipelineTemplateVersion]:
    stmt = (
        select(AiPipelineTemplateVersion)
        .where(
            AiPipelineTemplateVersion.template_id == template_id,
            AiPipelineTemplateVersion.is_deleted == False,
        )
        .order_by(AiPipelineTemplateVersion.version.desc(), AiPipelineTemplateVersion.id.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_latest_draft_version(
    db: AsyncSession,
    *,
    template_id: int,
) -> Optional[AiPipelineTemplateVersion]:
    stmt = (
        select(AiPipelineTemplateVersion)
        .where(
            AiPipelineTemplateVersion.template_id == template_id,
            AiPipelineTemplateVersion.is_deleted == False,
            AiPipelineTemplateVersion.is_published == False,
        )
        .order_by(AiPipelineTemplateVersion.version.desc(), AiPipelineTemplateVersion.id.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def cleanup_unpublished_template_versions(
    db: AsyncSession,
    *,
    template_id: int,
    keep_version: Optional[int] = None,
) -> None:
    stmt = (
        update(AiPipelineTemplateVersion)
        .where(
            AiPipelineTemplateVersion.template_id == template_id,
            AiPipelineTemplateVersion.is_deleted == False,
            AiPipelineTemplateVersion.is_published == False,
        )
        .values(is_deleted=True)
    )
    if keep_version is not None:
        stmt = stmt.where(AiPipelineTemplateVersion.version != keep_version)
    await db.execute(stmt)


async def list_bindings(
    db: AsyncSession,
    *,
    binding_type: Optional[str] = None,
    binding_target_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 20,
):
    conditions = [AiPipelineBinding.is_deleted == False]
    if binding_type:
        conditions.append(AiPipelineBinding.binding_type == binding_type)
    if binding_target_id is not None:
        conditions.append(AiPipelineBinding.binding_target_id == binding_target_id)

    count_stmt = select(func.count()).select_from(AiPipelineBinding).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(AiPipelineBinding)
        .where(*conditions)
        .order_by(AiPipelineBinding.updated_at.desc(), AiPipelineBinding.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def count_bindings_by_template_id(
    db: AsyncSession,
    *,
    template_id: int,
) -> int:
    stmt = select(func.count()).select_from(AiPipelineBinding).where(
        AiPipelineBinding.template_id == template_id,
        AiPipelineBinding.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar() or 0


async def create_binding(db: AsyncSession, **kwargs) -> AiPipelineBinding:
    payload = dict(kwargs)
    payload["runtime_input_defaults_json"] = _dump_json(payload.get("runtime_input_defaults_json"))
    payload["resource_bindings_json"] = _dump_json(payload.get("resource_bindings_json"))
    item = AiPipelineBinding(**payload)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def get_binding_by_id(db: AsyncSession, binding_id: int) -> Optional[AiPipelineBinding]:
    stmt = select(AiPipelineBinding).where(
        AiPipelineBinding.id == binding_id,
        AiPipelineBinding.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_binding(
    db: AsyncSession,
    binding: AiPipelineBinding,
    **kwargs,
) -> AiPipelineBinding:
    payload = dict(kwargs)
    if "runtime_input_defaults_json" in payload:
        payload["runtime_input_defaults_json"] = _dump_json(payload.get("runtime_input_defaults_json"))
    if "resource_bindings_json" in payload:
        payload["resource_bindings_json"] = _dump_json(payload.get("resource_bindings_json"))
    for key, value in payload.items():
        setattr(binding, key, value)
    await db.flush()
    await db.refresh(binding)
    return binding


async def delete_binding(
    db: AsyncSession,
    binding: AiPipelineBinding,
) -> None:
    binding.is_deleted = True
    await db.flush()


async def list_bindings_with_resource_bindings(
    db: AsyncSession,
) -> list[AiPipelineBinding]:
    stmt = (
        select(AiPipelineBinding)
        .where(
            AiPipelineBinding.is_deleted == False,
            AiPipelineBinding.resource_bindings_json.is_not(None),
        )
        .order_by(AiPipelineBinding.updated_at.desc(), AiPipelineBinding.id.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_provider_resources(
    db: AsyncSession,
    *,
    enabled_only: bool = False,
    offset: int = 0,
    limit: int = 200,
):
    conditions = [AiPipelineProviderResource.is_deleted == False]
    if enabled_only:
        conditions.append(AiPipelineProviderResource.enabled == True)

    count_stmt = select(func.count()).select_from(AiPipelineProviderResource).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(AiPipelineProviderResource)
        .where(*conditions)
        .order_by(AiPipelineProviderResource.updated_at.desc(), AiPipelineProviderResource.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return items, total


async def get_provider_resource_by_id(
    db: AsyncSession,
    resource_id: int,
) -> Optional[AiPipelineProviderResource]:
    stmt = select(AiPipelineProviderResource).where(
        AiPipelineProviderResource.id == resource_id,
        AiPipelineProviderResource.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_provider_resource_by_key(
    db: AsyncSession,
    provider_key: str,
) -> Optional[AiPipelineProviderResource]:
    stmt = select(AiPipelineProviderResource).where(
        AiPipelineProviderResource.resource_id == provider_key,
        AiPipelineProviderResource.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_provider_resource_by_provider_name(
    db: AsyncSession,
    provider_name: str,
) -> Optional[AiPipelineProviderResource]:
    stmt = select(AiPipelineProviderResource).where(
        AiPipelineProviderResource.provider_name == provider_name,
        AiPipelineProviderResource.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_provider_resource(db: AsyncSession, **kwargs) -> AiPipelineProviderResource:
    payload = dict(kwargs)
    payload["extra_headers_json"] = _dump_json(payload.get("extra_headers_json"))
    payload["extra_json"] = _dump_json(payload.get("extra_json"))
    item = AiPipelineProviderResource(**payload)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_provider_resource(
    db: AsyncSession,
    resource: AiPipelineProviderResource,
    **kwargs,
) -> AiPipelineProviderResource:
    payload = dict(kwargs)
    if "extra_headers_json" in payload:
        payload["extra_headers_json"] = _dump_json(payload.get("extra_headers_json"))
    if "extra_json" in payload:
        payload["extra_json"] = _dump_json(payload.get("extra_json"))
    for key, value in payload.items():
        setattr(resource, key, value)
    await db.flush()
    await db.refresh(resource)
    return resource


async def delete_provider_resource(
    db: AsyncSession,
    resource: AiPipelineProviderResource,
) -> None:
    resource.is_deleted = True
    await db.flush()


async def get_assistant_config(db: AsyncSession) -> Optional[AssistantConfig]:
    stmt = select(AssistantConfig).where(
        AssistantConfig.config_key == ASSISTANT_CONFIG_KEY,
        AssistantConfig.is_deleted == False,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_assistant_config(db: AsyncSession, **kwargs) -> AssistantConfig:
    item = AssistantConfig(config_key=ASSISTANT_CONFIG_KEY, **kwargs)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_assistant_config(
    db: AsyncSession,
    config: AssistantConfig,
    **kwargs,
) -> AssistantConfig:
    for key, value in kwargs.items():
        setattr(config, key, value)
    await db.flush()
    await db.refresh(config)
    return config


async def clear_default_bindings(
    db: AsyncSession,
    *,
    binding_type: str,
    binding_target_id: int,
) -> None:
    stmt = (
        update(AiPipelineBinding)
        .where(
            AiPipelineBinding.binding_type == binding_type,
            AiPipelineBinding.binding_target_id == binding_target_id,
            AiPipelineBinding.is_deleted == False,
        )
        .values(is_default=False)
    )
    await db.execute(stmt)


def load_json_value(value):
    return _load_json(value)


async def list_model_resources(
    db: AsyncSession,
    *,
    deployed_only: bool = True,
    offset: int = 0,
    limit: int = 200,
) -> list[AvailableModel]:
    conditions = [AvailableModel.is_deleted == False]
    if deployed_only:
        conditions.append(AvailableModel.is_deployed == True)

    stmt = (
        select(AvailableModel)
        .where(*conditions)
        .order_by(
            AvailableModel.is_deployed.desc(),
            case((AvailableModel.deployed_at.is_(None), 1), else_=0),
            AvailableModel.deployed_at.desc(),
            AvailableModel.created_at.desc(),
            AvailableModel.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())
