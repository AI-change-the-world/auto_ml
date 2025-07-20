import random
from typing import List, Optional

import cv2
import numpy as np
import torch
from diffusers import (
    StableDiffusion3Img2ImgPipeline,
    StableDiffusion3InpaintPipeline,
    StableDiffusion3Pipeline,
)
from PIL import Image, ImageDraw

from base.logger import logger

model_path = "/root/models/sd3m"

reserved_lora_modules = {
    "pcb": {
        "path": "/root/lora/pcb/sd3_Pictures_20240920_0/pytorch_lora_weights.safetensors",
        "prompt": "a macro photo of sks leather with a small dent and fine surface wrinkles",
    },
    "leather": {
        "path": "/root/lora/lora_feather_m/pytorch_lora_weights.safetensors",
        "prompt": "a photo of sks pcb contain 8 defects",
    },
}


class StableDiffusionUnified:
    def __init__(
        self,
        model_path: str,
        enable_img2img: bool = False,
        enable_inpaint: bool = False,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._base = StableDiffusion3Pipeline.from_pretrained(
            model_path, torch_dtype=torch.float16, device_map="balanced"  # 自动分配部分模块到 CPU
        )
        self._enable_img2img = enable_img2img
        self._enable_inpaint = enable_inpaint
        if enable_img2img:
            self._pipeline_img2img = StableDiffusion3Img2ImgPipeline.from_pipe(
                self._base
            )
        if enable_inpaint:
            self._pipeline_inpaint = StableDiffusion3InpaintPipeline.from_pipe(
                self._base
            )
        logger.info(
            f"stable diffusion max token length: {self._base.tokenizer.model_max_length}",
        )
        self._enabled_loras = []

    def enable_lora(self, lora_name: str):
        if lora_name in reserved_lora_modules:
            self._base.load_lora_weights(
                reserved_lora_modules[lora_name]["path"], adapter_name=lora_name
            )
            self._enabled_loras.append(lora_name)
            self._base.set_adapters(self._enabled_loras)
            logger.info(f"enable lora: {lora_name}")

    def disable_lora(self, lora_name: str):
        if lora_name in self._enabled_loras:
            self._enabled_loras.remove(lora_name)
            self._base.set_adapters(self._enabled_loras)
            logger.info(f"disable lora: {lora_name}")

    def text2img(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        num_images_per_prompt: int = 1,
        output_type: str = "pil",
    ) -> List[Image.Image]:
        generator = torch.manual_seed(seed) if seed is not None else None
        result = self._base(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
            num_images_per_prompt=num_images_per_prompt,
            output_type=output_type,
        )
        return result.images

    def img2img(
        self,
        prompt: str,
        image: Image.Image,
        strength: float = 0.5,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        num_images_per_prompt: int = 1,
        output_type: str = "pil",
    ) -> Optional[List[Image.Image]]:
        if not self._enable_img2img:
            logger.warning("img2img is not enabled.")
            return None

        generator = torch.manual_seed(seed) if seed is not None else None
        result = self._pipeline_img2img(
            prompt=prompt,
            prompt_3=prompt,
            image=image,
            strength=strength,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
            num_images_per_prompt=num_images_per_prompt,
            output_type=output_type,
            max_sequence_length=512,
        )
        return result.images

    def inpaint(
        self,
        prompt: str,
        image: Image.Image,
        mask: Image.Image,
        steps: int = 30,
        strength: float = 0.5,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        num_images_per_prompt: int = 1,
        output_type: str = "pil",
    ) -> Optional[List[Image.Image]]:
        if not self._enable_inpaint:
            logger.warning("inpaint is not enabled.")
            return None

        generator = torch.manual_seed(seed) if seed is not None else None

        # 确保 mask 与 image 同尺寸
        if mask.size != image.size:
            mask = mask.resize(image.size)

        result = self._pipeline_inpaint(
            prompt=prompt,
            image=image,
            mask_image=mask,
            strength=strength,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
            num_images_per_prompt=num_images_per_prompt,
            output_type=output_type,
        )
        return result.images


def generate_prompt(region_defects):
    chosen = [random.choice(r["possible_defects"]) for r in region_defects]
    return "Add realistic minor architectural defects such as " + ", ".join(chosen)


def generate_mask(image_size, bboxes):
    """bboxes  left, top, right, bottom"""
    mask = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(mask)
    for bbox in bboxes:
        draw.rectangle(bbox, fill=255)
    return mask.convert("RGB")


def inject_gaussian_noise_to_image(
    image: Image.Image,
    bboxes: list[list[int]],
    mean: float = 0,
    std: float = 15,
    seed: int = None,
) -> Image.Image:
    """
    在原图图像中指定 bbox 区域内注入高斯噪声，模拟墙面脏污/裂缝引导。
    """
    if seed is not None:
        np.random.seed(seed)

    img_array = np.array(image).astype(np.float32)

    for bbox in bboxes:
        x1, y1, x2, y2 = map(int, bbox)
        roi = img_array[y1:y2, x1:x2]
        noise = np.random.normal(mean, std, roi.shape)
        roi += noise
        roi = np.clip(roi, 0, 255)
        img_array[y1:y2, x1:x2] = roi

    return Image.fromarray(img_array.astype(np.uint8))


def generate_irregular_mask_in_bbox(
    image_size: tuple[int, int],
    bboxes: list[list[int]],
    num_blobs_per_box: int = 6,
    min_radius: int = 10,
    max_radius: int = 30,
) -> Image.Image:
    """
    在指定 bboxes 内生成不规则形状的 mask 区域。

    Returns:
        黑底白字 RGB mask，适用于 inpainting。
    """
    h, w = image_size
    mask = np.zeros((h, w), dtype=np.uint8)

    for bbox in bboxes:
        x1, y1, x2, y2 = map(int, bbox)
        for _ in range(num_blobs_per_box):
            x = np.random.randint(x1, x2)
            y = np.random.randint(y1, y2)
            r = np.random.randint(min_radius, max_radius)
            cv2.circle(mask, (x, y), r, 255, -1)

    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
    return Image.fromarray(mask).convert("L").convert("RGB")


def inject_salt_and_pepper_noise_to_image(
    image: Image.Image,
    bboxes: list[list[int]],
    noise_density: float = 0.2,
    pepper_ratio: float = 0.5,
    seed: int = None,
) -> Image.Image:
    """
    在原图中指定区域注入椒盐噪声，用于引导 SD inpaint 注意这些区域。

    参数：
        image: 原始图像 (PIL.Image)
        bboxes: 噪声区域 [[x1,y1,x2,y2], ...]
        noise_density: 噪声密度（0 ~ 1）
        pepper_ratio: 噪声中黑点比例
        seed: 随机种子
    返回：
        修改后的 PIL 图像
    """
    if seed is not None:
        np.random.seed(seed)

    img_array = np.array(image).copy()

    for bbox in bboxes:
        x1, y1, x2, y2 = map(int, bbox)
        x1 = max(0, min(x1, image.width))
        x2 = max(0, min(x2, image.width))
        y1 = max(0, min(y1, image.height))
        y2 = max(0, min(y2, image.height))

        roi = img_array[y1:y2, x1:x2]
        h, w, c = roi.shape
        num_pixels = h * w
        num_noise = int(noise_density * num_pixels)
        num_pepper = int(num_noise * pepper_ratio)
        num_salt = num_noise - num_pepper

        # pepper: black pixels
        for _ in range(num_pepper):
            y, x = np.random.randint(0, h), np.random.randint(0, w)
            roi[y, x] = [0, 0, 0]

        # salt: white pixels
        for _ in range(num_salt):
            y, x = np.random.randint(0, h), np.random.randint(0, w)
            roi[y, x] = [255, 255, 255]

    return Image.fromarray(img_array)


def generate_irregular_mask_in_bbox(
    image_size: tuple[int, int],
    bboxes: list[list[int]],
    num_blobs_per_box: int = 6,
    min_radius: int = 10,
    max_radius: int = 30,
) -> Image.Image:
    """
    在指定 bboxes 内生成不规则形状的 mask 区域。

    Returns:
        黑底白字 RGB mask，适用于 inpainting。
    """
    h, w = image_size
    mask = np.zeros((h, w), dtype=np.uint8)

    for bbox in bboxes:
        x1, y1, x2, y2 = map(int, bbox)
        for _ in range(num_blobs_per_box):
            x = np.random.randint(x1, x2)
            y = np.random.randint(y1, y2)
            r = np.random.randint(min_radius, max_radius)
            cv2.circle(mask, (x, y), r, 255, -1)

    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
    return Image.fromarray(mask).convert("L").convert("RGB")


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


def add_global_gaussian_noise(
    image: Image.Image, std: float = 15.0, seed: int = None
) -> Image.Image:
    """
    向整张图像添加高斯噪声，模拟真实纹理扰动。
    """
    if seed is not None:
        np.random.seed(seed)

    img_np = np.array(image).astype(np.float32)
    noise = np.random.normal(0, std, img_np.shape)
    img_noised = img_np + noise
    img_noised = np.clip(img_noised, 0, 255).astype(np.uint8)
    return Image.fromarray(img_noised)


def generate_global_random_mask(
    image_size: tuple[int, int], num_blobs: int = 20
) -> Image.Image:
    """
    在整张图上生成随机不规则 blob mask，引导 SD inpaint 更自然修改。
    """
    h, w = image_size
    mask = np.zeros((h, w), dtype=np.uint8)

    for _ in range(num_blobs):
        x, y = np.random.randint(0, w), np.random.randint(0, h)
        r = np.random.randint(20, 40)
        cv2.circle(mask, (x, y), r, 255, -1)

    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
    return Image.fromarray(mask).convert("L").convert("RGB")


def inpaint(
    image: Image,
    mask: Image,
    sd: StableDiffusionUnified,
    prompt: str = "natural background, photorealistic",
):
    return sd.inpaint(prompt, image, mask)


if __name__ == "__main__":
    import os

    sd = StableDiffusionUnified(model_path=model_path)
    ref_image_path = "result.png"
    mask_img_path = "mask.png"
    ref_image = Image.open(ref_image_path).convert("RGB").resize((1024, 1024))
    mask = Image.open(mask_img_path).convert("RGB")

    result_images = sd.inpaint(
        prompt="A realistic rooftop scene with subtle surface defects, like hairline cracks on tiles and slight wall spalling. Photorealistic lighting, consistent shadows, high detail, no overexposure, smooth edges, seamless integration of defect areas, realistic construction materials.",
        negative_prompt="cartoon, drawing, 3d, low quality, low resolution, blurry, unrealistic defect, overexposed, jagged edges, obvious collage, distorted geometry",
        image=ref_image,
        mask=mask,
        strength=0.8,
        steps=20,
        guidance_scale=7.5,
        seed=12345,
        num_images_per_prompt=5,
        output_type="pil",
    )
    for i, img in enumerate(result_images):
        img.save(os.path.join(f"result_{i}.png"))


# if __name__ == "__main__":
#     import os

#     sd = StableDiffusionUnified(model_path=model_path)
#     ref_image_path = "ref.jpg"
#     ref_image = Image.open(ref_image_path).convert("RGB").resize((1024, 1024))

#     bbox_wall = [[30, 30, 300, 480]]  # 你可根据白墙区域手动微调

#     # 注入高斯噪声
#     # noised_image = add_global_gaussian_noise(ref_image, std=20, seed=42)

#     # noised_image.save("noised_image.png")
#     mask = generate_global_random_mask((1024, 1024))
#     mask.save("mask.png")

#     result_images = sd.inpaint(
#         prompt="fine cracks on the white wall, peeling paint, construction defects, realistic texture",
#         negative_prompt="cartoon, blur, unrealistic, clean surface, smooth, painting",
#         image=ref_image,
#         mask=mask,
#         steps=20,
#         guidance_scale=6.5,
#         seed=12345,
#         num_images_per_prompt=3,
#         output_type="pil",
#     )
#     for i, img in enumerate(result_images):
#         img.save(os.path.join(f"result_{i}.png"))

# if __name__ == "__main__":
#     import base64
#     import os

#     from openai import OpenAI

#     vl_model = OpenAI(
#         api_key=os.environ.get("APIKEY"),
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )

