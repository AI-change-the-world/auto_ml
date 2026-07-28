"""MQ consumers that persist batch sandbox events and results."""
from app.config.database import AsyncSessionLocal
from app.modules.ai_pipeline.batch_service import get_batch_annotation_service


async def handle_pipeline_batch_progress(message) -> None:
    async with AsyncSessionLocal() as db:
        await get_batch_annotation_service().handle_worker_progress(
            db,
            message.model_dump(mode="json"),
        )


async def handle_pipeline_batch_result(message) -> None:
    async with AsyncSessionLocal() as db:
        await get_batch_annotation_service().handle_worker_result(
            db,
            message.model_dump(mode="json"),
        )
