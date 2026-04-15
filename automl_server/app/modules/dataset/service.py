"""
数据集业务逻辑
"""
import io
import os
import uuid
import zipfile
import tarfile
from typing import List, Optional

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException, BadRequestException
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import DatasetCreate, DatasetUpdate, DatasetResponse, FilePreviewResponse

# 支持的压缩包扩展名
ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.tar.gz',
                      '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz'}
# 跳过的文件/目录前缀
SKIP_PREFIXES = ('__MACOSX/', '.', '._')


class DatasetService:
    """数据集服务"""

    def __init__(self):
        self.s3 = get_s3_delegate()

    async def create_dataset(self, db: AsyncSession, data: DatasetCreate) -> DatasetResponse:
        """创建数据集"""
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
            save_path=save_path,
            description=data.description,
            count=0,
        )

        logger.info(f"Dataset created: {dataset.name}, path={save_path}")
        return DatasetResponse.model_validate(dataset)

    async def get_dataset(self, db: AsyncSession, dataset_id: int) -> DatasetResponse:
        """获取数据集"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        return DatasetResponse.model_validate(dataset)

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
        return [DatasetResponse.model_validate(item) for item in items], total

    async def update_dataset(
        self,
        db: AsyncSession,
        dataset_id: int,
        data: DatasetUpdate
    ) -> DatasetResponse:
        """更新数据集"""
        update_data = data.model_dump(exclude_unset=True)
        dataset = await crud.update_dataset(db, dataset_id, **update_data)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")
        return DatasetResponse.model_validate(dataset)

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
