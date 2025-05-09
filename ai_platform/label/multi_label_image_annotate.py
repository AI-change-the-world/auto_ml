import base64
from io import BytesIO
from typing import Any, List, Tuple, Union

import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.annotation.annotation_crud import get_annotation
from db.tool_model.tool_model import ToolModel
from db.tool_model.tool_model_crud import get_tool_model
from label.client import get_model
from yolo.response import Box, PredictResult, PredictResults


class MultiClassImageAnnotator:
    def __init__(
        self,
        tool_model: ToolModel,
        classes: List[str],
        batch_size=10,
        confidence_threshold=0.90,
    ):
        self.model = get_model(tool_model)
        self.model_name = tool_model.model_name
        self.batch_size = batch_size
        self.conf_threshold = confidence_threshold
        self.classes = classes

    def _image_to_base64(
        self, img: Union[np.ndarray, bytes, Image.Image, str]
    ) -> Tuple[str, Tuple[int, int]]:
        # 1. If it's a file path
        if isinstance(img, str):
            pil_image = Image.open(img).convert("RGB")

        # 2. If it's bytes
        elif isinstance(img, bytes):
            pil_image = Image.open(BytesIO(img)).convert("RGB")

        # 3. If it's a numpy array
        elif isinstance(img, np.ndarray):
            pil_image = Image.fromarray(img).convert("RGB")

        # 4. If it's already a PIL image
        elif isinstance(img, Image.Image):
            pil_image = img.convert("RGB")

        else:
            raise TypeError("Unsupported image input type.")

        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str, pil_image.size  # (width, height)

    def _chunk_classes(self) -> List[List[str]]:
        return [
            self.classes[i : i + self.batch_size]
            for i in range(0, len(self.classes), self.batch_size)
        ]

    def _build_prompt(self, class_batch: List[str], image_size: Tuple[int, int]) -> str:
        width, height = image_size
        return f"""
You are an object detection expert.

Given the following target classes:  
{class_batch}

Analyze the image and for each class, detect all visible instances.

Return your results in this exact format:  
<Class>: (x_min, y_min, x_max, y_max) [confidence: X.XX]

Rules:
- The image pixel coordinate system starts at (0, 0) in the top-left corner.
- The image has a right boundary at x = {width - 1} and a bottom boundary at y = {height - 1}.
- All coordinates must be integers within image bounds:
  - 0 ≤ x_min < x_max ≤ {width}
  - 0 ≤ y_min < y_max ≤ {height}
- Only include objects from the target classes.
- Only include objects with confidence ≥ {self.conf_threshold}.
- Do NOT include overlapping bounding boxes (IOU > 90%).
- Do NOT include ambiguous, partial, or low-confidence detections.
- Do NOT output negative or out-of-bound coordinates.
        """.strip()

    def _call_model(self, prompt: str, base64_image: str) -> str:
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=256,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str):
        results = []
        logger.info(f"Response: {response}")
        for line in response.strip().splitlines():
            try:
                class_part, rest = line.split(":", 1)
                box_part, conf_part = rest.strip().split("[confidence:")
                x, y, w, h = map(int, box_part.strip("() ").split(","))
                conf = float(conf_part.strip(" ]"))
                # detection = Detection
                # b = Box(x1=x, y1=y, x2=w +x, y2=h+y)
                b = Box(x1=x, y1=y, x2=w, y2=h)
                class_part = class_part.strip()
                p: PredictResult = PredictResult(
                    name=class_part,
                    box=b,
                    confidence=conf,
                    obj_class=self.classes.index(class_part),
                )
                results.append(p)
            except Exception:
                continue
        return results

    def annotate(self, image: Any) -> List[dict]:
        base64_img, image_size = self._image_to_base64(image)
        all_results = []
        for class_batch in self._chunk_classes():
            prompt = self._build_prompt(class_batch, image_size)
            response = self._call_model(prompt, base64_img)
            batch_results = self._parse_response(response)
            all_results.extend(batch_results)
        return all_results


def annotation_multi_class_image(
    img: str, annotation_id: int, tool_model_id: int, db: Session
):
    op = get_operator(s3_properties.datasets_bucket_name)
    tool_model = get_tool_model(db, tool_model_id)
    annotation = get_annotation(db, annotation_id)
    img_bytes = op.read(img)
    classes = str(annotation.class_items).split(";")
    # TODO remove this logic
    if classes.__len__() > 10:
        classes = classes[:10]
    annotator = MultiClassImageAnnotator(tool_model, classes=classes)
    res = annotator.annotate(img_bytes)
    return PredictResults(image_id=img, results=res)
