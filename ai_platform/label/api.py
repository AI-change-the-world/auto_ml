from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from base import create_response
from label.label_img import label_img as impl_label_img

router = APIRouter(
    prefix="/label",
    tags=["label"],
)


class LabelImgRequest(BaseModel):
    image_path: str
    classes: List[str]


@router.post("/image")
async def label_img(req: LabelImgRequest):
    return create_response(
        status=200,
        message="OK",
        data=impl_label_img(img_path=req.image_path, classes=req.classes),
    )
