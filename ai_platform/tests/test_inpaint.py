import base64
import cv2
import numpy as np
import json
import os
from openai import OpenAI

# ========== 配置 ==========
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(
    api_key=openai_api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

IMAGE_SIZE = (256, 256)  # 固定尺寸

# ========== 工具函数 ==========


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def call_mllm_find_bbox(original_img_path, generated_img_path):
    base64_orig = encode_image(original_img_path)
    base64_gen = encode_image(generated_img_path)

    prompt = """
你是一位经验丰富的皮革质量检测员，请对比以下两张 256x256 的皮革图像：

- 第一张图像是原始、无缺陷的皮革图；
- 第二张图像是通过 GAN 生成的皮革图，可能存在以下缺陷类型：
  - 局部纹理重复（如相邻区域出现类似的花纹块）
  - 局部颜色异常（色块偏暗、偏亮或颜色失真）
  - 局部结构扭曲（形状异常或边缘模糊）
  - 小范围孔洞或裂纹
  - 轻微的噪点或伪影

请你：
1. 只标记那些明显且局部的缺陷区域，忽略整体轻微差异；
2. 不要把皮革的自然纹理或正常色差误判为缺陷；
3. 返回缺陷区域的矩形框（bbox）和简短说明；
4. 如果没有缺陷，返回空数组 `[]`；
5. 所有坐标都在 `[0,256)` 内，整数。

⚠️ 仅返回严格的 JSON 格式：

```json
[
  {"bbox": [x1, y1, x2, y2], "reason": "简短描述缺陷"},
  ...
]


    """

    print("🚀 调用 多模态 开始分析图像差异...")

    response = client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_orig}"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_gen}"},
                    },
                ],
            }
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    content = response.choices[0].message.content.strip()
    print("🧠 MLLM 返回内容：\n", content)

    content = content.replace("```json", "").replace("```", "")

    try:
        bbox_data = json.loads(content)
        return bbox_data
    except json.JSONDecodeError:
        print("⚠️ 无法解析 GPT 返回的 JSON，请检查格式")
        return []


def generate_mask_from_bboxes(image_size, bbox_json, mask_path="mask.png"):
    print(f"🚀 生成 mask {bbox_json}")
    mask = np.zeros(image_size, dtype=np.uint8)
    for item in bbox_json:
        x1, y1, x2, y2 = item["bbox"]
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    cv2.imwrite(mask_path, mask)
    print(f"✅ 保存 mask 到：{mask_path}")
    return mask


# ========== 主流程 ==========


def run(original_img_path, generated_img_path, output_mask_path="mask.png"):
    bbox_data = call_mllm_find_bbox(original_img_path, generated_img_path)
    if not bbox_data:
        print("❌ 无法获取有效的 bbox，终止。")
        return
    generate_mask_from_bboxes(IMAGE_SIZE, bbox_data, output_mask_path)


# ========== 示例调用 ==========
if __name__ == "__main__":
    run(
        r"D:/github_repo/auto_ml/ai_platform/gan/good/0.png",
        r"D:\github_repo\auto_ml\ai_platform\augment\simple_gan\fake_sample_1.png",
        "mask.png",
    )
