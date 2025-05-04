import base64
import re
from typing import List

import cv2
import numpy as np

from label.models import ImageModel, LabelModel

base_prompt = {
    "type": "text",
    "text": """You are a vision expert specialized in object detection for YOLO models.  
Analyze the image and detect all objects from the following list:  
{{labels}}  

For each object you find, output one line in this strict format:  
<Class>: (x_min, y_min, width, height) [confidence: X.XX]  

- The image size is {{width}}x{{height}} pixels.  
- x_min, y_min, width, height are absolute pixel values.  
- Confidence is a float between 0.00 and 1.00 indicating how certain you are about the detection.  
- Output no more than 20 objects in total.  
- Only include detections with confidence >= 0.90.  
- Do NOT split a single object (e.g., a train) into multiple detections (e.g., many "cars").  
- Do NOT include multiple objects whose bounding boxes overlap more than 90% in area.  
- When multiple overlapping boxes are possible, keep only the one with the highest confidence.  
- If in doubt or the object appears ambiguous, do not include it.  
- Prioritize clear, distinct, and recognizable objects.

Example:
train: (42, 133, 320, 180) [confidence: 0.97]  
car: (600, 210, 180, 120) [confidence: 0.93]  
person: (500, 400, 120, 150) [confidence: 0.91]

Your output:""",
}

min_confidence = 0.95


def get_prompt(labels: List[str], width: int = 0, height: int = 0) -> str:
    assert len(labels) > 0, "labels must not be empty"
    assert width > 0 and height > 0, "width and height must be greater than 0"
    prompt = base_prompt.copy()
    label1 = labels[0]
    prompt["text"] = prompt["text"].replace("{{width}}", str(width))
    prompt["text"] = prompt["text"].replace("{{height}}", str(height))
    if len(labels) > 1:
        label2 = labels[1]
        prompt["text"] = prompt["text"].replace("{{label1}}", label1)
        prompt["text"] = prompt["text"].replace("{{label2}}", label2)
    else:
        prompt["text"] = prompt["text"].replace("{{label1}}", label1)
        prompt["text"] = prompt["text"].replace("{{label2}}", label1)
    _labels = list(map(lambda x: f"'{x}'", labels))
    prompt["text"] = prompt["text"].replace("{{labels}}", ", ".join(_labels))
    return prompt


def base64_to_cv2_image(base64_str: str) -> np.ndarray:
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    else:
        pass
    # 解码 Base64 字符串为字节
    img_data = base64.b64decode(base64_str)

    # 将字节数据转换为 NumPy 数组
    np_arr = np.frombuffer(img_data, np.uint8)

    # 使用 OpenCV 解码成图像
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # 也可以用 IMREAD_UNCHANGED

    return img


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_image_bytes(b: bytes):
    return base64.b64encode(b).decode("utf-8")


def result_to_label(result: str, img_data: str, h: int = 0, w: int = 0) -> ImageModel:
    """
    解析标注字符串并转换为 ImageModel
    :param result: LLM 返回的目标检测字符串，如：
                   "Vase: (243,150,411,346)\nFlower: (207,34,462,218)"
    :param img_data: 图像路径 or base64 编码的图像数据
    :return: ImageModel 对象
    """
    # import cv2

    # if img_data.startswith("data:"):
    #     img = base64_to_cv2_image(img_data)
    # else:
    #     img = cv2.imread(img_data)

    # if img is None:
    #     raise ValueError(f"Failed to read image: {img_data}")
    # h, w, _ = img.shape

    print(f"Image size: {w}x{h}")

    # print(result)
    # 正则匹配目标标注信息
    # pattern = re.compile(r"(\w+):\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)")
    pattern = re.compile(
        r"(\w+):\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)\s*\[confidence:\s*([0-9]*\.?[0-9]+)\]"
    )
    matches = pattern.findall(result)

    labels = []
    for match in matches:
        label, x_min, y_min, width, height, confidence = match
        confidence = float(confidence)
        if confidence < min_confidence:
            continue
        x_min, y_min, width, height = map(int, [x_min, y_min, width, height])

        # 计算最大边界值
        x_max = min(x_min + width, w)
        y_max = min(y_min + height, h)

        # 裁剪后的宽高
        width = max(0, x_max - x_min)
        height = max(0, y_max - y_min)

        # 若框被完全裁掉（例如全在图像外），可以跳过
        if width == 0 or height == 0:
            continue

        # 计算 YOLO 格式归一化 (x_center, y_center, width, height)
        x_center = (x_min + width / 2) / w
        y_center = (y_min + height / 2) / h
        norm_width = width / w
        norm_height = height / h

        labels.append(
            LabelModel(
                label=label,
                x_center=round(x_center, 4),
                y_center=round(y_center, 4),
                width=round(norm_width, 4),
                height=round(norm_height, 4),
                confidence=round(confidence, 4),
            )
        )

    return ImageModel(labels=labels)


if __name__ == "__main__":
    print(get_prompt(["person", "car"]))
