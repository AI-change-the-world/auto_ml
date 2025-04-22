from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from base import create_response
from base.nacos_config import get_db
from db.tool_model.tool_model_crud import get_tool_model
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


@router.post("/image")
async def label_img(req: LabelImgRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, req.model_id)

    if tool_model is None:
        return create_response(
            status=400,
            message="tool model not found",
            data=None,
        )

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
