import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Aether import AetherRequest, AetherResponse, ResponseMeta
from base.logger import logger
from base.nacos_config import get_db
from db.annotation.annotation_crud import get_annotation
from db.tool_model.tool_model_crud import get_tool_model
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
                    task_id=req.meta.task_id,
                ),
                error=None,
            )
            return response
        if req.task == "find similar":
            from label.find_similar import find_similar

            logger.info(f"extra: {req.extra}")
            annotation_id = req.extra.get("annotation_id")
            tool_model = get_tool_model(db, req.model_id)
            annotation = get_annotation(db, annotation_id)
            classes = str(annotation.class_items).split(";")
            left = req.extra["left"]
            top = req.extra["top"]
            bottom = req.extra["bottom"]
            right = req.extra["right"]
            label = req.extra["label"]
            res = find_similar(
                save_path=req.input.data,
                left=left,
                top=top,
                bottom=bottom,
                right=right,
                label=label,
                classes=classes,
                tool_model=tool_model,
            )
            response = AetherResponse[PredictResults](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error=None,
            )
            return response
        elif req.task == "label with reference":
            from label.label_with_reference import label_with_reference

            tool_model = get_tool_model(db, req.model_id)
            annotation = get_annotation(db, req.extra.get("annotation_id"))
            classes = str(annotation.class_items).split(";")
            res = label_with_reference(
                target_image=req.input.data,
                template_image=req.extra.get("template_image"),
                tool_model=tool_model,
                classes=classes,
            )
            response = AetherResponse[PredictResults](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
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
            return res
    except Exception as e:
        logger.error(e)
        return AetherResponse(
            success=False,
            output=None,
            meta=ResponseMeta(
                time_cost_ms=int((time.time() - start_time) * 1000),
                task_id=req.meta.task_id,
            ),
            error=str(e),
        )