#     def encode_image_to_base64(image_path):
#         with open(image_path, "rb") as f:
#             return base64.b64encode(f.read()).decode("utf-8")

#     def build_defect_prompt(base_prompt: str, defect_type: str = "crack on wall"):
#         return f"{base_prompt.strip()}, showing a subtle and realistic {defect_type}"

#     def describe_image_with_vl(
#         client: OpenAI,
#         image_path: str,
#         system_prompt: str = "You are a helpful assistant that describes images.",
#         model_name: str = "qwen-vl-max-latest",
#     ) -> str:
#         image_b64 = encode_image_to_base64(image_path)
#         messages = [
#             {
#                 "role": "system",
#                 "content": system_prompt
#                 or "You are a helpful assistant that describes images for image-to-image generation.",
#             },
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "image_url",
#                         "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
#                     },
#                     {
#                         "type": "text",
#                         "text": "Please describe this image in a realistic, detailed prompt suitable for Stable Diffusion img2img tasks. Focus on materials, lighting, environment and realism.",
#                     },
#                 ],
#             },
#         ]

#         response = client.chat.completions.create(
#             model=model_name,
#             messages=messages,
#             max_tokens=200,
#             temperature=0.7,
#         )
#         return response.choices[0].message.content

#     sd = StableDiffusionUnified(model_path=model_path)

