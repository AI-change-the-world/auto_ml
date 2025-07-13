import lpips
import torch

from label.client import get_model
from label.tools import base64_to_cv2_image

loss_fn = lpips.LPIPS(net="squeeze")


# 转相似度
def lpips_to_similarity(lpips_distance, max_lpips=0.5):
    lpips_clamped = min(lpips_distance, max_lpips)
    similarity = (1 - lpips_clamped / max_lpips) * 100
    return round(similarity, 2)


def cnn_measure(img1: str, img2: str) -> float:
    """
    Measure the similarity between two images.
    """
    cv_mat1 = base64_to_cv2_image(img1)
    cv_tensor = lpips.im2tensor(cv_mat1)
    cv_mat2 = base64_to_cv2_image(img2)
    cv_tensor2 = lpips.im2tensor(cv_mat2)

    with torch.no_grad():
        dist: torch.Tensor = loss_fn(cv_tensor, cv_tensor2)
    return lpips_to_similarity(dist.item())


def openai_measure(img1: str, img2: str, tool_model) -> str:
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
                        "url": f"data:image/jpeg;base64,{img1}",
                        "detail": "high",
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img2}",
                        "detail": "high",
                    },
                },
            ],
        },
    ]

    vl_model = get_model(tool_model)

    completion = vl_model.chat.completions.create(
        model="qwen-vl-max-latest",
        # model = "moonshot-v1-128k-vision-preview",
        max_tokens=1024,
        messages=messages,
        temperature=0.2,
    )

    return completion.choices[0].message.content
