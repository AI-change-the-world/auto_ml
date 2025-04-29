# this is just for testing
import base64
from typing import Optional

import cv2
import numpy as np

from base.deprecated import deprecated
from base.file_delegate import get_op
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.client import get_model


def draw_box_and_encode_base64(image_bytes, x1, y1, x2, y2):
    # 1. 从 bytes 解码为图像
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("无法从字节解码图像")

    # 2. 画矩形（白色框，2像素宽）
    pt1 = (int(x1), int(y1))
    pt2 = (int(x2), int(y2))
    cv2.rectangle(img, pt1, pt2, color=(255, 255, 255), thickness=2)

    cv2.imwrite("output.jpg", img)

    # 3. 编码图像为 JPEG 格式的 bytes
    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        raise ValueError("图像编码失败")

    # 4. 转为 Base64 字符串
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    return img_base64


safety_prompt = {
    "type": "text",
    "text": """你是一位专注于施工现场安全行为分析的多模态视觉专家。  
请分析图像中用白色框标注出的工人，并根据以下安全规范判断该工人是否存在不规范行为：  
{{safety_items}}

请输出一行分析，格式如下：  
工人：<是否规范> - <问题简述> [依据: <简要说明>]  

说明：
- <是否规范> 仅填写“规范”或“不规范”；  
- <问题简述> 可为空（当规范时），否则需简明列出问题，如“未佩戴安全帽”；  
- <简要说明> 需说明你是如何判断该问题的；  
- 如该工人姿态或遮挡过多，导致无法判断，请说明为“无法判断”并给出原因；  
- 如果不确定是否存在问题，则认为“规范”；  
- 提供的安全规范可能不完善，可以结合自身的经验进行判断，但请不要过度依赖经验。
- 如果有的话，依据需要给出具体规范，如：JGJ 59-2011、JGJ/T 429-2018 等。

输出示例：
工人：规范 -  [依据: 安全帽、防护服齐全，未处于危险区域]  
工人：不规范 - 未佩戴安全帽 [依据: 头部无遮挡，明显未见头盔]  
工人：无法判断 - [依据: 人员背对镜头，防护装备被遮挡]

你的输出：""",
}

reserved = """
1. 进入施工现场必须正确佩戴安全帽，系好下颚带；在高处作业时必须系好安全带，挂在牢固可靠处。（出处：《建筑施工安全检查标准》JGJ 59-2011、《建筑施工易发事故防治安全标准》JGJ/T 429-2018 等）

2. 高处作业时，严禁在无可靠防护措施的情况下临边、洞口作业，必须设置防护栏杆、安全网等防护设施。（出处：《建筑施工高处作业安全技术规范》JGJ 80-2016、《建筑施工安全检查标准》JGJ 59-2011）

3. 脚手架的搭设、拆除必须由专业架子工进行，严格按照施工方案和相关规范要求进行操作，搭设完成后经检查验收合格后方可使用。（出处：《建筑施工扣件式钢管脚手架安全技术规范》JGJ 130-2011、《建筑施工门式钢管脚手架安全技术规范》JGJ 128-2010）
"""


@deprecated(reason="effects are not good")
async def key_frame_analysis(
    frame_path: str,
    tool_model: ToolModel,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    prompt: Optional[str] = None,
):
    if tool_model is None:
        yield "tool_model is None"

    try:
        op = get_op()

        file_data = op.read(frame_path)
        b64 = draw_box_and_encode_base64(file_data, x1, y1, x2, y2)
        b64_with_header = f"data:image/jpeg;base64,{b64}"
        vl_model = get_model(tool_model)

        if prompt is None:
            prompt = safety_prompt["text"].replace("{{safety_items}}", reserved)

        req = {"type": "text", "text": prompt}

        completion = vl_model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=512,
            stream=True,
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
                        req,
                        {
                            "type": "image_url",
                            "image_url": {"url": b64_with_header},
                        },
                    ],
                },
            ],
        )
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content"):
                yield delta.content
    except Exception as e:
        logger.error(e)
    finally:
        yield "[DONE]"


describe_prompt = {
    "type": "text",
    "text": """
你是一位建筑施工现场分析专家。

请根据提供的图像，从以下五个方面进行详细描述，重点分析工人的工作状态和施工现场环境。要求描述具体、专业、有条理，语言正式，适合作为工程监督记录报告。

1. **现场环境**：
   - 描述施工场景的位置（如：室内/室外、高空/地面）。
   - 判断施工阶段（如：地基施工、钢结构搭建、装修阶段等）。
   - 天气情况（如可见）。

2. **工人情况**：
   - 有多少位工人？每位工人目前在做什么？尽量具体描述（如：“正在操作电焊机焊接钢筋”，“在搬运模板”）。
   - 工人的姿势（站立、弯腰、攀爬等）、注意力状态。
   - 是否佩戴安全装备（头盔、反光衣、手套、安全绳等）。

3. **工具与机械**：
   - 图中有哪些施工工具或机械？是否正在使用？
   - 谁在使用它们？使用方式是否规范？

4. **安全与规范性**：
   - 工人是否遵守安全规范？
   - 是否存在安全隐患？如杂乱电缆、缺少防护等。

5. **现场动态与协作**：
   - 当前有哪些施工活动正在进行？
   - 是否有工人之间的协作行为？协作方式如何？

请针对每个部分分别撰写结构清晰、内容详实的段落，不要遗漏细节。""",
}


async def describe_frame(
    frame_path: str,
    tool_model: ToolModel,
    prompt: Optional[str] = None,
):
    if tool_model is None:
        yield "tool_model is None"

    try:
        op = get_op()

        file_data = op.read(frame_path)
        b64 = base64.encodebytes(file_data).decode("utf-8")
        b64_with_header = f"data:image/jpeg;base64,{b64}"
        vl_model = get_model(tool_model)

        if prompt is None:
            prompt = describe_prompt["text"]

        req = {"type": "text", "text": prompt}

        completion = vl_model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=1024,
            stream=True,
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
                        req,
                        {
                            "type": "image_url",
                            "image_url": {"url": b64_with_header},
                        },
                    ],
                },
            ],
        )
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content"):
                yield delta.content
    except Exception as e:
        logger.error(e)
    finally:
        yield "[DONE]"
