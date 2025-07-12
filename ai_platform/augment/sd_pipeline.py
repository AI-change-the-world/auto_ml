import random

import torch
from diffusers import (
    AutoPipelineForImage2Image,
    AutoPipelineForInpainting,
    AutoPipelineForText2Image,
)
from PIL import Image, ImageDraw

model_path = "/root/models/sd35"


class StableDiffusionUnified:
    def __init__(
        self, model_path: str, device: str = "cuda", torch_dtype=torch.float16
    ):
        self._base = AutoPipelineForText2Image.from_pretrained(
            model_path,
            torch_dtype=torch_dtype,
        ).to(device)

        # 共享 base 构建 img2img 和 inpaint
        self._pipeline_img2img = AutoPipelineForImage2Image.from_pipe(self._base)
        self._pipeline_inpaint = AutoPipelineForInpainting.from_pipe(self._base)
        self.device = device

    def text2img(
        self,
        prompt: str,
        width=512,
        height=512,
        steps=30,
        guidance_scale=7.5,
        seed=None,
    ) -> Image.Image:
        generator = torch.manual_seed(seed) if seed else None
        return self._base(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]

    def img2img(
        self,
        prompt: str,
        image: Image.Image,
        strength=0.5,
        steps=30,
        guidance_scale=7.5,
        seed=None,
    ) -> Image.Image:
        generator = torch.manual_seed(seed) if seed else None
        return self._pipeline_img2img(
            prompt=prompt,
            image=image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]

    def inpaint(
        self,
        prompt: str,
        image: Image.Image,
        mask: Image.Image,
        steps=30,
        guidance_scale=7.5,
        seed=None,
    ) -> Image.Image:
        generator = torch.manual_seed(seed) if seed else None
        return self._pipeline_inpaint(
            prompt=prompt,
            image=image,
            mask_image=mask,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]


def generate_prompt(region_defects):
    chosen = [random.choice(r["possible_defects"]) for r in region_defects]
    return "Add realistic minor architectural defects such as " + ", ".join(chosen)


def generate_mask(image_size, bboxes):
    mask = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask)
    for bbox in bboxes:
        draw.rectangle(bbox, fill=255)
    return mask.convert("RGB")


def make_bottom_mask(image: Image, mask_height_ratio=0.15):
    w, h = image.size
    mask = Image.new("L", (w, h), 0)  # 全黑
    draw = ImageDraw.Draw(mask)
    draw.rectangle([0, int(h * (1 - mask_height_ratio)), w, h], fill=255)  # 画底部白条
    return mask.convert("RGB")


def refine_bbox(bbox, image_size, scale=0.2):
    """缩小原始 bbox 为更小的 mask 区域"""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    nw, nh = w * scale, h * scale
    rx0 = max(0, int(cx - nw / 2))
    ry0 = max(0, int(cy - nh / 2))
    rx1 = min(image_size[0], int(cx + nw / 2))
    ry1 = min(image_size[1], int(cy + nh / 2))
    return [rx0, ry0, rx1, ry1]


def inpaint(
    image: Image,
    mask: Image,
    sd: StableDiffusionUnified,
    prompt: str = "natural background, photorealistic",
):
    return sd.inpaint(prompt, image, mask)


if __name__ == "__main__":
    import base64
    import json
    import os

    from openai import OpenAI

    vl_model = OpenAI(
        api_key=os.environ.get("APIKEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    sd = StableDiffusionUnified(model_path=model_path)
    img_path = "./train/20240518110431.jpg"

    def encode_image_to_base64(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    img_base64 = encode_image_to_base64(img_path)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
请从图像中识别可能出现细微建筑缺陷的位置，例如墙面轻微裂缝、剥落、地面污渍等。

要求：
1. **缺陷应为小范围区域**（不应包含整面墙或整片地面）。
2. **缺陷区域要贴近真实场景，尽量靠边角或边缘**。
3. 每个缺陷输出格式为：{
   "possible_defects": 缺陷类型,
   "region": 所在区域（如墙、地面、柱子等）,
   "bbox": 缺陷区域的边界框 [x0, y0, x1, y1]
}

只返回 2~4 个缺陷区域。

请以如下 JSON 格式输出：
[
  {"region": "墙面", "bbox": [x0, y0, x1, y1], "possible_defects": ["裂缝", "掉漆", "霉斑"]},
  {"region": "地面", "bbox": [x0, y0, x1, y1], "possible_defects": ["水渍", "污渍"]},
  ...
]
                """,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}",
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

    result = (
        completion.choices[0].message.content.replace("```json", "").replace("```", "")
    )
    region_info = []
    try:
        region_info = json.loads(result)
    except:
        print(f"JSON 解析失败====> {result}")
    ori_image = Image.open(img_path)
    refined_region_info = []
    for region in region_info:
        refined_bbox = refine_bbox(region["bbox"], ori_image.size, scale=0.2)
        refined_region_info.append(
            {
                "region": region["region"],
                "bbox": refined_bbox,
                "possible_defects": region["possible_defects"],
            }
        )
    mask = generate_mask(ori_image.size, [r["bbox"] for r in refined_region_info])
    mask.save("output_mask.png")
    prompt = generate_prompt(region_info)
    print(f"[Prompt] {prompt}")

    inpainted = inpaint(ori_image, mask, sd, prompt=prompt)
    inpainted.save("output_inpaint.png")


# if __name__ == "__main__":
#     from time import sleep

#     def create_blank_image(size=(512, 512), color=(255, 255, 255)):
#         return Image.new("RGB", size, color)

#     def create_full_white_mask(size=(512, 512)):
#         return Image.new("L", size, 255)

#     def create_local_mask(size=(512, 512), box=(200, 200, 300, 300)):
#         mask = Image.new("L", size, 0)
#         for x in range(box[0], box[2]):
#             for y in range(box[1], box[3]):
#                 mask.putpixel((x, y), 255)
#         return mask

#     sd = StableDiffusionUnified(model_path=model_path)

#     # 示例 1：text2img
#     print("Generating from text...")
#     img1 = sd.text2img(prompt="a futuristic city under sunset")
#     img1.save("output_text2img.png")

#     # 示例 2：img2img（保留原图结构，只做细微调整）
#     print("Generating from reference image...")
#     ref_img = img1  # 用前面那张生成的图为参考
#     img2 = sd.img2img(
#         prompt="same city with some flying cars", image=ref_img, strength=0.2
#     )
#     img2.save("output_img2img.png")

#     # 示例 3：inpainting（遮盖一个区域再生成）
#     print("Inpainting a region...")
#     mask = create_local_mask(size=img2.size, box=(150, 150, 300, 300))
#     img3 = sd.inpaint(
#         prompt="replace the region with a giant floating orb",
#         image=img2,
#         mask=mask,
#     )
#     img3.save("output_inpaint.png")

#     sleep(20)
