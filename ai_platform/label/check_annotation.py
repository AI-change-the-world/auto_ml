import base64
from typing import List

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.client import get_model
from label.tools import bytes_to_image, parse_response
from yolo.response import PredictResults

# <Class>: (x_min, y_min, x_max, y_max) [confidence: X.XX]   请不要输出无效标注、分析或解释。

prompt = """
你是一个图像理解专家，任务是验证图像中物体的标注是否准确。  
以下是一些标注信息，每条包括：
- 类别（Class）
- 位置框（格式为: (x_min, y_min, x_max, y_max)）
- 置信度（confidence）

请根据图像执行以下操作：

### 验证要求：
1. **不要过度删除**：除非标注非常明显错误（如框内没有任何物体、类别完全不符），否则请保留标注。
2. **相似物体时偏向保留**：如迷彩服 vs 安全背心、人穿浅色衣服 vs 没穿背心，这些情况下，请保守判断，倾向保留。
3. **人类目标要特别谨慎**：只要框中确实有人，哪怕部分遮挡或姿势特殊，请保留“person”标注。
4. 请不要删除低置信度但明显正确的标注。
5. 如果标注不合理（如类别完全错误或框在空处），才删除。
6. 请不要输出无效标注、分析或解释。

### 输出格式：
仅返回合理的标注，格式如下（与输入一致）：
<Class>: (x_min, y_min, x_max, y_max) [confidence: X.XX]

下面是标注信息：
{annotations}

请根据图像内容，仅返回合理的标注，并遵守上述判断规则。
"""


def check_annotation(
    img: str, classes: List[str], annotations: str, tool_model: ToolModel
) -> PredictResults:
    vl_model = get_model(tool_model)
    op = get_operator(s3_properties.datasets_bucket_name)
    img_data = op.read(img)
    cv_img = bytes_to_image(img_data)
    h, w = cv_img.shape[:2]
    b64 = base64.b64encode(img_data).decode("utf-8")
    if not b64.startswith("data:image"):
        b64 = "data:image/png;base64," + b64

    prompt_template = prompt.format(annotations=annotations)
    completion = vl_model.chat.completions.create(
        model=tool_model.model_name,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [
                    prompt_template,
                    {
                        "type": "image_url",
                        "image_url": {"url": b64},
                    },
                ],
            },
        ],
    )
    logger.info("check annotation: " + completion.choices[0].message.content)
    l = parse_response(
        completion.choices[0].message.content,
        classes=classes,
    )
    return PredictResults(image_id=img, results=l, image_width=w, image_height=h)
