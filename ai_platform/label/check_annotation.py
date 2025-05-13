from typing import List
from db.tool_model.tool_model import ToolModel
from yolo.response import PredictResults


prompt = """
你是一个图像理解专家。现在请你验证以下图像标注信息是否准确。

每条标注包括：
- 类别（Class）
- 位置框（格式为 (x_min, y_min, x_max, y_max)）
- 置信度（confidence）

请执行以下任务：
1. 仔细观察图像中指定区域是否确实存在对应类别的物体。
2. 只保留合理的标注（框中确实包含该类别的物体，位置基本准确）。
3. 输出保留的标注信息，格式必须与输入完全一致：<Class>: (x_min, y_min, x_max, y_max) [confidence: X.XX]
4. 4. 请不要输出无效标注、分析或解释。

下面是标注信息：
{annotations}

请根据图像内容，只输出有效标注。
"""


def check_annotation(
    img: str, classes: List[str], annotations: list, tool_model: ToolModel
) -> PredictResults:
    pass