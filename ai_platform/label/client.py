import json
import os
from io import BytesIO
from typing import List, Tuple, Union

import groundingdino.datasets.transforms as T
import numpy as np
import supervision as sv
import torch
from groundingdino.util.inference import box_convert, load_model, predict
from openai import OpenAI
from PIL import Image

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.tools import bytes_to_image
from yolo.response import Box, PredictResult, PredictResults


def load_image(data: bytes) -> Tuple[np.array, torch.Tensor]:
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    image_source = Image.open(BytesIO(data)).convert("RGB")
    image = np.asarray(image_source)
    image_transformed, _ = transform(image_source, None)
    return image, image_transformed


class ProvidedModelEnum:
    yolo = "YOLO"
    gd = "GroundingDINO"


BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25


def _tensor_to_predict_results(
    boxes: torch.tensor,
    logits: torch.tensor,
    labels: List[str],
    height,
    width,
    classes: List[str],
) -> PredictResults:
    logits_list = logits.tolist()
    logger.info(f"classes: {classes}")
    logger.info(f"labels: {labels}")
    results = []
    xyxy = box_convert(boxes=boxes, in_fmt="cxcywh", out_fmt="xyxy").numpy()
    boxes_list = [row.tolist() for row in xyxy]
    for i in range(len(boxes_list)):
        box = Box(
            x1=boxes_list[i][0] * width,
            y1=boxes_list[i][1] * height,
            x2=boxes_list[i][2] * width,
            y2=boxes_list[i][3] * height,
        )
        logger.info(f"box: {box}")
        results.append(
            PredictResult(
                name=labels[i],
                obj_class=classes.index(labels[i]) if labels[i] in classes else -1,
                confidence=logits_list[i],
                box=box,
            )
        )
    return PredictResults(image_id="test.png", results=results)


class ProvidedModelClient:
    def __init__(
        self,
        model_save_path: str,
        model_name: str,
        model_type: ProvidedModelEnum = ProvidedModelEnum.yolo,
    ):
        self.model_save_path = model_save_path
        self.op = get_operator(s3_properties.models_bucket_name)
        self.model_type = model_type

        if not os.path.exists(model_name):
            logger.info(f"download model {model_name} from s3 {model_save_path}")
            self.op.write(model_name, self.op.read(model_save_path))

        if model_type == ProvidedModelEnum.yolo:
            from yolo.predict import YOLO

            self.model = YOLO(model_name)
        elif model_type == ProvidedModelEnum.gd:

            self.model = load_model(
                "./gd/groundingdino/config/GroundingDINO_SwinT_OGC.py",
                "groundingdino_swint_ogc.pth",
            )
        else:
            self.model = None

    def predict(self, image: bytes, classes: List[str]) -> Union[PredictResults, None]:
        if self.model_type == ProvidedModelEnum.yolo:
            img_data = bytes_to_image(image)
            detections = self.model(img_data)
            if len(detections) == 0:
                return PredictResults.from_data([], img="test.png")
            return PredictResults.from_data(
                json.loads(detections[0].to_json()), img="test.png"
            )
        elif self.model_type == ProvidedModelEnum.gd:
            image_source, image_tensor = load_image(image)
            prompt = prompt = ". ".join(classes) + "."
            boxes, logits, phrases = predict(
                model=self.model,
                image=image_tensor,
                caption=prompt,
                box_threshold=BOX_TRESHOLD,
                text_threshold=TEXT_TRESHOLD,
                device="cpu",
            )
            h, w = image_source.shape[:2]
            return _tensor_to_predict_results(
                boxes, logits, phrases, height=h, width=w, classes=classes
            )
        else:
            return None


def get_model(tool_model: ToolModel) -> Union[OpenAI, ProvidedModelClient, None]:
    if (
        tool_model.base_url is not None
        and tool_model.base_url.startswith("http")
        and tool_model.type == "mllm"
    ):
        return OpenAI(api_key=tool_model.api_key, base_url=tool_model.base_url)
    if tool_model.type == "yolo":
        return ProvidedModelClient(
            model_save_path=tool_model.model_save_path,
            model_name=tool_model.model_name,
            model_type=ProvidedModelEnum.yolo,
        )
    if tool_model.type == "gd":
        return ProvidedModelClient(
            model_save_path=tool_model.model_save_path,
            model_name=tool_model.model_name,
            model_type=ProvidedModelEnum.gd,
        )
    return None
