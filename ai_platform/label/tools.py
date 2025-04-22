import base64
import re
from typing import List

import cv2
import numpy as np

from label.models import ImageModel, LabelModel

base_prompt = {
    "type": "text",
    "text": """You are a vision expert specialized in object detection for YOLO models.  
Analyze the image and detect all objects from the following list (COCO classes):  
{{labels}}  

For each object you find, output one line in this strict format:  
<Class>: (x_min, y_min, width, height)  

- x_min, y_min, width, height are in absolute pixel values.  
- Do not return any explanations, titles, or extra text.  
- Only return valid lines matching the exact format above.  
- Detect as many instances as you can. Multiple instances of the same class are allowed.

Example:
{{label1}}: (42, 133, 120, 200)  
{{label2}}: (300, 100, 100, 180)  
{{label1}}: (500, 400, 120, 150)

Your output:""",
}


def get_prompt(labels: List[str]) -> str:
    assert len(labels) > 0, "labels must not be empty"
    prompt = base_prompt.copy()
    label1 = labels[0]
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


def result_to_label(result: str, img_data: str) -> ImageModel:
    """
    解析标注字符串并转换为 ImageModel
    :param result: LLM 返回的目标检测字符串，如：
                   "Vase: (243,150,411,346)\nFlower: (207,34,462,218)"
    :param img_data: 图像路径 or base64 编码的图像数据
    :return: ImageModel 对象
    """
    import cv2

    if img_data.startswith("data:"):
        img = base64_to_cv2_image(img_data)
    else:
        img = cv2.imread(img_data)

    if img is None:
        raise ValueError(f"Failed to read image: {img_data}")
    h, w, _ = img.shape

    # print(result)
    # 正则匹配目标标注信息
    pattern = re.compile(r"(\w+):\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)")
    matches = pattern.findall(result)

    labels = []
    for match in matches:
        label, x_min, y_min, width, height = match
        x_min, y_min, width, height = map(int, [x_min, y_min, width, height])

        # 计算 YOLO 归一化格式 (x_center, y_center, width, height)
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
            )
        )

    return ImageModel(labels=labels)


if __name__ == "__main__":
    print(get_prompt(["person", "car"]))
