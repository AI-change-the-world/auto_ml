import json
import os
from typing import List, Optional, Set

from sqlalchemy.orm import Session
from ultralytics import YOLO

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.available_models.available_models_crud import get_available_model
from label.tools import base64_to_cv2_image
from yolo.response import ClsPredictResults, PredictResults

running_models: Set[int] = set()


# unused
def __predict(model: YOLO, img: str) -> PredictResults:
    result = model.predict(img, stream=False)
    if len(result) == 0:
        return PredictResults.from_data([], img)
    return PredictResults.from_data(json.loads(result[0].to_json()), img=img)


# unused; deprecated
async def predict(model_name: str, imgs: List[str]):
    model = YOLO(model_name)

    # 异步生成推理结果
    for item in imgs:
        yield __predict(model, item).model_dump_json()

    yield "[DONE]"


def get_running_models() -> List[int]:
    global running_models
    return list(running_models)


def stop_model(model_id: int):
    global running_models
    running_models.remove(model_id)


def start_model(model_id: int, db: Session):
    global running_models
    am = get_available_model(db, model_id)
    if not am:
        return 1
    logger.info(f"start model {model_id} ")
    if not os.path.exists(am.save_path):
        logger.info(f"download model {model_id} from s3 {am.save_path}")
        # download model from s3
        op = get_operator(s3_properties.models_bucket_name)
        with open(am.save_path, "wb") as f:
            f.write(op.read(am.save_path))
    running_models.add(model_id)
    return 0


def predict_with_certain_model(
    model_id: int, img: str, db: Session
) -> Optional[PredictResults]:
    global running_models
    am = get_available_model(db, model_id)
    if not am:
        return None
    img_data = base64_to_cv2_image(img)
    h, w = img_data.shape[:2]
    if not os.path.exists(am.save_path):
        # download model from s3
        op = get_operator(s3_properties.models_bucket_name)
        with open(am.save_path, "wb") as f:
            f.write(op.read(am.save_path))
    model = YOLO(am.save_path)
    running_models.add(am.available_model_id)
    # eval
    detections = model(img_data)
    if len(detections) == 0:
        return PredictResults.from_data(
            [], img="test.png", image_height=h, image_width=w
        )
    return PredictResults.from_data(
        json.loads(detections[0].to_json()),
        img="test.png",
        image_height=h,
        image_width=w,
    )


def cls_predict_with_certain_model(
    model_id: int, img: str, db: Session
) -> Optional[ClsPredictResults]:
    global running_models
    am = get_available_model(db, model_id)
    if not am:
        return None
    img_data = base64_to_cv2_image(img)
    if not os.path.exists(am.save_path):
        # download model from s3
        op = get_operator(s3_properties.models_bucket_name)
        with open(am.save_path, "wb") as f:
            f.write(op.read(am.save_path))
    model = YOLO(am.save_path)
    running_models.add(am.available_model_id)
    # eval
    detections = model(img_data)
    if len(detections) == 0:
        return ClsPredictResults(
            image_id="test.png", name="unknown", confidence=0.0, class_id=-1
        )
    j = json.loads(detections[0].to_json())

    if isinstance(j, list):
        return ClsPredictResults(
            image_id="test.png",
            name=j[0]["name"],
            confidence=j[0]["confidence"],
            class_id=j[0]["class"],
        )
    else:
        return ClsPredictResults(
            image_id="test.png",
            name=j["name"],
            confidence=j["confidence"],
            class_id=j["class"],
        )
