"""
数据集业务逻辑
"""
import io
import json
import mimetypes
import os
import uuid
from datetime import datetime
import zipfile
import tarfile
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import DataType, DatasetScenarioType
from app.common.exceptions import NotFoundException, BadRequestException
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import (
    AssetResponse,
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    FilePreviewResponse,
    FileContentResponse,
    SampleItemCreate,
    SampleItemUpdate,
    SampleItemResponse,
)

# 支持的压缩包扩展名
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.tar.gz',
                      '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz'}
# 跳过的文件/目录前缀
SKIP_PREFIXES = ('__MACOSX/', '.', '._')


DEFAULT_AERIAL_STITCH_CONFIG: Dict[str, Any] = {
    "grouping": {
        "strategy": "filename_prefix",
        "pattern_hint": "{scene}_{rows}x{cols}_r{row}_c{col}.jpg",
        "sequence_order": "row_major",
    },
    "stitching": {
        "enabled": True,
        "allow_missing_tiles": True,
        "skip_invalid_files": True,
        "default_overlap_ratio": 0.2,
        "manual_alignment_required": False,
    },
    "annotation": {
        "coordinate_source": "global",
        "support_tile_annotation": True,
        "support_mosaic_annotation": True,
    },
    "training": {
        "default_views": ["tile", "mosaic"],
        "allow_view_specific_models": True,
    },
}

DEFAULT_LLM_CONVERSATION_CONFIG: Dict[str, Any] = {
    "conversation": {
        "mode": "llm",
        "result_format": "json",
        "roles": ["system", "user", "assistant"],
        "primary_input": "text",
    }
}

DEFAULT_MLLM_CONVERSATION_CONFIG: Dict[str, Any] = {
    "conversation": {
        "mode": "mllm",
        "result_format": "json",
        "roles": ["system", "user", "assistant"],
        "primary_input": "image",
    }
}

DEFAULT_DPO_PREFERENCE_CONFIG: Dict[str, Any] = {
    "preference": {
        "mode": "dpo",
        "result_format": "json",
        "comparison_type": "pairwise",
        "primary_input": "text",
        "allow_tie": True,
        "allow_skip": True,
    }
}


