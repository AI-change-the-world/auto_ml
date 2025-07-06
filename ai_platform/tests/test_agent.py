import os
import urllib.parse

import json5
from qwen_agent.agents import Assistant
from qwen_agent.tools.base import BaseTool, register_tool


# 注册自定义图像生成工具
@register_tool("my_image_gen")
class MyImageGen(BaseTool):
    description = (
        "AI 绘画（图像生成）服务，输入文本描述，返回基于文本信息绘制的图像 URL。"
    )
    parameters = [
        {
            "name": "prompt",
            "type": "string",
            "description": "期望的图像内容的详细描述",
            "required": True,
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        prompt = json5.loads(params)["prompt"]
        prompt = urllib.parse.quote(prompt)
        return json5.dumps(
            {"image_url": f"https://image.pollinations.ai/prompt/{prompt}"},
            ensure_ascii=False,
        )


# LLM 配置
llm_cfg = {
    "model": "qwen3-235b-a22b",
    "model_type": "qwen_dashscope",
    "api_key": os.getenv("OPENAI_API_KEY"),
    "generate_cfg": {"top_p": 0.8, "enable_thinking": False},
}

# 系统指令（可以简化，聚焦图像生成）
system_instruction = """你是一个图像生成助手，用户输入图像描述后，你调用 my_image_gen 工具生成图像，并返回图像的 URL。请用中文简洁回复。"""

# 创建智能体
tools = ["my_image_gen"]
bot = Assistant(llm=llm_cfg, system_message=system_instruction, function_list=tools)


# === 封装成函数 ===
def generate_image(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    response_text = ""
    for chunk in bot.run(messages=messages, stream=False):
        print(chunk, end="", flush=True)
        # response_text += chunk
    return response_text.strip()


# === 示例调用 ===
if __name__ == "__main__":
    prompt = "正面平视视角拍摄的光伏电池组件特写，完整展示8×12块深蓝色硅片组成的矩形阵列。每块硅片表面布满不规则网状裂纹，玻璃封装层呈现清晰的蛛网式破裂纹理，裂纹边缘带有细微高光反射。背景为冷调金属质感的工业车间环境，左侧45°强侧光照射突出玻璃裂痕的立体深度，工业摄影风格，超高细节写实画质，比例3:4"
    result = generate_image(prompt)
    print("生成图像的URL：", result)
