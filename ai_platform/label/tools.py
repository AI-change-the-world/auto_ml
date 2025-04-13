import base64
import re
from typing import List

from label.models import ImageModel, LabelModel


base_prompt = {
    "type": "text",
    "text": "You are an AI model trained to annotate images for YOLO object detection. "
    "Analyze the given image and identify objects belonging to the following categories: {{labels}}. "
    "For each detected object, provide the annotation in the following structured format:\n\n"
    "<Object Class>: (x_min, y_min, width, height)\n\n"
    "Example Output:\n"
    "{{label1}}: (120, 300, 80, 150)\n"
    "{{label2}}: (200, 100, 150, 200)\n\n"
    "Do not include any additional text or explanation. Only return the structured annotations.",
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


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def result_to_label(result: str, img_path: str) -> ImageModel:
    """
    解析标注字符串并转换为 ImageModel
    :param result: LLM 返回的目标检测字符串，如：
                   "Vase: (243,150,411,346)\nFlower: (207,34,462,218)"
    :param img_path: 图像路径
    :return: ImageModel 对象
    """
    import cv2

    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Failed to read image: {img_path}")
    h, w, _ = img.shape

    # 正则匹配目标标注信息
    pattern = re.compile(r"(\w+): \((\d+),(\d+),(\d+),(\d+)\)")
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

    return ImageModel(image_path=img_path, labels=labels)


if __name__ == "__main__":
    print(get_prompt(["person", "car"]))