#     # === 读取参考图像 ===
#     ref_image_path = "ref.jpg"

#     # 1. 描述原图
#     print("🔍 Describing image...")
#     base_prompt = describe_image_with_vl(vl_model,ref_image_path)
#     print("✅ Base Prompt:", base_prompt)

#     # 2. 构建缺陷 prompt
#     prompt = build_defect_prompt(base_prompt, "crack on wall")
#     negative_prompt = "painting, cartoon, lowres, unrealistic, anime, 3d render"


#     ref_image = (
#         Image.open(ref_image_path).convert("RGB").resize((768, 512))
#     )  # 3:2 建筑图常用比例

#     # # === 构造高质量 prompt ===
#     # prompt = (
#     #     "A realistic construction site with cranes, scaffolding, partially built concrete buildings, and workers in safety vests. "
#     #     "Dusty ground, industrial materials, cloudy sky. Photographed with a DSLR, wide-angle, photorealistic, daytime documentary style."
#     # )

#     # negative_prompt = "blurry, cartoon, painting, anime, fantasy, cgi, oversaturated, low quality, smooth, unrealistic, digital art"

#     # === 使用 img2img 生成图像 ===
#     result_images = sd.img2img(
#         prompt=prompt,
#         negative_prompt=negative_prompt,
#         image=ref_image,
#         strength=0.45,  # 越低越像原图（0.3~0.6 建议）
#         steps=40,
#         guidance_scale=6.5,
#         seed=12345,
#         num_images_per_prompt=3,
#         output_type="pil",
#     )

