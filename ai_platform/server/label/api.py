import traceback
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from base import create_response
from base.logger import logger
from base.nacos_config import get_db
from db.annotation.annotation_crud import get_annotation
from db.tool_model.tool_model_crud import get_tool_model
from label.find_similar import find_similar
from label.label_img import label_img as impl_label_img

router = APIRouter(
    prefix="/label",
    tags=["label"],
)


class LabelImgRequest(BaseModel):
    image_data: str
    classes: List[str]
    model_id: int
    prompt: Optional[str]


class FindSimilarRequest(BaseModel):
    path: str
    left: float
    top: float
    right: float
    bottom: float
    label: str
    model: int
    id: int


class MultiClassImageAnnotateRequest(BaseModel):
    image_data: str
    annotation_id: int
    tool_model_id: int


@router.post("/image/multi-class")
async def multi_class_image_annotate(
    req: MultiClassImageAnnotateRequest, db: Session = Depends(get_db)
):
    from label.multi_label_image_annotate import annotation_multi_class_image

    try:
        return create_response(
            status=200,
            message="OK",
            data=annotation_multi_class_image(
                img=req.image_data,
                annotation_id=req.annotation_id,
                tool_model_id=req.tool_model_id,
                db=db,
            ),
        )
    except Exception as e:
        traceback.print_exc()
        logger.fatal(e)
        return create_response(
            status=500,
            message="Internal Server Error",
        )


@router.post("/image")
async def label_img(req: LabelImgRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, req.model_id)

    if tool_model is None:
        return create_response(
            status=400,
            message="tool model not found",
            data=None,
        )
    try:
        return create_response(
            status=200,
            message="OK",
            data=impl_label_img(
                img_data=req.image_data,
                classes=req.classes,
                tool_model=tool_model,
                prompt=req.prompt,
            ),
        )
    except Exception as e:
        traceback.print_exc()
        logger.fatal(e)
        return create_response(
            status=500,
            message="Internal Server Error",
        )


@router.post("/similar")
async def similar_annotation(req: FindSimilarRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, req.model)
    annotation = get_annotation(db, req.id)
    if not annotation:
        return create_response(
            status=500,
            message="Annotation not found",
        )
    if not tool_model:
        return create_response(
            status=500,
            message="Tool model not found",
        )
    classes = str(annotation.class_items).split(";")
    try:
        res = find_similar(
            save_path=req.path,
            left=req.left,
            top=req.top,
            bottom=req.bottom,
            right=req.right,
            label=req.label,
            classes=classes,
            tool_model=tool_model,
        )
        return create_response(
            status=200,
            message="Success",
            data=res,
        )
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return create_response(
            status=500,
            message=str(e),
            data=None,
        )
