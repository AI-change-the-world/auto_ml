# this is just for testing
import base64
from typing import Any, AsyncGenerator, List, Optional

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

# multiple_frames_prompt = """
# 你是一位建筑施工现场分析专家。
# 我将向你提供多张施工现场图像，请你对图像中展示的场景和人物进行综合分析，要求专业、正式、有条理，适合作为工程监督记录报告。请从以下五个方面逐项详细描述，并在最后撰写一个总结段落，概括每位工人的行为变化和整体施工动态。


# 1. 现场环境对比分析
# 	•	描述各图像所呈现的施工场景（室内/室外、高空/地面），若有变化请指出。
# 	•	判断各图像所属的施工阶段（如：地基施工、模板搭设、钢结构拼装、室内装修等）。
# 	•	天气情况（如可见）：晴天/阴天/下雨、有无阳光或灯光等。

# 2. 工人活动与状态识别
# 	•	分别识别出图像中出现的所有工人，并编号（如：工人 A、B、C）。
# 	•	描述每位工人在各图中的位置、动作和所从事的工作（例如：“工人 A 在第一张图中搬运钢筋，在第三张图中正在焊接”）。
# 	•	工人的姿态（站立、弯腰、攀爬等）、注意力状态是否专注。
# 	•	是否佩戴完整安全装备（安全帽、反光背心、安全绳、手套等），有无穿戴不当或缺失的情况。

# 3. 施工工具与机械使用情况
# 	•	列出图中可见的工具或机械设备（如：电焊机、吊装设备、脚手架等）。
# 	•	哪些设备正在使用？谁在使用？是否符合规范操作姿势？
# 	•	如果出现设备闲置、摆放混乱，也请指出。

# 4. 安全规范与隐患评估
# 	•	分析施工行为是否符合安全规范，是否存在违规操作（如高处作业未系安全绳、电缆拖地等）。
# 	•	有无杂物堆放、临边未防护、电气设备裸露等潜在安全隐患。
# 	•	施工现场的整洁程度是否符合标准。

# 5. 多人协作与现场动态
# 	•	是否存在两人或多人协作行为？他们是如何配合的？如搬运材料、协助定位等。
# 	•	哪些工作是独立完成，哪些是小组协同？
# 	•	是否有明显的分工与协调机制体现？

# 6. 总结与工人行为概况
# 	•	请根据多张图像，概括每位工人的工作内容与行为变化轨迹（如：“工人 A 从清理现场转为焊接操作，始终保持佩戴完整防护装备”）。
# 	•	总结施工现场整体状态：进展是否有序，安全规范是否到位，是否存在管理盲区或值得表扬的行为。
# """

multiple_frames_prompt = """
你是一位**建筑施工现场分析专家**，请对我提供的多张施工现场图像进行**综合分析与专业评估**，要求分析**逻辑清晰、条理分明、语气正式专业，适用于工程监督记录报告**。  
请按照以下 **六个部分**逐项撰写内容，**每部分单独分段描述**，并在末尾撰写一个综合性“第六部分总结”。

---

## 第1部分：现场环境对比分析
- **图像场景类型**：
  - 图1：  
  - 图2：  
  - 图3：  
- **施工阶段判断**：
  - 图1：  
  - 图2：  
  - 图3：  
- **天气与照明情况**：
  - 图1：  
  - 图2：  
  - 图3：  

---

## 第2部分：工人活动与状态识别
- **工人识别与编号**：
  - 图1：工人 A、B  
  - 图2：工人 A、C  
  - 图3：工人 A、B、C  
- **工人活动描述**：
  - 工人 A：
    - 图1：位置、动作、作业内容  
    - 图2：  
    - 图3：  
  - 工人 B：
    - 图1：  
    - 图3：  
  - 工人 C：
    - 图2：  
    - 图3：  
- **工人姿态与注意力状态**：  
  - A：  
  - B：  
  - C：  
- **安全装备穿戴情况**：
  - A：  
  - B：  
  - C：  

---

## 第3部分：施工工具与机械使用情况
- **可见施工工具与设备**：
  - 图1：  
  - 图2：  
  - 图3：  
- **设备使用情况与操作规范**：
  - 使用中设备：  
  - 操作者编号及行为：  
  - 操作是否规范：  
- **设备闲置或摆放混乱情况**：
  - 闲置设备：  
  - 问题说明：  

---

## 第4部分：安全规范与隐患评估
- **施工行为安全性分析**：
  - 高空作业是否防护：  
  - 操作规范性：  
- **潜在安全隐患识别**：
  - 电缆、电气设备：  
  - 杂物堆放：  
  - 临边/洞口防护：  
- **现场整洁程度**：
  - 清洁标准符合情况：  

---

## 第5部分：多人协作与现场动态
- **是否存在协作行为**：
  - 类型与参与者：  
  - 典型协作场景：  
- **独立作业与小组协同区分**：
  - 独立完成任务：  
  - 小组协作任务：  
- **流程协调与施工节奏**：
  - 是否有序：  
  - 是否存在等待/重复作业等低效现象：  

---

## 第6部分：总结与工人行为概况
- **工人行为轨迹概括**：
  - 工人 A：  
  - 工人 B：  
  - 工人 C：  
- **施工现场整体状态评估**：
  - 进展情况：  
  - 安全规范落实情况：  
  - 管理盲区或值得表扬行为：  
"""


