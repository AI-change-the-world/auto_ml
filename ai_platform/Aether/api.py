import time
import traceback

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from Aether import AetherRequest, AetherResponse, ResponseMeta
from base.file_delegate import s3_properties
from base.logger import logger
from base.nacos_config import get_db
from db.annotation.annotation_crud import get_annotation
from db.task.task_crud import get_task
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from db.tool_model.tool_model_crud import get_tool_model
from yolo.response import PredictResults

router = APIRouter(
    prefix="/aether",
    tags=["aether"],
)


@router.post("")
async def handle_request(req: AetherRequest[dict], db: Session = Depends(get_db)):
    start_time = time.time()
    task = get_task(db, req.meta.task_id)
    task_available = True
    if task is None:
        logger.warning(
            f"find no task for task id: {req.meta.task_id}, will not save logs"
        )
        task_available = False
    if task_available:
        tlc = TaskLogCreate(
            task_id=req.meta.task_id,
            log_content=f"[pre-task] initialize ...",
        )
        create_log(db, tlc)
    try:
        if req.task == "label":
            from label.label_img import agent_label_img

            logger.info(f"extra: {req.extra}")
            annotation_id = req.extra.get("annotation_id")
            annotation = get_annotation(db, annotation_id)
            classes = str(annotation.class_items).split(";")
            res = agent_label_img(
                img_name=req.input.data,
                classes=classes,
                tool_model=get_tool_model(db, req.model_id),
            )
            logger.info(f"res: {res}")
            response = AetherResponse[PredictResults](
                success=res is not None,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error="agent error" if res is None else None,
            )
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] eval done",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
            return response
        elif req.task == "label in batches":
            from label.multi_label_image_annotate import annotation_multi_class_image

            logger.info(f"extra: {req.extra}")
            annotation_id = req.extra.get("annotation_id")
            res = annotation_multi_class_image(
                img=req.input.data,
                annotation_id=annotation_id,
                tool_model_id=req.model_id,
                db=db,
            )
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[on task] merge results ...",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
            response = AetherResponse[PredictResults](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error=None,
            )
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] eval done",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
            return response
        elif req.task == "find similar":
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
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] eval done",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
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
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] eval done",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
            return response
        elif req.task == "label with gd":
            from label.label_with_gd import label_with_gd

            logger.info(f"label with gd, model id: {req.model_id}")

            tool_model = get_tool_model(db, req.model_id)
            annotation = get_annotation(db, req.extra.get("annotation_id"))
            classes = str(annotation.class_items).split(";")
            res = label_with_gd(
                img_path=req.input.data,
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
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] eval done",
                )
                create_log(db, tlc)
                # update_task(db, req.meta.task_id, {"status": 3})
            return response
        elif req.task == "check annotation":
            from label.check_annotation import check_annotation

            tool_model = get_tool_model(db, req.model_id)
            annotation = get_annotation(db, req.extra.get("annotation_id"))
            classes = str(annotation.class_items).split(";")
            annotations = req.extra.get("annotations")
            res = check_annotation(
                img=req.input.data,
                classes=classes,
                annotations=str(annotations),
                tool_model=tool_model,
            )
            # logger.info(f"check annotation res : {res.model_dump_json()}")
            response = AetherResponse[PredictResults](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error=None,
            )
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] check annotations done",
                )
                create_log(db, tlc)
            return response
        elif req.task == "deep describe":
            from process.video_process.key_frame_analysis import (
                deep_describe_frame_sync,
            )

            tool_model = get_tool_model(db, req.model_id)
            annotation = get_annotation(db, req.extra.get("annotation_id"))
            prompt = req.extra.get("prompt")
            res = deep_describe_frame_sync(
                frame_path=req.input.data,
                tool_model=tool_model,
                prompt=prompt,
                bucket=s3_properties.datasets_bucket_name,
            )
            response = AetherResponse[str](
                success=True,
                output=res,
                meta=ResponseMeta(
                    time_cost_ms=int((time.time() - start_time) * 1000),
                    task_id=req.meta.task_id,
                ),
                error=None,
            )
            if task_available:
                tlc = TaskLogCreate(
                    task_id=req.meta.task_id,
                    log_content=f"[post-task] check annotations done",
                )
                create_log(db, tlc)
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
        traceback.print_exc()
        logger.error(e)
        if task_available:
            tlc = TaskLogCreate(
                task_id=req.meta.task_id,
                log_content=f"error :{e}",
            )
            create_log(db, tlc)
        return AetherResponse(
            success=False,
            output=None,
            meta=ResponseMeta(
                time_cost_ms=int((time.time() - start_time) * 1000),
                task_id=req.meta.task_id,
            ),
            error=str(e),
        )
