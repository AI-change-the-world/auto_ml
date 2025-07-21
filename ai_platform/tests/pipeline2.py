"""
an unfinished concrete wall in a construction site,
realistic texture, visible holes and cracks, stained surface, water streaks,
rough cement wall, highly detailed, photorealistic


no painting, no furniture, no clean surface, no smooth wall, no render, 
no text, no watermark
"""


import base64
import os

from openai import OpenAI

# 配置你的 OpenAI API key 和 base url（用于 Qwen-VL 模型）
api_key = os.getenv("OPENAI_API_KEY")

vl_model = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

img = r"D:\fh_project\dataset\images\val_reshape\20241231084955.jpg"

# 读取图像并 base64 编码
with open(img, "rb") as f:
    img_bytes = f.read()
    base64_img = base64.b64encode(img_bytes).decode("utf-8")

# 构建消息
messages = [
    {
        "role": "system",
        "content": "你是一个专业的图像分析与提示词生成助手，任务是根据用户提供的参考图像内容，分析其场景、风格、元素，然后自动生成用于 img2img 任务的 prompt 和 negative prompt。",
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "你是一个专业的图像分析助手。请根据下方图像，分析其内容，并返回适用于 Stable Diffusion img2img 模式的 prompt 和 negative_prompt。"
                    "\n\n"
                    "请返回如下格式的 JSON：\n"
                    "{\n"
                    '  "prompt": "...",\n'
                    '  "negative_prompt": "..."\n'
                    "}\n\n"
                    "要求：\n"
                    "- prompt 为英文，描述图像内容的真实感构图、细节、风格修饰词。\n"
                    "- negative_prompt 包括不希望出现的内容，例如模糊、卡通、低质量、低分辨率、动漫风格等。\n"
                    "- 风格整体偏真实，不要夸张艺术处理。\n"
                    "- 严格输出 JSON 格式，不能输出自然语言说明。\n"
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_img}"},
            },
        ],
    },
]

# 调用接口
completion = vl_model.chat.completions.create(
    model="qwen-vl-max-latest",
    # model = "moonshot-v1-128k-vision-preview",
    max_tokens=256,
    messages=messages,
    temperature=0.7,
)

# 解析结果
response = completion.choices[0].message.content
print("💡 Prompt 和 Negative Prompt：")
print(response)
