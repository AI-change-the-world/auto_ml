"""Read-only workspace query tools available to the workbench assistant."""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AiPipelineBatchRun,
    AiPipelineBatchRunEvent,
    AiPipelineBatchRunItem,
    Annotation,
    AnnotationRecord,
    AvailableModel,
    Dataset,
    SampleItem,
    Task,
)

from .knowledge_base import (
    PRODUCT_KNOWLEDGE_DOCUMENTS,
    PRODUCT_KNOWLEDGE_SOURCES,
    AssistantKnowledgeBase,
)


TASK_STATUS_NAMES = {
    0: "pending",
    1: "running",
    2: "postprocessing",
    3: "succeeded",
    4: "failed",
}
TASK_STATUS_VALUES = {name: value for value, name in TASK_STATUS_NAMES.items()}
MAX_TOOL_RESULT_LIMIT = 20


ASSISTANT_QUERY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_product_knowledge",
            "description": (
                "读取 AutoML 工作台操作知识库。用户询问如何创建、上传、标注、导出、训练、部署、字段格式、页面入口或操作步骤时必须使用。"
                "请根据问题从下列文件中选择所有需要的文件并在一次调用中传入；不要按关键词搜索，也不要遗漏跨流程问题所需的文件。\n"
                + "\n".join(f"- {document.source}: {document.description}" for document in PRODUCT_KNOWLEDGE_DOCUMENTS)
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "documents": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(PRODUCT_KNOWLEDGE_SOURCES)},
                        "minItems": 1,
                        "maxItems": 5,
                        "uniqueItems": True,
                        "description": "要读取的知识库文件名。一个问题涉及多个主题时，选择多个文件。",
                    },
                },
                "required": ["documents"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_platform_overview",
            "description": "查询工作台当前总览：数据集、标注项目、训练任务、已部署模型和批量标注任务的实时数量。用于回答平台整体状态或数量问题。",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_datasets",
            "description": "按名称查询数据集，并返回实时样本数量、数据类型、场景类型与创建时间。用户询问某个数据集或数据集清单时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "数据集名称关键词；不传则列出最近创建的数据集。",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "最多返回数量，默认 10。",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_annotations",
            "description": "按名称查询标注项目，返回关联数据集、标注类型、类别和实际标注记录数。用户询问标注项目、类别或完成情况时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "标注项目名称关键词；不传则列出最近创建的标注项目。",
                    },
                    "dataset_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "可选，限定关联的数据集 ID。",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "最多返回数量，默认 10。",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_training_tasks",
            "description": "查询训练任务及其状态、关联数据集/标注、创建时间和失败原因摘要。排查训练任务或询问运行状态时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "pending", "running", "postprocessing", "succeeded", "failed"],
                        "description": "任务状态；不传或 all 表示全部状态。",
                    },
                    "dataset_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "可选，限定关联的数据集 ID。",
                    },
                    "annotation_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "可选，限定关联的标注项目 ID。",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "最多返回数量，默认 10。",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_deployments",
            "description": "查询模型和部署状态，返回模型名称、部署标识、设备、版本、推理次数和最近推理时间。用户询问部署、在线模型或推理使用情况时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "deployed_only": {
                        "type": "boolean",
                        "description": "为 true 时只返回已部署模型；默认 false。",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "模型名称关键词；不传则列出最近创建的模型。",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "最多返回数量，默认 10。",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_batch_annotation_runs",
            "description": "查询批量辅助标注运行记录，返回 run_id、脚本、状态、进度、各结果计数、关联数据集/标注和错误摘要。用户询问批量标注运行状态时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "queued", "running", "succeeded", "failed", "canceled"],
                        "description": "运行状态；不传或 all 表示全部状态。",
                    },
                    "dataset_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "可选，限定数据集 ID。",
                    },
                    "annotation_id": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "可选，限定标注项目 ID。",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "最多返回数量，默认 10。",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_batch_annotation_run_detail",
            "description": "按 run_id 查询一条批量辅助标注运行的完整诊断摘要，包括样本状态统计、最近失败样本错误和最近事件。用户给出批量任务 ID 或需要排障细节时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "批量标注任务运行 ID，例如 batch_xxx。",
                    },
                },
                "required": ["run_id"],
                "additionalProperties": False,
            },
        },
    },
]