single_frame_deep_analyze_prompt = """
你是一名负责工地安全分析的多模态专家。现在请结合下方的现场图像和初步检测结果，对施工现场进行全面的安全分析。请严格从以下六个方面展开分析，并注意参考初步检测结果进行补充与修正：

---

**小模型检测结果：**  
检测到 10 个目标：  
{{yolo_result}}

---

请从以下六个方面依次分析：

### 1. 现场环境对比分析
- 判断现场是否为标准施工环境（如围挡、标识、材料堆放等是否规范）  
- 分析图像中是否存在与小模型结果不一致之处  

### 2. 工人活动与状态识别
- 判断工人是否处于工作、休息、操作机械等状态  
- 补充小模型未提及的行为识别，如抽烟、玩手机、疲劳操作等  

### 3. 施工工具与机械使用情况
- 是否存在危险工具未妥善存放、机械无防护操作等现象  
- 工人是否正确使用工具或机械设备  

### 4. 安全规范与隐患评估
- 对照小模型结果，判断工人是否全面佩戴防护装备，如安全帽、背心、口罩等  
- 判断是否存在违章作业或安全死角  

### 5. 多人协作与现场动态
- 分析是否存在多人协作、交叉作业等情况，是否有配合不当的风险  
- 判断人群密集度是否合理，有无潜在碰撞风险  

### 6. 总结与工人行为概况
- 总结工人整体的安全行为状态  
- 结合小模型数据和图像内容，提出改进建议或重点关注点  

---

**要求：**
- 不要盲目信任小模型的结果，如发现其误判，应明确指出  
- 输出结构清晰、逻辑严谨、语言客观，便于用于后续生成安全分析报告  
- 若某方面缺乏信息支持，可说明 “不足以判断” 并说明原因  
"""

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
            prompt = multiple_frames_prompt

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


async def deep_describe_frame(
    frame_path: str,
    tool_model: ToolModel,
    prompt: str
):
    if tool_model is None:
        yield "tool_model is None"

    try:
        op = get_op()

        file_data = op.read(frame_path)
        b64 = base64.encodebytes(file_data).decode("utf-8")
        b64_with_header = f"data:image/jpeg;base64,{b64}"
        vl_model = get_model(tool_model)

        prompt = single_frame_deep_analyze_prompt.replace("{{yolo_result}}", prompt)

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


async def describe_frames(
    frame_paths: List[str],
    tool_model,
    prompt: Optional[str] = None,
) -> AsyncGenerator[Any, Any]:
    if tool_model is None:
        yield "tool_model is None"
        return

    try:
        op = get_op()
        vl_model = get_model(tool_model)

        if prompt is None:
            prompt = describe_prompt["text"]

        # 构建图像部分的内容列表
        image_contents = []
        for path in frame_paths:
            file_data = op.read(path)
            b64 = base64.encodebytes(file_data).decode("utf-8")
            b64_with_header = f"data:image/jpeg;base64,{b64}"

            image_contents.append(
                {"type": "image_url", "image_url": {"url": b64_with_header}}
            )

        # 构建完整的消息内容（多张图 + 文本 prompt）
        user_content = [{"type": "text", "text": prompt}] + image_contents

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
                    "content": user_content,
                },
            ],
        )

        # 处理流式输出
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content"):
                yield delta.content

    except Exception as e:
        logger.error(f"Error in describe_frames: {e}")
    finally:
        yield "[DONE]"
