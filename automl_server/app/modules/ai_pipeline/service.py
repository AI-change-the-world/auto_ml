"""AI Pipeline service"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequestException, NotFoundException
from app.config.settings import get_settings
from app.utils.http_client import HttpClient

from . import crud
from .schemas import (
    AiPipelineBindingCreate,
    AiPipelineModelResourceItem,
    AiPipelineCapabilityContextTarget,
    AiPipelineCapabilityField,
    AiPipelineCapabilityFieldOption,
    AiPipelineCapabilityItem,
    AiPipelineBindingResponse,
    AiPipelineBindingUpdate,
    AiPipelineTemplateCreate,
    AiPipelineTemplateDetail,
    AiPipelineTemplateDraftSave,
    AiPipelineTemplateListItem,
)

ASSIST_CAPABILITIES = {
    "assist_annotation",
    "draft_annotation",
    "draft_annotation_preview",
    "extract_white_annotations",
    "render_white_annotation_overlay",
    "understand_white_annotations",
}


class AiPipelineService:
    def _build_template_detail_base(
        self,
        template,
        current_version,
    ) -> dict[str, Any]:
        base_detail = AiPipelineTemplateListItem.model_validate(
            template,
            from_attributes=True,
        ).model_dump()
        base_detail["latest_version"] = getattr(current_version, "version", None) or 0
        base_detail["published_version"] = None
        return base_detail

    def _build_template_detail_from_version(
        self,
        *,
        base_detail: dict[str, Any],
        version,
    ) -> AiPipelineTemplateDetail:
        return AiPipelineTemplateDetail(
            **base_detail,
            definition_json=crud.load_json_value(getattr(version, "definition_json", None)),
            form_schema_json=crud.load_json_value(getattr(version, "form_schema_json", None)),
            change_note=getattr(version, "change_note", None),
        )

    async def _get_current_template_version(
        self,
        db: AsyncSession,
        template_id: int,
    ):
        return await crud.get_template_version(
            db,
            template_id=template_id,
            version=None,
        )

    async def list_capabilities(self) -> list[AiPipelineCapabilityItem]:
        settings = get_settings()
        client = HttpClient(
            base_url=settings.ai_pipeline_runtime.base_url,
            timeout=settings.ai_pipeline_runtime.timeout,
        )
        try:
            response = await client.get("/v1/capabilities")
        except Exception as exc:
            raise BadRequestException(f"failed to load AI pipeline capabilities: {exc}") from exc

        if response.status_code != 200:
            raise BadRequestException(
                f"failed to load AI pipeline capabilities: {response.status_code}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise BadRequestException(
                f"invalid AI pipeline capability payload: {exc}"
            ) from exc

        if not isinstance(payload, list):
            raise BadRequestException("invalid AI pipeline capability payload")

        return [
            self._build_capability_item(item)
            for item in payload
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]

    async def create_template(
        self,
        db: AsyncSession,
        data: AiPipelineTemplateCreate,
    ) -> AiPipelineTemplateListItem:
        existing = await crud.get_template_by_key(db, data.template_key)
        if existing:
            raise BadRequestException(f"AI pipeline template `{data.template_key}` already exists")

        payload = data.model_dump()
        payload["latest_version"] = 0
        payload["published_version"] = None
        created = await crud.create_template(db, **payload)
        return AiPipelineTemplateListItem.model_validate(created, from_attributes=True)

    async def list_templates(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        scene_type: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> tuple[list[AiPipelineTemplateListItem], int]:
        offset = (page - 1) * page_size
        items, total = await crud.list_templates(
            db,
            offset=offset,
            limit=page_size,
            scene_type=scene_type,
            status=status,
            keyword=keyword,
        )
        return [
            AiPipelineTemplateListItem.model_validate(item, from_attributes=True)
            for item in items
        ], total

    async def get_template_detail(
        self,
        db: AsyncSession,
        template_key: str,
    ) -> AiPipelineTemplateDetail:
        template = await crud.get_template_by_key(db, template_key)
        if not template:
            raise NotFoundException(f"AI pipeline template `{template_key}` not found")

        current_version = await self._get_current_template_version(db, template.id)
        base_detail = self._build_template_detail_base(template, current_version)
        if not current_version:
            return AiPipelineTemplateDetail(
                **base_detail,
                definition_json=None,
                form_schema_json=None,
            )

        return self._build_template_detail_from_version(
            base_detail=base_detail,
            version=current_version,
        )

    async def save_template_definition(
        self,
        db: AsyncSession,
        template_key: str,
        data: AiPipelineTemplateDraftSave,
    ) -> AiPipelineTemplateDetail:
        template = await crud.get_template_by_key(db, template_key)
        if not template:
            raise NotFoundException(f"AI pipeline template `{template_key}` not found")

        current_version = await self._get_current_template_version(db, template.id)
        payload = data.model_dump()
        if current_version:
            saved_version = await crud.update_template_version(
                db,
                current_version,
                **payload,
            )
            next_latest_version = saved_version.version
        else:
            next_version = 1
            saved_version = await crud.create_template_version(
                db,
                template_id=template.id,
                version=next_version,
                is_published=False,
                **payload,
            )
            next_latest_version = next_version

        await crud.update_template(
            db,
            template,
            latest_version=next_latest_version,
            published_version=None,
            status="active" if template.status != "disabled" else "disabled",
        )
        return await self.get_template_detail(db, template_key)

    async def disable_template(
        self,
        db: AsyncSession,
        template_key: str,
    ) -> AiPipelineTemplateDetail:
        template = await crud.get_template_by_key(db, template_key)
        if not template:
            raise NotFoundException(f"AI pipeline template `{template_key}` not found")

        await crud.update_template(
            db,
            template,
            status="disabled",
        )
        return await self.get_template_detail(db, template_key)

    async def delete_template(
        self,
        db: AsyncSession,
        template_key: str,
    ) -> None:
        template = await crud.get_template_by_key(db, template_key)
        if not template:
            raise NotFoundException(f"AI pipeline template `{template_key}` not found")

        binding_count = await crud.count_bindings_by_template_id(
            db,
            template_id=template.id,
        )
        if binding_count > 0:
            raise BadRequestException(
                f"AI pipeline template `{template_key}` still has active bindings"
            )

        await crud.delete_template(db, template)

    async def list_bindings(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        binding_type: str | None = None,
        binding_target_id: int | None = None,
    ) -> tuple[list[AiPipelineBindingResponse], int]:
        offset = (page - 1) * page_size
        items, total = await crud.list_bindings(
            db,
            binding_type=binding_type,
            binding_target_id=binding_target_id,
            offset=offset,
            limit=page_size,
        )
        result: list[AiPipelineBindingResponse] = []
        for item in items:
            result.append(await self._build_binding_response(db, item))
        return result, total

    async def create_binding(
        self,
        db: AsyncSession,
        data: AiPipelineBindingCreate,
    ) -> AiPipelineBindingResponse:
        template = await crud.get_template_by_id(db, data.template_id)
        if not template:
            raise NotFoundException(f"AI pipeline template id `{data.template_id}` not found")

        version = await self._get_current_template_version(db, data.template_id)
        if not version:
            raise BadRequestException(f"AI pipeline template `{template.template_key}` definition is empty")

        annotation = None
        if data.binding_type == "annotation_project":
            from app.modules.annotation import crud as annotation_crud

            annotation = await annotation_crud.get_annotation_by_id(
                db,
                data.binding_target_id,
            )
            if not annotation:
                raise NotFoundException(
                    f"annotation project `{data.binding_target_id}` not found"
                )

        if data.is_default:
            await crud.clear_default_bindings(
                db,
                binding_type=data.binding_type,
                binding_target_id=data.binding_target_id,
            )

        create_payload = data.model_dump()
        create_payload["template_version"] = version.version
        created = await crud.create_binding(db, **create_payload)
        if data.is_default and data.binding_type == "annotation_project" and annotation is not None:
            from app.modules.annotation import crud as annotation_crud

            await annotation_crud.update_annotation(
                db,
                annotation.id,
                default_ai_pipeline_binding_id=created.id,
            )
        return await self._build_binding_response(db, created, template=template, version=version)

    async def update_binding(
        self,
        db: AsyncSession,
        binding_id: int,
        data: AiPipelineBindingUpdate,
    ) -> AiPipelineBindingResponse:
        binding = await crud.get_binding_by_id(db, binding_id)
        if not binding:
            raise NotFoundException(f"AI pipeline binding `{binding_id}` not found")

        update_data = data.model_dump(exclude_unset=True)
        template_id = update_data.get("template_id", binding.template_id)
        if template_id != binding.template_id:
            template = await crud.get_template_by_id(db, template_id)
            if not template:
                raise NotFoundException(f"AI pipeline template id `{template_id}` not found")
            version = await self._get_current_template_version(db, template_id)
            if not version:
                raise BadRequestException(f"AI pipeline template `{template.template_key}` definition is empty")
            update_data["template_version"] = version.version
        if "is_default" in update_data and update_data["is_default"] is True:
            await crud.clear_default_bindings(
                db,
                binding_type=binding.binding_type,
                binding_target_id=binding.binding_target_id,
            )

        updated = await crud.update_binding(db, binding, **update_data)

        if binding.binding_type == "annotation_project":
            from app.modules.annotation import crud as annotation_crud

            annotation = await annotation_crud.get_annotation_by_id(
                db,
                binding.binding_target_id,
            )
            if annotation:
                if updated.is_default:
                    await annotation_crud.update_annotation(
                        db,
                        annotation.id,
                        default_ai_pipeline_binding_id=updated.id,
                    )
                elif annotation.default_ai_pipeline_binding_id == updated.id:
                    await annotation_crud.update_annotation(
                        db,
                        annotation.id,
                        default_ai_pipeline_binding_id=None,
                    )

        return await self._build_binding_response(db, updated)

    async def delete_binding(
        self,
        db: AsyncSession,
        binding_id: int,
    ) -> None:
        binding = await crud.get_binding_by_id(db, binding_id)
        if not binding:
            raise NotFoundException(f"AI pipeline binding `{binding_id}` not found")

        await crud.delete_binding(db, binding)

        if binding.binding_type == "annotation_project":
            from app.modules.annotation import crud as annotation_crud

            annotation = await annotation_crud.get_annotation_by_id(
                db,
                binding.binding_target_id,
            )
            if annotation and annotation.default_ai_pipeline_binding_id == binding.id:
                await annotation_crud.update_annotation(
                    db,
                    annotation.id,
                    default_ai_pipeline_binding_id=None,
                )

    async def get_binding_execution_context(
        self,
        db: AsyncSession,
        binding_id: int,
    ) -> dict[str, Any] | None:
        binding = await crud.get_binding_by_id(db, binding_id)
        if not binding:
            return None

        template = await crud.get_template_by_id(db, binding.template_id)
        if not template:
            return None

        version = await crud.get_template_version(
            db,
            template_id=template.id,
            version=binding.template_version,
        )
        if not version:
            return None

        descriptor = self._build_legacy_assist_descriptor(template, version)
        if descriptor is None:
            return None

        return {
            "binding_id": binding.id,
            "binding_type": binding.binding_type,
            "binding_target_id": binding.binding_target_id,
            "template_id": template.id,
            "template_key": template.template_key,
            "template_version": version.version,
            "template_name": template.name,
            "definition_json": crud.load_json_value(getattr(version, "definition_json", None)),
            "runtime_input_defaults_json": crud.load_json_value(
                binding.runtime_input_defaults_json
            ),
            "resource_bindings_json": crud.load_json_value(
                binding.resource_bindings_json
            ),
            "pipeline_descriptor": descriptor,
        }

    async def list_assist_template_descriptors(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        return await self._list_legacy_assist_descriptors(db)

    async def list_assist_template_detail_descriptors(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        return await self._list_legacy_assist_descriptors(db)

    async def list_home_assist_template_descriptors(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        templates, _ = await crud.list_templates(
            db,
            offset=0,
            limit=500,
            scene_type="assist_annotation",
        )
        items: list[dict[str, Any]] = []
        for template in templates:
            target_version = template.published_version or template.latest_version
            version = None
            if target_version:
                version = await crud.get_template_version(
                    db,
                    template_id=template.id,
                    version=target_version,
                )
            descriptor = self._build_home_assist_descriptor(template, version)
            if descriptor is not None:
                items.append(descriptor)
        return items

    async def list_model_resources(
        self,
        db: AsyncSession,
        *,
        deployed_only: bool = True,
        limit: int = 200,
    ) -> list[AiPipelineModelResourceItem]:
        items = await crud.list_model_resources(
            db,
            deployed_only=deployed_only,
            offset=0,
            limit=limit,
        )
        result: list[AiPipelineModelResourceItem] = []
        for item in items:
            display_name = (
                str(getattr(item, "name", "") or "").strip()
                or f"Model #{item.id}"
            )
            result.append(
                AiPipelineModelResourceItem(
                    resource_id=f"model:{item.id}",
                    model_id=item.id,
                    display_name=display_name,
                    model_name=getattr(item, "name", None),
                    model_type=getattr(item, "model_type", None),
                    runtime_template=getattr(item, "runtime_template", None),
                    is_deployed=bool(getattr(item, "is_deployed", False)),
                    deployment_device=getattr(item, "deployment_device", None),
                    deployed_at=getattr(item, "deployed_at", None),
                )
            )
        return result

    async def _list_legacy_assist_descriptors(
        self,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        templates, _ = await crud.list_templates(
            db,
            offset=0,
            limit=500,
        )
        items: list[dict[str, Any]] = []
        for template in templates:
            if template.status not in {"published", "disabled"}:
                continue

            target_version = template.published_version or template.latest_version
            if not target_version:
                continue

            version = await crud.get_template_version(
                db,
                template_id=template.id,
                version=target_version,
            )
            if not version:
                continue

            descriptor = self._build_legacy_assist_descriptor(template, version)
            if descriptor is not None:
                items.append(descriptor)
        return items

    def _build_legacy_assist_descriptor(
        self,
        template,
        version,
    ) -> dict[str, Any] | None:
        definition = crud.load_json_value(getattr(version, "definition_json", None))
        form_schema = crud.load_json_value(getattr(version, "form_schema_json", None))

        definition_dict = definition if isinstance(definition, dict) else {}
        form_schema_dict = form_schema if isinstance(form_schema, dict) else {}
        legacy_metadata = form_schema_dict.get("legacy_metadata")
        if not isinstance(legacy_metadata, dict):
            legacy_metadata = {}

        pipeline_type = str(
            definition_dict.get("pipeline_type")
            or template.scene_type
            or ""
        ).strip() or "generic"
        supported_annotation_types = self._normalize_int_list(
            definition_dict.get("supported_annotation_types")
            or legacy_metadata.get("supported_annotation_types")
        )
        supported_shapes = self._normalize_string_list(
            definition_dict.get("supported_shapes")
            or legacy_metadata.get("supported_shapes")
        )
        steps = definition_dict.get("steps")
        if not isinstance(steps, list):
            steps = []
        if not self._looks_like_assist_template(pipeline_type, steps):
            return None

        return {
            "id": template.template_key,
            "name": template.template_key,
            "display_name": template.name,
            "description": template.description,
            "pipeline_type": pipeline_type,
            "supported_annotation_types": supported_annotation_types,
            "supported_shapes": supported_shapes,
            "steps": steps,
            "enabled": template.status != "disabled",
            "template_id": template.id,
            "template_version": version.version,
            "scene_type": template.scene_type,
            "input_kind": template.input_kind,
            "output_kind": template.output_kind,
            "source": "db",
        }

    def _build_home_assist_descriptor(
        self,
        template,
        version=None,
    ) -> dict[str, Any] | None:
        definition = crud.load_json_value(getattr(version, "definition_json", None)) if version else None
        form_schema = crud.load_json_value(getattr(version, "form_schema_json", None)) if version else None

        definition_dict = definition if isinstance(definition, dict) else {}
        form_schema_dict = form_schema if isinstance(form_schema, dict) else {}
        legacy_metadata = form_schema_dict.get("legacy_metadata")
        if not isinstance(legacy_metadata, dict):
            legacy_metadata = {}

        pipeline_type = str(
            definition_dict.get("pipeline_type")
            or template.scene_type
            or ""
        ).strip() or "generic"
        if pipeline_type != "assist_annotation":
            return None

        supported_annotation_types = self._normalize_int_list(
            definition_dict.get("supported_annotation_types")
            or legacy_metadata.get("supported_annotation_types")
        )
        supported_shapes = self._normalize_string_list(
            definition_dict.get("supported_shapes")
            or legacy_metadata.get("supported_shapes")
        )
        steps = definition_dict.get("steps")
        if not isinstance(steps, list):
            steps = []

        return {
            "id": template.template_key,
            "name": template.template_key,
            "display_name": template.name,
            "description": template.description,
            "pipeline_type": pipeline_type,
            "supported_annotation_types": supported_annotation_types,
            "supported_shapes": supported_shapes,
            "steps": steps,
            "enabled": template.status != "disabled",
            "template_id": template.id,
            "template_version": getattr(version, "version", 0) if version else 0,
            "scene_type": template.scene_type,
            "input_kind": template.input_kind,
            "output_kind": template.output_kind,
            "source": "db",
            "status": template.status,
        }

    async def _build_binding_response(
        self,
        db: AsyncSession,
        binding,
        *,
        template=None,
        version=None,
    ) -> AiPipelineBindingResponse:
        template = template or await crud.get_template_by_id(db, binding.template_id)
        if template and version is None:
            version = await crud.get_template_version(
                db,
                template_id=template.id,
                version=binding.template_version,
            )

        descriptor = (
            self._build_legacy_assist_descriptor(template, version)
            if template and version
            else None
        )
        return AiPipelineBindingResponse(
            id=binding.id,
            binding_type=binding.binding_type,
            binding_target_id=binding.binding_target_id,
            template_id=binding.template_id,
            template_version=binding.template_version,
            template_key=getattr(template, "template_key", None),
            template_name=getattr(template, "name", None),
            name=binding.name,
            description=binding.description,
            pipeline_type=descriptor.get("pipeline_type") if descriptor else None,
            supported_annotation_types=descriptor.get("supported_annotation_types", []) if descriptor else [],
            supported_shapes=descriptor.get("supported_shapes", []) if descriptor else [],
            enabled=bool(descriptor.get("enabled", True)) if descriptor else True,
            is_default=bool(binding.is_default),
            runtime_input_defaults_json=crud.load_json_value(binding.runtime_input_defaults_json),
            resource_bindings_json=crud.load_json_value(binding.resource_bindings_json),
            created_by=binding.created_by,
            created_at=binding.created_at,
            updated_at=binding.updated_at,
        )

    def _looks_like_assist_template(
        self,
        pipeline_type: str,
        steps: list[Any],
    ) -> bool:
        if pipeline_type == "assist_annotation":
            return True
        for step in steps:
            if isinstance(step, dict) and step.get("capability") in ASSIST_CAPABILITIES:
                return True
        return False

    def _normalize_int_list(self, value: Any) -> list[int]:
        if not isinstance(value, list):
            return []
        items: list[int] = []
        for item in value:
            text = str(item).strip()
            if text.lstrip("-").isdigit():
                items.append(int(text))
        return items

    def _normalize_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                items.append(text.lower())
        return items

    def _normalize_optional_string(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _build_capability_item(self, item: dict[str, Any]) -> AiPipelineCapabilityItem:
        name = str(item.get("name") or "").strip()
        display_name = str(item.get("display_name") or name).strip() or name

        return AiPipelineCapabilityItem(
            name=name,
            display_name=display_name,
            description=self._normalize_optional_string(item.get("description")),
            category=str(item.get("category") or "general").strip().lower() or "general",
            requires_provider=bool(item.get("requires_provider", False)),
            provider_role=self._normalize_optional_string(item.get("provider_role")),
            recommended_output_key=self._normalize_optional_string(
                item.get("recommended_output_key")
            ),
            input_types=self._normalize_string_list(item.get("input_types")),
            output_type=self._normalize_optional_string(item.get("output_type")),
            scene_types=self._normalize_string_list(item.get("scene_types")),
            parameter_fields=self._build_capability_fields(item.get("parameter_fields")),
            context_mapping_targets=self._build_context_targets(item.get("context_mapping_targets")),
        )

    def _build_capability_fields(self, items: Any) -> list[AiPipelineCapabilityField]:
        if not isinstance(items, list):
            return []
        result: list[AiPipelineCapabilityField] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            options: list[AiPipelineCapabilityFieldOption] = []
            raw_options = item.get("options")
            if isinstance(raw_options, list):
                for option in raw_options:
                    if not isinstance(option, dict):
                        continue
                    label = str(option.get("label") or option.get("value") or "").strip()
                    if not label or "value" not in option:
                        continue
                    options.append(
                        AiPipelineCapabilityFieldOption(
                            label=label,
                            value=option["value"],
                        )
                    )
            result.append(
                AiPipelineCapabilityField(
                    key=key,
                    label=str(item.get("label") or key),
                    value_type=str(item.get("value_type") or "string"),
                    required=bool(item.get("required", False)),
                    description=str(item.get("description")).strip() if item.get("description") else None,
                    widget=str(item.get("widget")).strip() if item.get("widget") else None,
                    default_value=item.get("default_value"),
                    placeholder=str(item.get("placeholder")).strip() if item.get("placeholder") else None,
                    binding_kind=str(item.get("binding_kind") or "parameter"),
                    resource_type=str(item.get("resource_type")).strip() if item.get("resource_type") else None,
                    task_kind=str(item.get("task_kind")).strip() if item.get("task_kind") else None,
                    deployed_only=bool(item["deployed_only"]) if "deployed_only" in item and item.get("deployed_only") is not None else None,
                    options=options,
                )
            )
        return result

    def _build_context_targets(self, items: Any) -> list[AiPipelineCapabilityContextTarget]:
        if not isinstance(items, list):
            return []
        result: list[AiPipelineCapabilityContextTarget] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            result.append(
                AiPipelineCapabilityContextTarget(
                    key=key,
                    label=str(item.get("label") or key),
                    description=str(item.get("description")).strip() if item.get("description") else None,
                    accepted_output_types=self._normalize_string_list(item.get("accepted_output_types")),
                )
            )
        return result


def get_ai_pipeline_service() -> AiPipelineService:
    return AiPipelineService()
