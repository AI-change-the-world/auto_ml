"""
数据集业务逻辑
"""
import uuid
from typing import List, Optional

from fastapi import UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException, BadRequestException
from app.utils.s3_delegate import get_s3_delegate
from . import crud
from .schemas import DatasetCreate, DatasetUpdate, DatasetResponse, FilePreviewResponse


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
        """上传文件到数据集"""
        dataset = await crud.get_dataset_by_id(db, dataset_id)
        if not dataset:
            raise NotFoundException(f"Dataset {dataset_id} not found")

        uploaded_count = 0

        for file in files:
            try:
                # 读取文件内容
                content = await file.read()

                # 上传到 S3
                file_key = f"{dataset.save_path}/{file.filename}"
                await self.s3.put_file(
                    file_key,
                    content,
                    bucket_type="datasets",
                    content_type=file.content_type,
                )

                # 保存文件记录
                await crud.create_dataset_file(
                    db,
                    dataset_id=dataset_id,
                    file_name=file.filename,
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


# 服务单例
_service: Optional[DatasetService] = None


def get_dataset_service() -> DatasetService:
    """获取数据集服务"""
    global _service
    if _service is None:
        _service = DatasetService()
    return _service
