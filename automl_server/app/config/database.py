"""
数据库配置
使用 SQLAlchemy 2.0 AsyncIO
"""
from typing import AsyncGenerator
from sqlalchemy import select, text

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from .settings import get_settings

# 创建异步引擎
settings = get_settings()
engine = create_async_engine(
    settings.database.url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建表）"""
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.db.models import (
            Dataset, DatasetFile, Annotation, AnnotationFile,
            Task, TaskLog, TaskSource, BaseModels,
            AvailableModel, ModelInferenceLog
        )
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_schema_compatibility(conn)
        logger.info("Database tables created successfully")

    await seed_base_models()


async def _ensure_schema_compatibility(conn):
    """Apply lightweight additive schema fixes for existing dev databases."""
    if conn.dialect.name != "mysql":
        return
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'available_model' "
            "AND COLUMN_NAME = 'onnx_model_path'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE available_model "
                "ADD COLUMN onnx_model_path VARCHAR(512) DEFAULT NULL COMMENT 'ONNX模型路径' "
                "AFTER model_path"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'available_model' "
            "AND COLUMN_NAME = 'class_names'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE available_model "
                "ADD COLUMN class_names TEXT DEFAULT NULL COMMENT '类别名称 JSON' "
                "AFTER model_type"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'available_model' "
            "AND COLUMN_NAME = 'deployed_at'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE available_model "
                "ADD COLUMN deployed_at DATETIME DEFAULT NULL COMMENT '最近一次部署时间' "
                "AFTER deployment_device"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'available_model' "
            "AND COLUMN_NAME = 'inference_count'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE available_model "
                "ADD COLUMN inference_count BIGINT NOT NULL DEFAULT 0 COMMENT '累计推理调用次数' "
                "AFTER deployed_at"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'available_model' "
            "AND COLUMN_NAME = 'last_inference_at'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE available_model "
                "ADD COLUMN last_inference_at DATETIME DEFAULT NULL COMMENT '最近一次推理时间' "
                "AFTER inference_count"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'dataset' "
            "AND COLUMN_NAME = 'scenario_type'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE dataset "
                "ADD COLUMN scenario_type INT DEFAULT 0 COMMENT '场景类型: 0=普通, 1=无人机航拍/拼接' "
                "AFTER data_type"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'dataset' "
            "AND COLUMN_NAME = 'scenario_config'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "ALTER TABLE dataset "
                "ADD COLUMN scenario_config TEXT DEFAULT NULL COMMENT '场景配置 JSON' "
                "AFTER scenario_type"
            )
        )
    await conn.execute(
        text(
            "UPDATE available_model am "
            "JOIN task t ON am.task_id = t.id AND t.is_deleted = 0 "
            "JOIN annotation a ON t.annotation_id = a.id AND a.is_deleted = 0 "
            "SET am.class_names = a.classes "
            "WHERE (am.class_names IS NULL OR am.class_names = '') "
            "AND a.classes IS NOT NULL AND a.classes <> ''"
        )
    )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'task_source'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "CREATE TABLE task_source ("
                "id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID', "
                "task_id BIGINT NOT NULL COMMENT '任务ID', "
                "dataset_id BIGINT NOT NULL COMMENT '数据集ID', "
                "annotation_id BIGINT NOT NULL COMMENT '标注ID', "
                "source_order INT DEFAULT 0 COMMENT '来源顺序', "
                "source_name VARCHAR(255) DEFAULT NULL COMMENT '来源名称快照', "
                "created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间', "
                "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间', "
                "is_deleted TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记', "
                "PRIMARY KEY (id), "
                "KEY idx_task_source_task_id (task_id), "
                "KEY idx_task_source_dataset_id (dataset_id), "
                "KEY idx_task_source_annotation_id (annotation_id)"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务训练数据源'"
            )
        )
    result = await conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'model_inference_log'"
        )
    )
    if result.scalar_one() == 0:
        await conn.execute(
            text(
                "CREATE TABLE model_inference_log ("
                "id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID', "
                "model_id BIGINT NOT NULL COMMENT '模型ID', "
                "request_type VARCHAR(32) DEFAULT NULL COMMENT '请求方式: file/base64', "
                "success TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否成功', "
                "duration_ms INT DEFAULT NULL COMMENT '推理耗时毫秒', "
                "result_count INT NOT NULL DEFAULT 0 COMMENT '返回结果数量', "
                "image_width INT DEFAULT NULL COMMENT '图像宽度', "
                "image_height INT DEFAULT NULL COMMENT '图像高度', "
                "error_message TEXT DEFAULT NULL COMMENT '错误信息', "
                "client_ip VARCHAR(64) DEFAULT NULL COMMENT '客户端IP', "
                "created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间', "
                "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间', "
                "is_deleted TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记', "
                "PRIMARY KEY (id), "
                "KEY idx_model_inference_log_model_id (model_id), "
                "KEY idx_model_inference_log_created_at (created_at)"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型推理调用记录'"
            )
        )


BASE_MODEL_SEEDS = [
    ("yolov8n.pt", "detection", "YOLOv8 nano detection baseline", "yolov8n.pt"),
    ("yolov8s.pt", "detection", "YOLOv8 small detection baseline", "yolov8s.pt"),
    ("yolov8m.pt", "detection", "YOLOv8 medium detection baseline", "yolov8m.pt"),
    ("yolov8l.pt", "detection", "YOLOv8 large detection baseline", "yolov8l.pt"),
    ("yolov8x.pt", "detection", "YOLOv8 extra-large detection baseline", "yolov8x.pt"),
    ("yolov8n-obb.pt", "detection_obb", "YOLOv8 nano OBB detection baseline", "yolov8n-obb.pt"),
    ("yolov8s-obb.pt", "detection_obb", "YOLOv8 small OBB detection baseline", "yolov8s-obb.pt"),
    ("yolov8m-obb.pt", "detection_obb", "YOLOv8 medium OBB detection baseline", "yolov8m-obb.pt"),
    ("yolov8l-obb.pt", "detection_obb", "YOLOv8 large OBB detection baseline", "yolov8l-obb.pt"),
    ("yolov8x-obb.pt", "detection_obb", "YOLOv8 extra-large OBB detection baseline", "yolov8x-obb.pt"),
    ("yolo11n.pt", "detection", "YOLO11 nano detection baseline", "yolo11n.pt"),
    ("yolo11s.pt", "detection", "YOLO11 small detection baseline", "yolo11s.pt"),
    ("yolo11m.pt", "detection", "YOLO11 medium detection baseline", "yolo11m.pt"),
    ("yolo11l.pt", "detection", "YOLO11 large detection baseline", "yolo11l.pt"),
    ("yolo11x.pt", "detection", "YOLO11 extra-large detection baseline", "yolo11x.pt"),
    ("yolo11n-obb.pt", "detection_obb", "YOLO11 nano OBB detection baseline", "yolo11n-obb.pt"),
    ("yolo11s-obb.pt", "detection_obb", "YOLO11 small OBB detection baseline", "yolo11s-obb.pt"),
    ("yolo11m-obb.pt", "detection_obb", "YOLO11 medium OBB detection baseline", "yolo11m-obb.pt"),
    ("yolo11l-obb.pt", "detection_obb", "YOLO11 large OBB detection baseline", "yolo11l-obb.pt"),
    ("yolo11x-obb.pt", "detection_obb", "YOLO11 extra-large OBB detection baseline", "yolo11x-obb.pt"),
    ("yolov8n-cls.pt", "classification", "YOLOv8 nano classification baseline", "yolov8n-cls.pt"),
    ("yolov8s-cls.pt", "classification", "YOLOv8 small classification baseline", "yolov8s-cls.pt"),
    ("yolov8m-cls.pt", "classification", "YOLOv8 medium classification baseline", "yolov8m-cls.pt"),
    ("yolov8l-cls.pt", "classification", "YOLOv8 large classification baseline", "yolov8l-cls.pt"),
    ("yolov8x-cls.pt", "classification", "YOLOv8 extra-large classification baseline", "yolov8x-cls.pt"),
    ("yolo11n-cls.pt", "classification", "YOLO11 nano classification baseline", "yolo11n-cls.pt"),
    ("yolo11s-cls.pt", "classification", "YOLO11 small classification baseline", "yolo11s-cls.pt"),
    ("yolo11m-cls.pt", "classification", "YOLO11 medium classification baseline", "yolo11m-cls.pt"),
    ("yolo11l-cls.pt", "classification", "YOLO11 large classification baseline", "yolo11l-cls.pt"),
    ("yolo11x-cls.pt", "classification", "YOLO11 extra-large classification baseline", "yolo11x-cls.pt"),
    ("yolov8n-seg.pt", "segmentation", "YOLOv8 nano segmentation baseline", "yolov8n-seg.pt"),
    ("yolov8s-seg.pt", "segmentation", "YOLOv8 small segmentation baseline", "yolov8s-seg.pt"),
    ("yolov8m-seg.pt", "segmentation", "YOLOv8 medium segmentation baseline", "yolov8m-seg.pt"),
    ("yolov8l-seg.pt", "segmentation", "YOLOv8 large segmentation baseline", "yolov8l-seg.pt"),
    ("yolov8x-seg.pt", "segmentation", "YOLOv8 extra-large segmentation baseline", "yolov8x-seg.pt"),
    ("yolo11n-seg.pt", "segmentation", "YOLO11 nano segmentation baseline", "yolo11n-seg.pt"),
    ("yolo11s-seg.pt", "segmentation", "YOLO11 small segmentation baseline", "yolo11s-seg.pt"),
    ("yolo11m-seg.pt", "segmentation", "YOLO11 medium segmentation baseline", "yolo11m-seg.pt"),
    ("yolo11l-seg.pt", "segmentation", "YOLO11 large segmentation baseline", "yolo11l-seg.pt"),
    ("yolo11x-seg.pt", "segmentation", "YOLO11 extra-large segmentation baseline", "yolo11x-seg.pt"),
]


async def seed_base_models():
    from app.db.models import BaseModels

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BaseModels.name).where(BaseModels.is_deleted == False)
        )
        existing = set(result.scalars().all())
        created = 0

        for name, model_type, description, save_path in BASE_MODEL_SEEDS:
            if name in existing:
                continue
            session.add(
                BaseModels(
                    name=name,
                    model_type=model_type,
                    description=description,
                    save_path=save_path,
                )
            )
            created += 1

        if created:
            await session.commit()
            logger.info(f"Seeded {created} base models")
