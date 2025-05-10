import base64
import os

import cv2
from openai import OpenAI

# 1870×1214 pixels

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


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


template_img = (
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_template.png"
)
target_img = (
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_test_resize.png"
)

vl_model = OpenAI(
    api_key=os.environ.get("APIKEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# vl_model = OpenAI(
#     api_key=os.environ.get("MOONSHOT_API_KEY"),
#     base_url="https://api.moonshot.cn/v1",
# )

# Base64 编码图像
template_base64 = encode_image_to_base64(template_img)
target_base64 = encode_image_to_base64(target_img)

width = 935
height = 670

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt.format(width=width, height=height)},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{template_base64}",
                    "detail": "high",
                },
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{target_base64}",
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

res = completion.choices[0].message.content

print(res)

result_img = cv2.imread(target_img)

for line in res.strip().splitlines():
    try:
        class_part, rest = line.split(":", 1)
        box_part, conf_part = rest.strip().split("[confidence:")
        x, y, w, h = map(int, box_part.strip("() ").split(","))
        conf = float(conf_part.strip(" ]"))
        # detection = Detection
        # b = Box(x1=x, y1=y, x2=w +x, y2=h+y)
        class_part = class_part.strip()
        cv2.rectangle(result_img, (x, y), (w, h), color=(0, 255, 0), thickness=2)
        cv2.putText(
            result_img,
            class_part,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (36, 255, 12),
            2,
        )
    except Exception:
        continue

cv2.imwrite("result_road.png", result_img)