class DatasetService:
    """数据集服务"""

    def __init__(self):
        self.s3 = get_s3_delegate()

    async def create_dataset(self, db: AsyncSession, data: DatasetCreate) -> DatasetResponse:
        """创建数据集"""
        self._validate_dataset_type_and_scenario(data.data_type, data.scenario_type)
        scenario_config = self._prepare_scenario_config(
            data.data_type,
            data.scenario_type,
            data.scenario_config,
        )

        # 生成 S3 存储路径
        dataset_uuid = str(uuid.uuid4())
        save_path = f"datasets/{dataset_uuid}"

        # 在 S3 创建目录
        try:
            await self.s3.create_directory(save_path, bucket_type="datasets")
        except Exception as e:
            logger.error(f"Failed to create S3 directory: {e}")
            raise BadRequestException(
                f"Failed to create storage directory: {e}")

        # 保存到数据库
        dataset = await crud.create_dataset(
            db,
            name=data.name,
            storage_type=data.storage_type,
            data_type=data.data_type,
            scenario_type=data.scenario_type,
            scenario_config=self._dump_scenario_config(scenario_config),
            save_path=save_path,
            description=data.description,
            count=0,
        )

        logger.info(f"Dataset created: {dataset.name}, path={save_path}")
        return self._to_response(dataset)

    async def get_dataset(self, db: AsyncSession, dataset_id: int) -> DatasetResponse:
        """获取数据集"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        return self._to_response(dataset)

    async def list_datasets(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        keyword: str = None
    ) -> tuple[List[DatasetResponse], int]:
        """分页查询数据集"""
        offset = (page - 1) * page_size
        items, total = await crud.get_datasets(db, offset, page_size, keyword)
        return [self._to_response(item) for item in items], total

    async def update_dataset(
        self,
        db: AsyncSession,
        dataset_id: int,
        data: DatasetUpdate
    ) -> DatasetResponse:
        """更新数据集"""
        update_data = data.model_dump(exclude_unset=True)
        if "scenario_type" in update_data or "scenario_config" in update_data:
            dataset = None
            data_type = update_data.get("data_type")
            scenario_type = update_data.get("scenario_type")
            if scenario_type is None or data_type is None:
                dataset = await crud.get_dataset_by_id(db, dataset_id)
                if not dataset:
                    raise NotFoundException(f"Dataset {dataset_id} not found")
            if scenario_type is None:
                scenario_type = dataset.scenario_type
            if data_type is None:
                data_type = dataset.data_type

            self._validate_dataset_type_and_scenario(data_type, scenario_type)

            scenario_config = self._prepare_scenario_config(
                data_type,
                scenario_type,
                update_data.get("scenario_config"),
            )
            update_data["scenario_config"] = self._dump_scenario_config(
                scenario_config)

        dataset = await crud.update_dataset(db, dataset_id, **update_data)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        return self._to_response(dataset)

    async def delete_dataset(self, db: AsyncSession, dataset_id: int) -> bool:
        """删除数据集"""
        # 获取数据集
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        # TODO: 可选择是否删除 S3 文件

        # 软删除
        return await crud.delete_dataset(db, dataset_id)

    async def list_sample_items(
        self,
        db: AsyncSession,
        dataset_id: int,
        page: int = 1,
        page_size: int = 100,
        item_type: Optional[str] = None,
    ) -> tuple[list[SampleItemResponse], int]:
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        offset = (page - 1) * page_size
        items, total = await crud.get_sample_items(db, dataset_id, offset, page_size, item_type)
        return [await self._to_sample_response(db, item) for item in items], total

    async def create_sample_item(
        self,
        db: AsyncSession,
        dataset_id: int,
        data: SampleItemCreate,
    ) -> SampleItemResponse:
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        item_key = data.item_key.strip()
        if await crud.get_sample_item_by_key(db, dataset_id, item_key):
            raise BadRequestException(f"Sample item `{item_key}` already exists")

        item = await crud.create_sample_item(
            db,
            dataset_id=dataset_id,
            asset_id=None,
            item_type=data.item_type.strip(),
            item_key=item_key,
            locator=self._dump_json(data.locator),
            payload=self._dump_json(data.payload),
            sort_order=0,
        )
        await crud.update_dataset_count(db, dataset_id, await crud.get_sample_item_count(db, dataset_id))
        return await self._to_sample_response(db, item)

    async def update_sample_item(
        self,
        db: AsyncSession,
        dataset_id: int,
        sample_item_id: int,
        data: SampleItemUpdate,
    ) -> SampleItemResponse:
        item = await crud.get_sample_item_by_id(db, sample_item_id)
        if not item or item.dataset_id != dataset_id:
            raise NotFoundException(f"Sample item {sample_item_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        if "item_key" in update_data and update_data["item_key"]:
            item_key = update_data["item_key"].strip()
            existing = await crud.get_sample_item_by_key(db, dataset_id, item_key)
            if existing and existing.id != sample_item_id:
                raise BadRequestException(f"Sample item `{item_key}` already exists")
            update_data["item_key"] = item_key
        if "locator" in update_data:
            update_data["locator"] = self._dump_json(update_data["locator"])
        if "payload" in update_data:
            update_data["payload"] = self._dump_json(update_data["payload"])

        updated = await crud.update_sample_item(db, sample_item_id, **update_data)
        if not updated:
            raise NotFoundException(f"Sample item {sample_item_id} not found")
        return await self._to_sample_response(db, updated)

    async def delete_sample_item(
        self,
        db: AsyncSession,
        dataset_id: int,
        sample_item_id: int,
    ) -> bool:
        item = await crud.get_sample_item_by_id(db, sample_item_id)
        if not item or item.dataset_id != dataset_id:
            raise NotFoundException(f"Sample item {sample_item_id} not found")
        deleted = await crud.delete_sample_item(db, sample_item_id)
        await crud.update_dataset_count(db, dataset_id, await crud.get_sample_item_count(db, dataset_id))
        return deleted

    async def upload_files(
        self,
        db: AsyncSession,
        dataset_id: int,
        files: List[UploadFile]
    ) -> int:
        """上传文件到数据集，支持压缩包自动解压"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        uploaded_count = 0

        for file in files:
            try:
                content = await file.read()
                filename = file.filename or "unknown"

                if dataset.scenario_type == DatasetScenarioType.DPO_PREFERENCE:
                    imported_count = await self._import_dpo_file(db, dataset, content, filename)
                    uploaded_count += imported_count
                    continue

                # 检查是否为压缩包
                if self._is_archive(filename):
                    count = await self._extract_and_upload(
                        db, dataset, content, filename
                    )
                    uploaded_count += count
                else:
                    # 普通文件直接上传
                    file_key = f"{dataset.save_path}/{filename}"
                    mime_type = file.content_type or mimetypes.guess_type(filename)[0]
                    await self.s3.put_file(
                        file_key, content,
                        bucket_type="datasets",
                        content_type=mime_type,
                    )
                    await self._create_asset_backed_sample(
                        db,
                        dataset,
                        filename,
                        file_key,
                        mime_type,
                        len(content),
                    )
                    uploaded_count += 1

            except Exception as e:
                logger.error(f"Failed to upload file {file.filename}: {e}")
                continue

        # 更新样本数量
        new_count = await crud.get_sample_item_count(db, dataset_id)
        await crud.update_dataset_count(db, dataset_id, new_count)

        logger.info(f"Uploaded {uploaded_count} files to dataset {dataset_id}")
        return uploaded_count

    def _is_archive(self, filename: str) -> bool:
        """检查文件是否为压缩包"""
        lower = filename.lower()
        for ext in ARCHIVE_EXTENSIONS:
            if lower.endswith(ext):
                return True
        return False

    async def _create_asset_backed_sample(
        self,
        db: AsyncSession,
        dataset,
        file_name: str,
        save_path: str,
        mime_type: Optional[str],
        size_bytes: int,
    ):
        asset = await crud.create_asset(
            db,
            dataset_id=dataset.id,
            asset_type=self._infer_asset_type(file_name, mime_type),
            file_name=file_name,
            save_path=save_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            meta_json=None,
        )
        return await crud.create_sample_item(
            db,
            dataset_id=dataset.id,
            asset_id=asset.id,
            item_type=self._infer_sample_item_type(dataset, file_name, mime_type),
            item_key=file_name,
            locator=self._dump_json({"asset_path": save_path}),
            payload=None,
            sort_order=0,
        )

    def _infer_asset_type(self, file_name: str, mime_type: Optional[str]) -> str:
        mime = (mime_type or "").lower()
        ext = os.path.splitext(file_name.lower())[1]
        if mime.startswith("image/") or ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".svg"}:
            return "image"
        if mime.startswith("video/") or ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
            return "video"
        if mime.startswith("audio/") or ext in {".mp3", ".wav", ".ogg", ".flac", ".aac"}:
            return "audio"
        if mime.startswith("text/") or ext in {".txt", ".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
            return "text"
        return "file"

    def _infer_sample_item_type(self, dataset, file_name: str, mime_type: Optional[str]) -> str:
        if dataset.scenario_type in {DatasetScenarioType.LLM_CONVERSATION, DatasetScenarioType.MLLM_CONVERSATION}:
            return "conversation"
        if dataset.scenario_type == DatasetScenarioType.DPO_PREFERENCE:
            return "preference"

        asset_type = self._infer_asset_type(file_name, mime_type)
        if asset_type in {"image", "text", "video", "audio"}:
            return asset_type
        return "file"

    def _prepare_scenario_config(
        self,
        data_type: int,
        scenario_type: int,
        config: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Normalize scenario config before storing it as JSON."""
        if scenario_type == DatasetScenarioType.NORMAL:
            return config

        if scenario_type == DatasetScenarioType.AERIAL_STITCH:
            if data_type != DataType.IMAGE:
                raise BadRequestException("Aerial stitch scenario only supports image datasets")
            if not config:
                return DEFAULT_AERIAL_STITCH_CONFIG
            normalized = json.loads(json.dumps(DEFAULT_AERIAL_STITCH_CONFIG))
            for key, value in config.items():
                if isinstance(value, dict) and isinstance(normalized.get(key), dict):
                    normalized[key].update(value)
                else:
                    normalized[key] = value
            return normalized

        if scenario_type == DatasetScenarioType.LLM_CONVERSATION:
            if data_type != DataType.TEXT:
                raise BadRequestException("LLM conversation scenario only supports text datasets")
            if not config:
                return DEFAULT_LLM_CONVERSATION_CONFIG
            normalized = json.loads(json.dumps(DEFAULT_LLM_CONVERSATION_CONFIG))
            for key, value in config.items():
                if isinstance(value, dict) and isinstance(normalized.get(key), dict):
                    normalized[key].update(value)
                else:
                    normalized[key] = value
            return normalized

        if scenario_type == DatasetScenarioType.MLLM_CONVERSATION:
            if data_type != DataType.IMAGE:
                raise BadRequestException("MLLM conversation scenario only supports image datasets")
            if not config:
                return DEFAULT_MLLM_CONVERSATION_CONFIG
            normalized = json.loads(json.dumps(DEFAULT_MLLM_CONVERSATION_CONFIG))
            for key, value in config.items():
                if isinstance(value, dict) and isinstance(normalized.get(key), dict):
                    normalized[key].update(value)
                else:
                    normalized[key] = value
            return normalized

        if scenario_type == DatasetScenarioType.DPO_PREFERENCE:
            if data_type != DataType.TEXT:
                raise BadRequestException("DPO preference scenario only supports text datasets")
            if not config:
                return DEFAULT_DPO_PREFERENCE_CONFIG
            normalized = json.loads(json.dumps(DEFAULT_DPO_PREFERENCE_CONFIG))
            for key, value in config.items():
                if isinstance(value, dict) and isinstance(normalized.get(key), dict):
                    normalized[key].update(value)
                else:
                    normalized[key] = value
            return normalized

        raise BadRequestException(
            f"Unsupported dataset scenario_type: {scenario_type}")

    def _dump_scenario_config(self, config: Optional[Dict[str, Any]]) -> Optional[str]:
        if config is None:
            return None
        return json.dumps(config, ensure_ascii=False)

    def _dump_json(self, payload: Optional[Dict[str, Any]]) -> Optional[str]:
        if payload is None:
            return None
        return json.dumps(payload, ensure_ascii=False)

    def _load_json(self, raw_payload) -> Optional[Dict[str, Any]]:
        if not raw_payload:
            return None
        if isinstance(raw_payload, dict):
            return raw_payload
        try:
            parsed = json.loads(raw_payload)
        except (TypeError, json.JSONDecodeError):
            logger.warning("Invalid JSON payload, returning empty value")
            return None
        return parsed if isinstance(parsed, dict) else None

    def _load_scenario_config(self, raw_config) -> Optional[Dict[str, Any]]:
        if not raw_config:
            return None
        if isinstance(raw_config, dict):
            return raw_config
        try:
            parsed = json.loads(raw_config)
        except (TypeError, json.JSONDecodeError):
            logger.warning(
                "Invalid dataset scenario_config JSON, returning empty config")
            return None
        return parsed if isinstance(parsed, dict) else None

    def _to_response(self, dataset) -> DatasetResponse:
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            storage_type=dataset.storage_type,
            data_type=dataset.data_type,
            scenario_type=dataset.scenario_type or DatasetScenarioType.NORMAL,
            scenario_config=self._load_scenario_config(dataset.scenario_config),
            save_path=dataset.save_path,
            count=dataset.count or 0,
            description=dataset.description,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    async def _to_sample_response(self, db: AsyncSession, item) -> SampleItemResponse:
        asset_response = None
        if item.asset_id:
            asset = await crud.get_asset_by_id(db, item.asset_id)
            if asset:
                asset_response = AssetResponse.model_validate(asset)
        return SampleItemResponse(
            id=item.id,
            dataset_id=item.dataset_id,
            asset_id=item.asset_id,
            item_type=item.item_type,
            item_key=item.item_key,
            locator=self._load_json(item.locator),
            payload=self._load_json(item.payload),
            sort_order=item.sort_order or 0,
            created_at=item.created_at,
            updated_at=item.updated_at,
            asset=asset_response,
        )

    async def _get_asset_backed_sample(self, db: AsyncSession, dataset_id: int, sample_item_id: int):
        item = await crud.get_sample_item_by_id(db, sample_item_id)
        if not item or item.dataset_id != dataset_id:
            raise NotFoundException(f"Sample item {sample_item_id} not found")
        if not item.asset_id:
            raise BadRequestException("Sample item is not backed by an asset")
        asset = await crud.get_asset_by_id(db, item.asset_id)
        if not asset:
            raise NotFoundException(f"Asset for sample item {sample_item_id} not found")
        return item, asset

    def _validate_dataset_type_and_scenario(self, data_type: int, scenario_type: int) -> None:
        if scenario_type == DatasetScenarioType.AERIAL_STITCH and data_type != DataType.IMAGE:
            raise BadRequestException("Aerial stitch scenario only supports image datasets")
        if scenario_type == DatasetScenarioType.LLM_CONVERSATION and data_type != DataType.TEXT:
            raise BadRequestException("LLM conversation scenario only supports text datasets")
        if scenario_type == DatasetScenarioType.MLLM_CONVERSATION and data_type != DataType.IMAGE:
            raise BadRequestException("MLLM conversation scenario only supports image datasets")
        if scenario_type == DatasetScenarioType.DPO_PREFERENCE and data_type != DataType.TEXT:
            raise BadRequestException("DPO preference scenario only supports text datasets")

    async def _extract_and_upload(
        self,
        db: AsyncSession,
        dataset,
        content: bytes,
        archive_name: str,
    ) -> int:
        """解压压缩包并上传内部文件"""
        extracted_count = 0
        lower = archive_name.lower()

        if lower.endswith('.zip'):
            extracted_count = await self._extract_zip(
                db, dataset, content
            )
        elif lower.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz')):
            extracted_count = await self._extract_tar(
                db, dataset, content, archive_name
            )
        else:
            logger.warning(f"Unsupported archive format: {archive_name}")

        logger.info(f"Extracted {extracted_count} files from {archive_name}")
        return extracted_count

    async def _extract_zip(
        self,
        db: AsyncSession,
        dataset,
        content: bytes,
    ) -> int:
        """解压 ZIP 文件"""
        count = 0
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for info in zf.infolist():
                    # 跳过目录和系统文件
                    if info.is_dir():
                        continue
                    inner_name = info.filename
                    if self._should_skip(inner_name):
                        continue

                    # 取文件名（去掉目录前缀）
                    base_name = os.path.basename(inner_name)
                    if not base_name:
                        continue

                    file_data = zf.read(info)
                    file_key = f"{dataset.save_path}/{base_name}"
                    mime_type = mimetypes.guess_type(base_name)[0]

                    await self.s3.put_file(
                        file_key,
                        file_data,
                        bucket_type="datasets",
                        content_type=mime_type,
                    )
                    await self._create_asset_backed_sample(db, dataset, base_name, file_key, mime_type, len(file_data))
                    count += 1
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP file")
            raise BadRequestException("Invalid ZIP file")
        return count

    async def _extract_tar(
        self,
        db: AsyncSession,
        dataset,
        content: bytes,
        archive_name: str,
    ) -> int:
        """解压 TAR/TAR.GZ/TAR.BZ2/TAR.XZ 文件"""
        count = 0
        lower = archive_name.lower()

        # 确定压缩模式
        if lower.endswith(('.tar.gz', '.tgz')):
            mode = 'r:gz'
        elif lower.endswith(('.tar.bz2', '.tbz2')):
            mode = 'r:bz2'
        elif lower.endswith(('.tar.xz', '.txz')):
            mode = 'r:xz'
        else:
            mode = 'r:'

        try:
            with tarfile.open(fileobj=io.BytesIO(content), mode=mode) as tf:
                for member in tf.getmembers():
                    if not member.isfile():
                        continue
                    if self._should_skip(member.name):
                        continue

                    base_name = os.path.basename(member.name)
                    if not base_name:
                        continue

                    f = tf.extractfile(member)
                    if f is None:
                        continue

                    file_data = f.read()
                    file_key = f"{dataset.save_path}/{base_name}"
                    mime_type = mimetypes.guess_type(base_name)[0]

                    await self.s3.put_file(
                        file_key,
                        file_data,
                        bucket_type="datasets",
                        content_type=mime_type,
                    )
                    await self._create_asset_backed_sample(db, dataset, base_name, file_key, mime_type, len(file_data))
                    count += 1
        except (tarfile.TarError, Exception) as e:
            logger.error(f"Failed to extract tar: {e}")
            raise BadRequestException(f"Invalid archive file: {e}")
        return count

    @staticmethod
    def _should_skip(name: str) -> bool:
        """检查是否应跳过的文件"""
        base = os.path.basename(name)
        for prefix in SKIP_PREFIXES:
            if name.startswith(prefix) or base.startswith(prefix):
                return True
        return False

    async def preview_sample(
        self,
        db: AsyncSession,
        dataset_id: int,
        sample_item_id: int,
    ) -> FilePreviewResponse:
        """预览样本关联资源（生成预签名 URL）"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        item, asset = await self._get_asset_backed_sample(db, dataset_id, sample_item_id)
        if not asset or not asset.save_path:
            raise NotFoundException(f"Asset for sample item {sample_item_id} not found")

        # 检查文件是否存在
        exists = await self.s3.file_exists(asset.save_path, bucket_type="datasets")
        if not exists:
            raise NotFoundException(f"Asset for sample item {sample_item_id} not found")

        # 生成预签名 URL
        presigned_url = await self.s3.get_presigned_url(asset.save_path, bucket_type="datasets")

        return FilePreviewResponse(
            file_name=asset.file_name or item.item_key,
            presigned_url=presigned_url,
        )

    async def get_sample_content(
        self,
        db: AsyncSession,
        dataset_id: int,
        sample_item_id: int,
    ) -> FileContentResponse:
        """读取样本关联文本资源内容"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        if dataset.data_type != DataType.TEXT:
            raise BadRequestException("Only text datasets support reading file content")

        item, asset = await self._get_asset_backed_sample(db, dataset_id, sample_item_id)
        if not asset or not asset.save_path:
            raise NotFoundException(f"Asset for sample item {sample_item_id} not found")

        raw_bytes = await self.s3.get_file(asset.save_path, bucket_type="datasets")
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("utf-8", errors="replace")

        return FileContentResponse(file_name=asset.file_name or item.item_key, content=content)

    async def _import_dpo_file(
        self,
        db: AsyncSession,
        dataset,
        content: bytes,
        file_name: str,
    ) -> int:
        ext = os.path.splitext(file_name.lower())[1]
        if ext != ".jsonl":
            raise BadRequestException("DPO preference dataset only supports .jsonl import")

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BadRequestException(f"Failed to decode JSONL file as utf-8: {exc}") from exc

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise BadRequestException("DPO JSONL file is empty")

        validated_items: list[dict[str, Any]] = []
        seen_item_keys: set[str] = set()
        for index, line in enumerate(lines, start=1):
            try:
                raw_item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BadRequestException(f"Invalid JSONL at line {index}: {exc}") from exc
            item = self._normalize_dpo_payload(raw_item, line_no=index)
            item_key = item["item_key"]
            if item_key in seen_item_keys:
                raise BadRequestException(f"Duplicate item_key `{item_key}` at line {index}")
            if await crud.get_sample_item_by_key(db, dataset.id, item_key):
                raise BadRequestException(f"Sample item `{item_key}` already exists")
            seen_item_keys.add(item_key)
            validated_items.append(item)

        for item in validated_items:
            await crud.create_sample_item(
                db,
                dataset_id=dataset.id,
                asset_id=None,
                item_type="preference",
                item_key=item["item_key"],
                locator=None,
                payload=self._dump_json(item["payload"]),
                sort_order=0,
            )

        await crud.update_dataset_count(db, dataset.id, await crud.get_sample_item_count(db, dataset.id))
        return len(validated_items)

    def _normalize_dpo_payload(self, raw_item: Any, line_no: int) -> dict[str, Any]:
        if not isinstance(raw_item, dict):
            raise BadRequestException(f"DPO JSONL line {line_no} must be an object")

        item_key = str(raw_item.get("item_key") or "").strip()
        if not item_key:
            raise BadRequestException(f"DPO JSONL line {line_no} missing item_key")

        prompt = raw_item.get("prompt")
        if not isinstance(prompt, dict):
            raise BadRequestException(f"DPO JSONL line {line_no} missing prompt object")

        messages = prompt.get("messages")
        if not isinstance(messages, list) or not messages:
            raise BadRequestException(f"DPO JSONL line {line_no} prompt.messages must be a non-empty list")

        normalized_messages: list[dict[str, str]] = []
        has_user_message = False
        for message in messages:
            if not isinstance(message, dict):
                raise BadRequestException(f"DPO JSONL line {line_no} has invalid prompt message")
            role = str(message.get("role") or "").strip()
            content = str(message.get("content") or "")
            if role not in {"system", "user", "assistant"}:
                raise BadRequestException(f"DPO JSONL line {line_no} has unsupported prompt role `{role}`")
            if role == "user":
                has_user_message = True
            normalized_messages.append({
                "role": role,
                "content": content,
            })
        if not has_user_message:
            raise BadRequestException(f"DPO JSONL line {line_no} prompt.messages must contain at least one user message")

        responses = raw_item.get("responses")
        if not isinstance(responses, list) or len(responses) != 2:
            raise BadRequestException(f"DPO JSONL line {line_no} responses must contain exactly 2 items")

        normalized_responses: list[dict[str, Any]] = []
        seen_response_ids: set[str] = set()
        contents: list[str] = []
        for response in responses:
            if not isinstance(response, dict):
                raise BadRequestException(f"DPO JSONL line {line_no} has invalid response item")
            response_id = str(response.get("response_id") or "").strip()
            if not response_id:
                raise BadRequestException(f"DPO JSONL line {line_no} response_id is required")
            if response_id in seen_response_ids:
                raise BadRequestException(f"DPO JSONL line {line_no} duplicate response_id `{response_id}`")
            seen_response_ids.add(response_id)
            content = response.get("content")
            if not isinstance(content, str):
                raise BadRequestException(f"DPO JSONL line {line_no} response.content must be a string")
            contents.append(content.strip())
            metadata = response.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                raise BadRequestException(f"DPO JSONL line {line_no} response.metadata must be an object")
            normalized_responses.append({
                "response_id": response_id,
                "content": content,
                "model_id": str(response.get("model_id") or "").strip() or None,
                "metadata": metadata if isinstance(metadata, dict) else {},
            })

        if not any(contents):
            raise BadRequestException(f"DPO JSONL line {line_no} responses cannot both be empty")
        if contents[0] == contents[1]:
            raise BadRequestException(f"DPO JSONL line {line_no} responses cannot be identical")

        reference = raw_item.get("reference")
        if reference is not None and not isinstance(reference, dict):
            raise BadRequestException(f"DPO JSONL line {line_no} reference must be an object")
        tags = raw_item.get("tags")
        if tags is not None and (not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags)):
            raise BadRequestException(f"DPO JSONL line {line_no} tags must be a string array")

        return {
            "item_key": item_key,
            "payload": {
                "version": 1,
                "format": "dpo_preference_sample",
                "prompt": {
                    "system_prompt": str(prompt.get("system_prompt") or ""),
                    "messages": normalized_messages,
                },
                "responses": normalized_responses,
                "reference": reference if isinstance(reference, dict) else None,
                "tags": tags if isinstance(tags, list) else [],
                "imported_at": datetime.utcnow().isoformat(),
            },
        }


def get_dataset_service() -> DatasetService:
    """获取数据集服务"""
    return DatasetService()
