import json
import os
from typing import List, Optional

from ultralytics import YOLO

from base.file_delegate import FileDelegate, GetFileRequest, get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.models import ImageModel
from label.tools import (
    base64_to_cv2_image,
    bytes_to_image,
    encode_image_bytes,
    get_prompt,
    parse_response,
)
from yolo.response import PredictResults

max_tokens = 128

delegate = FileDelegate(bucket_type=s3_properties.datasets_bucket_name)


def label_img(
    img_data: str, classes: List[str], tool_model: ToolModel, prompt: Optional[str]
) -> ImageModel:
    """
    对图像进行标注
    :param img_data: 图像路径 or base64 编码的图像数据
    :param classes: 类别名称列表
    :return: ImageModel 对象
    """
    from label.client import get_model
    from label.tools import get_prompt, result_to_label

    vl_model = get_model(tool_model)

    # print(f"label_img: {img_data}, classes: {classes}")

    # get s3 image data
    b: Optional[bytes] = delegate.get_file(
        GetFileRequest(
            file_name=img_data,
            file_type=0,
            storage_type=1,
            url="/",
        )
    )

    if b is None:
        raise ValueError(f"Failed to read image: {img_data}")

    img_data = encode_image_bytes(b)

    if img_data.startswith("data:"):
        base64_img = img_data
    else:
        base64_img = f"data:image/png;base64,{img_data}"

    img = base64_to_cv2_image(img_data)
    if img is None:
        raise ValueError(f"Failed to read image: {img_data}")
    h, w, _ = img.shape

    if prompt is None:
        prompt = get_prompt(classes, w, h)
        completion = vl_model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are a helpful assistant."}
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        prompt,
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_img},
                        },
                    ],
                },
            ],
        )
    else:
        completion = vl_model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are a helpful assistant."}
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        prompt,
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_img},
                        },
                    ],
                },
            ],
        )
    return result_to_label(completion.choices[0].message.content, img_data, h=h, w=w)


def agent_label_img(
    img_name: str, classes: List[str], tool_model: ToolModel
) -> Optional[PredictResults] :
    """
    对图像进行标注
    :param img_data: 图像路径 or base64 编码的图像数据
    :param classes: 类别名称列表
    :return: PredictResults 对象
    """
    from label.client import get_model

    vl_model = get_model(tool_model)

    # print(f"label_img: {img_data}, classes: {classes}")

    # get s3 image data
    b: Optional[bytes] = delegate.get_file(
        GetFileRequest(
            file_name=img_name,
            file_type=0,
            storage_type=1,
            url="/",
        )
    )

    if b is None:
        raise ValueError(f"Failed to read image: {img_name}")
    
    if tool_model.type == "vision":
        model_path = tool_model.base_url
        model_name = model_path.split("/")[-1]
        # download model
        if not os.path.exists(model_name):
        # download model from s3
            op = get_operator(s3_properties.models_bucket_name)
            with open(model_path, "wb") as f:
                f.write(op.read(model_name))
        yolo = YOLO(model_name)
        img = bytes_to_image(b, "RGB", True)
        if img is None:
            raise ValueError(f"Failed to read image: {img_name}")
        h, w, _ = img.shape
        detections = yolo(img)
        if len(detections) == 0:
            return PredictResults.from_data(
                [], img=img_name, image_height=h, image_width=w
            )
        return PredictResults.from_data(
            json.loads(detections[0].to_json()),
            img=img_name,
            image_height=h,
            image_width=w,
        )
    elif tool_model.type == "vllm":
        img_data = encode_image_bytes(b)

        if img_data.startswith("data:"):
            base64_img = img_data
        else:
            base64_img = f"data:image/png;base64,{img_data}"

        img = base64_to_cv2_image(img_data)
        if img is None:
            raise ValueError(f"Failed to read image: {img_data}")
        h, w, _ = img.shape

        prompt = get_prompt(classes, w, h)
        completion = vl_model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant."}],
                },
                {
                    "role": "user",
                    "content": [
                        prompt,
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_img},
                        },
                    ],
                },
            ],
        )
        res = completion.choices[0].message.content
        logger.info(res)
        l = parse_response(res, classes)
        return PredictResults(image_id=img_name, results=l, image_height=h, image_width=w)
    else:
        return None
