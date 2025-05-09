import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from Aether import AetherRequest, AetherResponse, ResponseMeta
from base.logger import logger
from base.nacos_config import get_db
from yolo.response import PredictResults

router = APIRouter(
    prefix="/aether",
    tags=["aether"],
)


@router.post("")
async def handle_request(req: AetherRequest[dict], db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        if req.task == "label":
            from label.multi_label_image_annotate import annotation_multi_class_image
            logger.info(f"extra: {req.extra}")
            annotation_id = req.extra.get("annotation_id")
            res = annotation_multi_class_image(
                img=req.input.data,
                annotation_id=annotation_id,
                tool_model_id=req.model_id,
                db=db,
            )
            response = AetherResponse[PredictResults](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=str(req.meta.task_id),
                ),
                error=None,
            )
            return response
        else:
            res = AetherResponse(
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error="task not supported",
            )
            return JSONResponse(
                status_code=500,
                content=res,
            )
    except Exception as e:
        logger.error(e)
        return JSONResponse(
            status_code=500,
            content=AetherResponse(
                success=False,
                output=None,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error=str(e),
            ),
        )
