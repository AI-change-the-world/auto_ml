from typing import List

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.client import get_model
from label.tools import bytes_to_image, cv2_to_base64
from yolo.response import Box, PredictResult, PredictResults

prompt = """
## 🎯 Object Detection Task

You are given two images:

1. A **Template Image**: Contains examples of one or more object types, with class names (e.g., "apple", "wrench", "button").
2. A **Target Image**: This is the image to annotate.

---

### 📐 Target Image Info:

- The target image resolution is **{width} pixels wide × {height} pixels tall**
- All bounding box coordinates you output must be based on this full resolution.
- Coordinates must be provided in **absolute pixel values**, not percentages or normalized values.

---

### 🚀 Task:

Identify and annotate all instances in the **target image** that are visually and semantically similar to those in the **template image**.

For each object, provide:

- The **class name** (same as the label in the template)
- The **bounding box coordinates**: `(x1, y1, x2, y2)` in **absolute pixel units**
- A confidence score between 0.0 and 1.0

---

### ✅ Output Format:

Each result should be a separate line, following this format:

<Class>: (x1, y1, x2, y2) [confidence: X.xx]

---

Example:

Diameter: (305, 628, 315, 640) [confidence: 0.96]
Diameter: (605, 880, 615, 892) [confidence: 0.94]

---

- `x1, y1` = top-left corner
- `x2, y2` = bottom-right corner
- All values must fit within **0 ≤ x ≤ {width}**, **0 ≤ y ≤ {height}**

---

### ⚠️ Critical Notes:

- Do NOT guess or extrapolate object positions.
- Do NOT output bounding boxes that are too small or outside the image.
- The coordinates must match the actual object location in the image — **no hallucinated spacing or alignment**.
- Confidence score must be over 0.5 to be included.
- Return only the bounding box list, no explanation or formatting.

"""


def label_with_reference(
    target_image: str,
    template_image: str,  # base64
    tool_model: ToolModel,
    classes: List[str],
):
    op = get_operator(s3_properties.datasets_bucket_name)
    target_image_bytes = op.read(target_image)
    # target_b64 = base64.b64encode(target_image_bytes).decode("utf-8")
    target_img_array = bytes_to_image(target_image_bytes)
    h, w, _ = target_img_array.shape
    logger.info(f"target image shape: {h}x{w}")
    target_b64 = cv2_to_base64(target_img_array)

    vl_model = get_model(tool_model)
    global prompt
    _prompt = prompt.format(width=w, height=h)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{template_image}",
                        "detail": "high",
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{target_b64}",
                        "detail": "high",
                    },
                },
            ],
        },
    ]

    completion = vl_model.chat.completions.create(
        model="qwen-vl-max-latest",
        # model = "moonshot-v1-128k-vision-preview",
        max_tokens=1024,
        messages=messages,
        temperature=0.7,
    )
    response = completion.choices[0].message.content
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
                # obj_class=classes.index(class_part),
                obj_class=classes.index(class_part) if class_part in classes else -1,
            )
            results.append(p)
        except Exception:
            continue
    return PredictResults(results=results, image_id=target_image)
