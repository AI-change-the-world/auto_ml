from openai import OpenAI
import base64
import os

vl_model = OpenAI(
    api_key=os.environ.get("APIKEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# 1. 输入图像路径
real_img_path = "D:/github_repo/auto_ml/ai_platform/gan/good/0.png"
gen_img_path = "D:/github_repo/auto_ml/ai_platform/gan/good/1.png"

# 2. 编码图像为 base64
real_img_b64 = encode_image(real_img_path)
gen_img_b64 = encode_image(gen_img_path)

# 3. 构造 ChatPrompt
messages = [
    {
        "role": "system",
        "content": (
            "你是一位专业图像分析师，擅长分析两张图像之间的视觉相似性、结构差异和语义一致性。"
            "请先描述两张图像的内容，然后判断它们是否属于同一场景或数据分布，接着指出细节差异，最后打分并总结。"
            "请输出结构化结果，便于程序提取评分与分析信息。"
        ),
    },
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "以下是两张图像，请你：\n"
                    "1. 分别描述图像A 和 图像B 的内容；\n"
                    "2. 判断它们是否来自同一类真实场景或数据分布；\n"
                    "3. 指出具体差异点（如纹理、色彩、结构等方面）；\n"
                    "4. 给出一个 0~100 的相似度评分（越高越相似）；\n"
                    "5. 总结是否存在显著差异。\n\n"
                    "请严格按照以下结构化格式输出：\n\n"
                    "相似度评分：<0~100 的整数>\n"
                    "评估结果：<简要总结，如“差异不显著”、“基本一致”、“存在显著结构差异”等>\n"
                    "差异分析：\n"
                    "- 图像内容描述：\n"
                    "  - 图像A：<描述>\n"
                    "  - 图像B：<描述>\n"
                    "- 纹理差异：<描述>\n"
                    "- 色彩差异：<描述>\n"
                    "- 结构差异：<描述>\n"
                    "- 其他观察：<描述>"
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{real_img_b64}",
                    "detail": "high",
                },
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{gen_img_b64}",
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
    temperature=0.2,
)

# 5. 输出结果
print("\n=== 评估结果 ===\n")
print(completion.choices[0].message.content)