class AssistantQueryTools:
    """Executes the narrow, read-only query surface exposed to the model."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_base = AssistantKnowledgeBase()

    async def execute(self, tool_name: str, raw_arguments: str | None) -> dict[str, Any]:
        try:
            arguments = self._parse_arguments(raw_arguments)
            allowed_arguments = {
                "read_product_knowledge": {"documents"},
                "get_platform_overview": set(),
                "list_datasets": {"keyword", "limit"},
                "list_annotations": {"keyword", "dataset_id", "limit"},
                "list_training_tasks": {"status", "dataset_id", "annotation_id", "limit"},
                "list_deployments": {"deployed_only", "keyword", "limit"},
                "list_batch_annotation_runs": {"status", "dataset_id", "annotation_id", "limit"},
                "get_batch_annotation_run_detail": {"run_id"},
            }
            handlers = {
                "read_product_knowledge": self.read_product_knowledge,
                "get_platform_overview": self.get_platform_overview,
                "list_datasets": self.list_datasets,
                "list_annotations": self.list_annotations,
                "list_training_tasks": self.list_training_tasks,
                "list_deployments": self.list_deployments,
                "list_batch_annotation_runs": self.list_batch_annotation_runs,
                "get_batch_annotation_run_detail": self.get_batch_annotation_run_detail,
            }
            handler = handlers.get(tool_name)
            if not handler:
                return {"ok": False, "error": f"未知查询工具：{tool_name}"}
            unexpected_arguments = set(arguments) - allowed_arguments[tool_name]
            if unexpected_arguments:
                raise ValueError(f"工具参数不支持：{', '.join(sorted(unexpected_arguments))}")
            result = await handler(arguments)
            logger.info("Assistant query tool executed: tool={} result_count={}", tool_name, self._result_count(result))
            return {"ok": True, "data": result}
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception:
            logger.exception("Assistant query tool failed: tool={}", tool_name)
            return {"ok": False, "error": "平台查询失败，请告知用户查看服务端日志或稍后重试。"}

    async def read_product_knowledge(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        documents = arguments.get("documents")
        if not isinstance(documents, list) or not documents:
            raise ValueError("documents 必须是至少包含一个文件名的数组")
        if not all(isinstance(source, str) and source in PRODUCT_KNOWLEDGE_SOURCES for source in documents):
            raise ValueError("documents 包含不支持的知识库文件")
        return self.knowledge_base.read(documents)

    async def get_platform_overview(self, _arguments: dict[str, Any]) -> dict[str, Any]:
        dataset_count, annotation_count, task_count, running_task_count, deployed_model_count, batch_run_count, running_batch_count = (
            await self._get_counts()
        )
        return {
            "datasets": dataset_count,
            "annotations": annotation_count,
            "training_tasks": {"total": task_count, "running": running_task_count},
            "deployed_models": deployed_model_count,
            "batch_annotation_runs": {"total": batch_run_count, "running": running_batch_count},
        }

    async def list_datasets(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        keyword = self._optional_keyword(arguments.get("keyword"))
        limit = self._limit(arguments.get("limit"))
        actual_sample_count = (
            select(func.count())
            .select_from(SampleItem)
            .where(SampleItem.dataset_id == Dataset.id, SampleItem.is_deleted == False)
            .correlate(Dataset)
            .scalar_subquery()
        )
        stmt = select(
            Dataset.id,
            Dataset.name,
            Dataset.data_type,
            Dataset.scenario_type,
            Dataset.count.label("reported_sample_count"),
            Dataset.description,
            Dataset.created_at,
            actual_sample_count.label("sample_count"),
        ).where(Dataset.is_deleted == False)
        if keyword:
            stmt = stmt.where(Dataset.name.like(f"%{keyword}%"))
        rows = await self.db.execute(stmt.order_by(Dataset.created_at.desc(), Dataset.id.desc()).limit(limit))
        return [
            {
                "id": row.id,
                "name": row.name,
                "sample_count": int(row.sample_count or 0),
                "reported_sample_count": int(row.reported_sample_count or 0),
                "data_type": self._dataset_data_type(row.data_type),
                "scenario_type": self._dataset_scenario_type(row.scenario_type),
                "description": self._truncate(row.description, 300),
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def list_annotations(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        keyword = self._optional_keyword(arguments.get("keyword"))
        dataset_id = self._optional_id(arguments.get("dataset_id"), "dataset_id")
        limit = self._limit(arguments.get("limit"))
        record_count = (
            select(func.count())
            .select_from(AnnotationRecord)
            .where(
                AnnotationRecord.annotation_id == Annotation.id,
                AnnotationRecord.is_deleted == False,
            )
            .correlate(Annotation)
            .scalar_subquery()
        )
        stmt = select(
            Annotation.id,
            Annotation.name,
            Annotation.dataset_id,
            Annotation.annotation_type,
            Annotation.classes,
            Annotation.created_at,
            Dataset.name.label("dataset_name"),
            record_count.label("record_count"),
        ).outerjoin(Dataset, (Dataset.id == Annotation.dataset_id) & (Dataset.is_deleted == False)).where(
            Annotation.is_deleted == False
        )
        if keyword:
            stmt = stmt.where(Annotation.name.like(f"%{keyword}%"))
        if dataset_id:
            stmt = stmt.where(Annotation.dataset_id == dataset_id)
        rows = await self.db.execute(stmt.order_by(Annotation.created_at.desc(), Annotation.id.desc()).limit(limit))
        return [
            {
                "id": row.id,
                "name": row.name,
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "annotation_type": self._annotation_type(row.annotation_type),
                "classes": self._parse_classes(row.classes),
                "record_count": int(row.record_count or 0),
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def list_training_tasks(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        status = self._task_status(arguments.get("status"))
        dataset_id = self._optional_id(arguments.get("dataset_id"), "dataset_id")
        annotation_id = self._optional_id(arguments.get("annotation_id"), "annotation_id")
        limit = self._limit(arguments.get("limit"))
        stmt = select(
            Task.id,
            Task.task_type,
            Task.dataset_id,
            Task.annotation_id,
            Task.status,
            Task.error_message,
            Task.created_at,
            Task.updated_at,
            Dataset.name.label("dataset_name"),
            Annotation.name.label("annotation_name"),
        ).outerjoin(Dataset, (Dataset.id == Task.dataset_id) & (Dataset.is_deleted == False)).outerjoin(
            Annotation,
            (Annotation.id == Task.annotation_id) & (Annotation.is_deleted == False),
        ).where(Task.is_deleted == False)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if dataset_id:
            stmt = stmt.where(Task.dataset_id == dataset_id)
        if annotation_id:
            stmt = stmt.where(Task.annotation_id == annotation_id)
        rows = await self.db.execute(stmt.order_by(Task.created_at.desc(), Task.id.desc()).limit(limit))
        return [
            {
                "id": row.id,
                "task_type": self._task_type(row.task_type),
                "status": TASK_STATUS_NAMES.get(row.status, f"unknown({row.status})"),
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "annotation_id": row.annotation_id,
                "annotation_name": row.annotation_name,
                "error_summary": self._truncate(row.error_message, 1200),
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]

    async def list_deployments(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        deployed_only = self._optional_boolean(arguments.get("deployed_only"), "deployed_only") is True
        keyword = self._optional_keyword(arguments.get("keyword"))
        limit = self._limit(arguments.get("limit"))
        stmt = select(
            AvailableModel.id,
            AvailableModel.name,
            AvailableModel.model_type,
            AvailableModel.runtime_template,
            AvailableModel.task_id,
            AvailableModel.dataset_id,
            AvailableModel.is_deployed,
            AvailableModel.deployment_id,
            AvailableModel.deployment_version,
            AvailableModel.deployment_device,
            AvailableModel.deployed_at,
            AvailableModel.inference_count,
            AvailableModel.last_inference_at,
            AvailableModel.created_at,
        ).where(AvailableModel.is_deleted == False)
        if deployed_only:
            stmt = stmt.where(AvailableModel.is_deployed == True)
        if keyword:
            stmt = stmt.where(AvailableModel.name.like(f"%{keyword}%"))
        rows = await self.db.execute(stmt.order_by(AvailableModel.created_at.desc(), AvailableModel.id.desc()).limit(limit))
        return [
            {
                "id": row.id,
                "name": row.name,
                "model_type": row.model_type,
                "runtime_template": row.runtime_template,
                "task_id": row.task_id,
                "dataset_id": row.dataset_id,
                "is_deployed": bool(row.is_deployed),
                "deployment_id": row.deployment_id,
                "deployment_version": row.deployment_version,
                "deployment_device": row.deployment_device,
                "deployed_at": row.deployed_at,
                "inference_count": int(row.inference_count or 0),
                "last_inference_at": row.last_inference_at,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def list_batch_annotation_runs(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        status = self._batch_run_status(arguments.get("status"))
        dataset_id = self._optional_id(arguments.get("dataset_id"), "dataset_id")
        annotation_id = self._optional_id(arguments.get("annotation_id"), "annotation_id")
        limit = self._limit(arguments.get("limit"))
        stmt = select(
            AiPipelineBatchRun.run_id,
            AiPipelineBatchRun.dataset_id,
            AiPipelineBatchRun.annotation_id,
            AiPipelineBatchRun.script_key,
            AiPipelineBatchRun.script_version,
            AiPipelineBatchRun.status,
            AiPipelineBatchRun.progress,
            AiPipelineBatchRun.total_count,
            AiPipelineBatchRun.succeeded_count,
            AiPipelineBatchRun.failed_count,
            AiPipelineBatchRun.skipped_count,
            AiPipelineBatchRun.canceled_count,
            AiPipelineBatchRun.error_message,
            AiPipelineBatchRun.started_at,
            AiPipelineBatchRun.finished_at,
            AiPipelineBatchRun.created_at,
            Dataset.name.label("dataset_name"),
            Annotation.name.label("annotation_name"),
        ).outerjoin(Dataset, (Dataset.id == AiPipelineBatchRun.dataset_id) & (Dataset.is_deleted == False)).outerjoin(
            Annotation,
            (Annotation.id == AiPipelineBatchRun.annotation_id) & (Annotation.is_deleted == False),
        ).where(AiPipelineBatchRun.is_deleted == False)
        if status:
            stmt = stmt.where(AiPipelineBatchRun.status == status)
        if dataset_id:
            stmt = stmt.where(AiPipelineBatchRun.dataset_id == dataset_id)
        if annotation_id:
            stmt = stmt.where(AiPipelineBatchRun.annotation_id == annotation_id)
        rows = await self.db.execute(stmt.order_by(AiPipelineBatchRun.created_at.desc(), AiPipelineBatchRun.id.desc()).limit(limit))
        return [
            {
                "run_id": row.run_id,
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                "annotation_id": row.annotation_id,
                "annotation_name": row.annotation_name,
                "script_key": row.script_key,
                "script_version": row.script_version,
                "status": row.status,
                "progress": int(row.progress or 0),
                "total_count": int(row.total_count or 0),
                "succeeded_count": int(row.succeeded_count or 0),
                "failed_count": int(row.failed_count or 0),
                "skipped_count": int(row.skipped_count or 0),
                "canceled_count": int(row.canceled_count or 0),
                "error_summary": self._truncate(row.error_message, 1200),
                "started_at": row.started_at,
                "finished_at": row.finished_at,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    async def get_batch_annotation_run_detail(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run_id = self._required_run_id(arguments.get("run_id"))
        run = await self.db.scalar(
            select(AiPipelineBatchRun).where(
                AiPipelineBatchRun.run_id == run_id,
                AiPipelineBatchRun.is_deleted == False,
            )
        )
        if not run:
            return {"found": False, "run_id": run_id}

        dataset_name, annotation_name = await self._related_names(run.dataset_id, run.annotation_id)
        status_rows = await self.db.execute(
            select(AiPipelineBatchRunItem.status, func.count())
            .where(
                AiPipelineBatchRunItem.batch_run_id == run.id,
                AiPipelineBatchRunItem.is_deleted == False,
            )
            .group_by(AiPipelineBatchRunItem.status)
        )
        failures = await self.db.execute(
            select(
                AiPipelineBatchRunItem.item_key,
                AiPipelineBatchRunItem.status,
                AiPipelineBatchRunItem.error_message,
                AiPipelineBatchRunItem.attempt_count,
                AiPipelineBatchRunItem.finished_at,
            )
            .where(
                AiPipelineBatchRunItem.batch_run_id == run.id,
                AiPipelineBatchRunItem.is_deleted == False,
                AiPipelineBatchRunItem.error_message.is_not(None),
            )
            .order_by(AiPipelineBatchRunItem.updated_at.desc(), AiPipelineBatchRunItem.id.desc())
            .limit(10)
        )
        events = await self.db.execute(
            select(
                AiPipelineBatchRunEvent.event_type,
                AiPipelineBatchRunEvent.event_payload,
                AiPipelineBatchRunEvent.created_at,
            )
            .where(
                AiPipelineBatchRunEvent.batch_run_id == run.id,
                AiPipelineBatchRunEvent.is_deleted == False,
            )
            .order_by(AiPipelineBatchRunEvent.id.desc())
            .limit(10)
        )
        return {
            "found": True,
            "run": {
                "run_id": run.run_id,
                "dataset_id": run.dataset_id,
                "dataset_name": dataset_name,
                "annotation_id": run.annotation_id,
                "annotation_name": annotation_name,
                "script_key": run.script_key,
                "script_version": run.script_version,
                "status": run.status,
                "progress": int(run.progress or 0),
                "total_count": int(run.total_count or 0),
                "succeeded_count": int(run.succeeded_count or 0),
                "failed_count": int(run.failed_count or 0),
                "skipped_count": int(run.skipped_count or 0),
                "canceled_count": int(run.canceled_count or 0),
                "error_message": self._truncate(run.error_message, 2400),
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "created_at": run.created_at,
            },
            "item_status_counts": {row[0]: int(row[1] or 0) for row in status_rows},
            "recent_item_errors": [
                {
                    "item_key": row.item_key,
                    "status": row.status,
                    "attempt_count": int(row.attempt_count or 0),
                    "error": self._truncate(row.error_message, 2400),
                    "finished_at": row.finished_at,
                }
                for row in failures
            ],
            "recent_events": [
                {
                    "event_type": row.event_type,
                    "payload": self._parse_json_value(row.event_payload, 2400),
                    "created_at": row.created_at,
                }
                for row in events
            ],
        }

    async def _get_counts(self) -> tuple[int, int, int, int, int, int, int]:
        values = await self.db.execute(
            select(
                select(func.count()).select_from(Dataset).where(Dataset.is_deleted == False).scalar_subquery(),
                select(func.count()).select_from(Annotation).where(Annotation.is_deleted == False).scalar_subquery(),
                select(func.count()).select_from(Task).where(Task.is_deleted == False).scalar_subquery(),
                select(func.count()).select_from(Task).where(Task.is_deleted == False, Task.status == 1).scalar_subquery(),
                select(func.count()).select_from(AvailableModel).where(
                    AvailableModel.is_deleted == False,
                    AvailableModel.is_deployed == True,
                ).scalar_subquery(),
                select(func.count()).select_from(AiPipelineBatchRun).where(
                    AiPipelineBatchRun.is_deleted == False
                ).scalar_subquery(),
                select(func.count()).select_from(AiPipelineBatchRun).where(
                    AiPipelineBatchRun.is_deleted == False,
                    AiPipelineBatchRun.status.in_(["queued", "running"]),
                ).scalar_subquery(),
            )
        )
        return tuple(int(value or 0) for value in values.one())

    async def _related_names(self, dataset_id: int, annotation_id: int) -> tuple[str | None, str | None]:
        dataset_name = await self.db.scalar(
            select(Dataset.name).where(Dataset.id == dataset_id, Dataset.is_deleted == False)
        )
        annotation_name = await self.db.scalar(
            select(Annotation.name).where(Annotation.id == annotation_id, Annotation.is_deleted == False)
        )
        return dataset_name, annotation_name

    @staticmethod
    def _parse_arguments(raw_arguments: str | None) -> dict[str, Any]:
        if not raw_arguments:
            return {}
        try:
            value = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise ValueError("工具参数不是有效 JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("工具参数必须是 JSON 对象")
        return value

    @staticmethod
    def _optional_keyword(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("keyword 必须是字符串")
        normalized = value.strip()
        if len(normalized) > 100:
            raise ValueError("keyword 不能超过 100 个字符")
        return normalized or None

    @staticmethod
    def _optional_id(value: Any, field_name: str) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{field_name} 必须是正整数")
        return value

    @staticmethod
    def _limit(value: Any) -> int:
        if value is None:
            return 10
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("limit 必须是整数")
        if not 1 <= value <= MAX_TOOL_RESULT_LIMIT:
            raise ValueError(f"limit 必须在 1 到 {MAX_TOOL_RESULT_LIMIT} 之间")
        return value

    @staticmethod
    def _optional_boolean(value: Any, field_name: str) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} 必须是布尔值")
        return value

    @staticmethod
    def _task_status(value: Any) -> int | None:
        if value is None or value == "all":
            return None
        if not isinstance(value, str) or value not in TASK_STATUS_VALUES:
            raise ValueError("status 必须是有效的训练任务状态")
        return TASK_STATUS_VALUES[value]

    @staticmethod
    def _batch_run_status(value: Any) -> str | None:
        if value is None or value == "all":
            return None
        valid_values = {"queued", "running", "succeeded", "failed", "canceled"}
        if not isinstance(value, str) or value not in valid_values:
            raise ValueError("status 必须是有效的批量标注运行状态")
        return value

    @staticmethod
    def _required_run_id(value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("run_id 必须是字符串")
        normalized = value.strip()
        if not normalized or len(normalized) > 64:
            raise ValueError("run_id 不能为空且不能超过 64 个字符")
        return normalized

    @staticmethod
    def _truncate(value: Any, limit: int) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return normalized if len(normalized) <= limit else f"{normalized[:limit]}..."

    @staticmethod
    def _parse_classes(value: Any) -> list[str]:
        parsed = AssistantQueryTools._parse_json_value(value)
        if not isinstance(parsed, list):
            return []
        return [str(item) for item in parsed[:50]]

    @staticmethod
    def _parse_json_value(value: Any, string_limit: int = 600) -> Any:
        if not isinstance(value, str):
            return value
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return AssistantQueryTools._truncate(value, string_limit)
        serialized = json.dumps(parsed, ensure_ascii=False, default=_json_default)
        if len(serialized) > string_limit:
            return AssistantQueryTools._truncate(serialized, string_limit)
        return parsed

    @staticmethod
    def _dataset_data_type(value: Any) -> str:
        return {0: "image", 1: "text", 2: "video", 3: "audio"}.get(value, f"unknown({value})")

    @staticmethod
    def _dataset_scenario_type(value: Any) -> str:
        return {0: "general", 1: "aerial", 2: "llm_conversation", 3: "mllm_conversation"}.get(
            value,
            f"unknown({value})",
        )

    @staticmethod
    def _annotation_type(value: Any) -> str:
        return {0: "detection", 1: "classification", 2: "segmentation", 3: "mllm", 4: "pose", 5: "llm"}.get(
            value,
            f"unknown({value})",
        )

    @staticmethod
    def _task_type(value: Any) -> str:
        return {0: "detection", 1: "classification", 2: "segmentation", 3: "pose"}.get(value, f"unknown({value})")

    @staticmethod
    def _result_count(result: Any) -> int:
        if isinstance(result, list):
            return len(result)
        return 1


def serialize_tool_result(value: Any) -> str:
    """Serialise SQL values for an OpenAI tool response without losing timestamps."""
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)
