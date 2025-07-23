from typing import List

import cv2

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.client import get_model
from label.tools import bytes_to_image, cv2_to_base64, parse_boxes_from_string
from yolo.response import PredictResults

basic_prompt = """
### 📝 Task Description

You are given an image that contains multiple objects. Your task is to identify and annotate **all objects** in the image that belong to the same category as the one highlighted by a white rectangle.

---

### 📋 Object Categories in This Image

{categories_md}

---

### 🎯 Target Category

The white rectangle highlights an example of a **{example_category}**.  
Please find and annotate **all other {example_category}s** in the image.

---

### 🧾 Expected Output Format

Return the bounding boxes for each detected {example_category} as a list of coordinates:  
```
(x, y, width, height)
```

For example:
```
[
  (34, 88, 45, 45),
  (120, 150, 50, 48)
]
```

If no other {example_category}s are found, respond with:
```
None
```

---

### 🖍️ Notes

- Only annotate objects that belong to the same category as the one inside the white rectangle.
- Do not annotate objects from other categories.
- Use visual similarity, shape, color, and context to determine category match.
- The white rectangle is drawn clearly with a visible white border.

---

### ⚠️ Instructions

- Do **not** explain your reasoning.
- Do **not** include step-by-step analysis.
- Only return the final result in the specified format.
- Do not annotate any objects from other categories.
"""


def build_prompt(categories: List[str], example_category: str) -> str:
    categories_md = "\n".join(f"- {cat}" for cat in categories)
    return basic_prompt.format(
        categories_md=categories_md, example_category=example_category
    )


max_tokens = 128


def find_similar(
    save_path: str,
    left: float,
    top: float,
    bottom: float,
    right: float,
    label: str,
    classes: List[str],
    tool_model: ToolModel,
):
    op = get_operator(s3_properties.datasets_bucket_name)
    file_bytes = op.read(save_path)
    img = bytes_to_image(file_bytes)
    # 将 float 坐标转换为整数像素坐标
    pt1 = (int(left), int(top))
    pt2 = (int(right), int(bottom))

    # 绘制白色矩形框（BGR = (255, 255, 255)）
    img = cv2.rectangle(img, pt1, pt2, color=(255, 255, 255), thickness=2)
    h, w = img.shape[:2]
    # b64 = base64.b64encode(file_bytes).decode("utf-8")
    b64 = cv2_to_base64(img)
    b64_with_header = f"data:image/png;base64,{b64}"
    vl_model = get_model(tool_model)

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
                    build_prompt(classes, label),
                    {
                        "type": "image_url",
                        "image_url": {"url": b64_with_header},
                    },
                ],
            },
        ],
    )
    logger.info("other objects: " + completion.choices[0].message.content)
    l = parse_boxes_from_string(
        completion.choices[0].message.content,
        obj_class=classes.index(label) if label in classes else -1,
        name=label,
    )
    return PredictResults(image_id=save_path, results=l, image_width=w, image_height=h)