#     # === 保存输出 ===
#     for i, img in enumerate(result_images):
#         img.save(f"generated_{i}.png")

#     print("✅ 图像生成完成，共生成", len(result_images), "张")


# if __name__ == "__main__":
#     import base64
#     import json
#     import os

#     from openai import OpenAI

#     vl_model = OpenAI(
#         api_key=os.environ.get("APIKEY"),
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )
#     sd = StableDiffusionUnified(model_path=model_path)
#     img_path = "./train/20240518110431.jpg"

#     def encode_image_to_base64(image_path):
#         with open(image_path, "rb") as f:
#             return base64.b64encode(f.read()).decode("utf-8")

#     img_base64 = encode_image_to_base64(img_path)

#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": """
# 请从图像中识别可能出现细微建筑缺陷的位置，例如墙面轻微裂缝、剥落、地面污渍等。

# 要求：
# 1. **缺陷应为小范围区域**（不应包含整面墙或整片地面）。
# 2. **缺陷区域要贴近真实场景，尽量靠边角或边缘**。
# 3. 每个缺陷输出格式为：{
#    "possible_defects": 缺陷类型,
#    "region": 所在区域（如墙、地面、柱子等）,
#    "bbox": 缺陷区域的边界框 [x0, y0, x1, y1]
# }

# 只返回 2~4 个缺陷区域。

# 请以如下 JSON 格式输出：
# [
#   {"region": "墙面", "bbox": [x0, y0, x1, y1], "possible_defects": ["裂缝", "掉漆", "霉斑"]},
#   {"region": "地面", "bbox": [x0, y0, x1, y1], "possible_defects": ["水渍", "污渍"]},
#   ...
# ]
#                 """,
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/png;base64,{img_base64}",
#                         "detail": "high",
#                     },
#                 },
#             ],
#         },
#     ]

#     completion = vl_model.chat.completions.create(
#         model="qwen-vl-max-latest",
#         # model = "moonshot-v1-128k-vision-preview",
#         max_tokens=1024,
#         messages=messages,
#         temperature=0.7,
#     )

#     result = (
#         completion.choices[0].message.content.replace("```json", "").replace("```", "")
#     )
#     region_info = []
#     try:
#         region_info = json.loads(result)
#     except:
#         print(f"JSON 解析失败====> {result}")
#     ori_image = Image.open(img_path)
#     refined_region_info = []
#     for region in region_info:
#         refined_bbox = refine_bbox(region["bbox"], ori_image.size, scale=0.2)
#         refined_region_info.append(
#             {
#                 "region": region["region"],
#                 "bbox": refined_bbox,
#                 "possible_defects": region["possible_defects"],
#             }
#         )
#     mask = generate_mask(ori_image.size, [r["bbox"] for r in refined_region_info])
#     mask.save("output_mask.png")
#     prompt = generate_prompt(region_info)
#     print(f"[Prompt] {prompt}")

#     inpainted = inpaint(ori_image, mask, sd, prompt=prompt)
#     inpainted.save("output_inpaint.png")


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
