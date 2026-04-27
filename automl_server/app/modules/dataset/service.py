"""
数据集业务逻辑
"""
import io
import json
import os
import uuid
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
from .schemas import DatasetCreate, DatasetUpdate, DatasetResponse, FilePreviewResponse, FileContentResponse

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

                # 检查是否为压缩包
                if self._is_archive(filename):
                    count = await self._extract_and_upload(
                        db, dataset, content, filename
                    )
                    uploaded_count += count
                else:
                    # 普通文件直接上传
                    file_key = f"{dataset.save_path}/{filename}"
                    await self.s3.put_file(
                        file_key, content,
                        bucket_type="datasets",
                        content_type=file.content_type,
                    )
                    await crud.create_dataset_file(
                        db,
                        dataset_id=dataset_id,
                        file_name=filename,
                        save_path=file_key,
                    )
                    uploaded_count += 1

            except Exception as e:
                logger.error(f"Failed to upload file {file.filename}: {e}")
                continue

        # 更新文件数量
        new_count = await crud.get_dataset_file_count(db, dataset_id)
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

        raise BadRequestException(
            f"Unsupported dataset scenario_type: {scenario_type}")

    def _dump_scenario_config(self, config: Optional[Dict[str, Any]]) -> Optional[str]:
        if config is None:
            return None
        return json.dumps(config, ensure_ascii=False)

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

    def _validate_dataset_type_and_scenario(self, data_type: int, scenario_type: int) -> None:
        if scenario_type == DatasetScenarioType.AERIAL_STITCH and data_type != DataType.IMAGE:
            raise BadRequestException("Aerial stitch scenario only supports image datasets")
        if scenario_type == DatasetScenarioType.LLM_CONVERSATION and data_type != DataType.TEXT:
            raise BadRequestException("LLM conversation scenario only supports text datasets")
        if scenario_type == DatasetScenarioType.MLLM_CONVERSATION and data_type != DataType.IMAGE:
            raise BadRequestException("MLLM conversation scenario only supports image datasets")

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

                    await self.s3.put_file(
                        file_key, file_data, bucket_type="datasets"
                    )
                    await crud.create_dataset_file(
                        db,
                        dataset_id=dataset.id,
                        file_name=base_name,
                        save_path=file_key,
                    )
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

                    await self.s3.put_file(
                        file_key, file_data, bucket_type="datasets"
                    )
                    await crud.create_dataset_file(
                        db,
                        dataset_id=dataset.id,
                        file_name=base_name,
                        save_path=file_key,
                    )
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

    async def get_files(
        self,
        db: AsyncSession,
        dataset_id: int,
        page: int = 1,
        page_size: int = 100
    ) -> tuple[list, int]:
        """获取数据集文件列表"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        offset = (page - 1) * page_size
        files, total = await crud.get_dataset_files(db, dataset_id, offset, page_size)
        return files, total

    async def preview_file(
        self,
        db: AsyncSession,
        dataset_id: int,
        file_name: str
    ) -> FilePreviewResponse:
        """预览文件（生成预签名 URL）"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        file_key = f"{dataset.save_path}/{file_name}"

        # 检查文件是否存在
        exists = await self.s3.file_exists(file_key, bucket_type="datasets")
        if not exists:
            raise NotFoundException(f"File {file_name} not found")

        # 生成预签名 URL
        presigned_url = await self.s3.get_presigned_url(file_key, bucket_type="datasets")

        return FilePreviewResponse(
            file_name=file_name,
            presigned_url=presigned_url,
        )

    async def get_file_content(
        self,
        db: AsyncSession,
        dataset_id: int,
        file_name: str,
    ) -> FileContentResponse:
        """读取文本文件内容"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        if dataset.data_type != DataType.TEXT:
            raise BadRequestException("Only text datasets support reading file content")

        file_record = await crud.get_dataset_file_by_name(db, dataset_id, file_name)
        if not file_record or not file_record.save_path:
            raise NotFoundException(f"File {file_name} not found")

        raw_bytes = await self.s3.get_file(file_record.save_path, bucket_type="datasets")
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("utf-8", errors="replace")

        return FileContentResponse(file_name=file_name, content=content)

    async def delete_file(
        self,
        db: AsyncSession,
        dataset_id: int,
        file_id: int,
    ) -> bool:
        """删除数据集中的单个文件"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        file_record = await crud.get_dataset_file_by_id(db, file_id)
        if not file_record or file_record.dataset_id != dataset_id:
            raise NotFoundException(
                f"File {file_id} not found in dataset {dataset_id}")

        # 从 S3 删除
        try:
            if file_record.save_path:
                await self.s3.delete_file(file_record.save_path, bucket_type="datasets")
        except Exception as e:
            logger.warning(
                f"Failed to delete S3 file {file_record.save_path}: {e}")

        # 软删除数据库记录
        await crud.delete_dataset_file(db, file_id)

        # 更新文件数量
        new_count = await crud.get_dataset_file_count(db, dataset_id)
        await crud.update_dataset_count(db, dataset_id, new_count)

        logger.info(f"Deleted file {file_id} from dataset {dataset_id}")
        return True

    async def batch_delete_files(
        self,
        db: AsyncSession,
        dataset_id: int,
        file_ids: list[int],
    ) -> int:
        """批量删除数据集文件"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        # 逐个删除 S3 文件
        for file_id in file_ids:
            file_record = await crud.get_dataset_file_by_id(db, file_id)
            if file_record and file_record.dataset_id == dataset_id and file_record.save_path:
                try:
                    await self.s3.delete_file(file_record.save_path, bucket_type="datasets")
                except Exception as e:
                    logger.warning(f"Failed to delete S3 file: {e}")

        # 批量软删除
        deleted = await crud.batch_delete_dataset_files(db, file_ids)

        # 更新文件数量
        new_count = await crud.get_dataset_file_count(db, dataset_id)
        await crud.update_dataset_count(db, dataset_id, new_count)

        logger.info(f"Batch deleted {deleted} files from dataset {dataset_id}")
        return deleted


def get_dataset_service() -> DatasetService:
    """获取数据集服务"""
    return DatasetService()
