import asyncio
import base64
import functools
import io
import json
import random
import traceback
import uuid
from typing import Optional

import torch
from fastapi import APIRouter, Depends
from openai import OpenAI
from PIL import Image
from sqlalchemy.orm import Session
from sse_starlette import EventSourceResponse

from augment.measure import cnn_measure, openai_measure
from augment.req_and_resp import *
from augment.sd_pipeline import StableDiffusionUnified, reserved_lora_modules
from augment.simple_gan.model import Generator as Model
from base import create_response
from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from base.nacos_config import get_db
from db.tool_model.tool_model_crud import get_tool_model
from label.client import get_model
from label.tools import base64_to_pil_image, pil_to_base64

model_path = "generator.pth"

model = Model(z_dim=2048, img_channels=3).to("cpu")
model.load_state_dict(torch.load(model_path))


router = APIRouter(
    prefix="/augment",
    tags=["Augment"],
)

__RESERVED_NEGATIVE_PROMPT__ = "cartoon, drawing, 3d, low quality, low resolution, blurry, unrealistic defect, overexposed, jagged edges, obvious collage, distorted geometry"


# TODO merge to augment, just for demo
@router.post("/gan/generate/stream")
async def gan_generate_stream(req: GANRequest):
    """Stream-generated images from the GAN model"""

    async def image_generator():
        operator = get_operator(s3_properties.augment_bucket_name)
        with torch.no_grad():
            z = torch.randn(req.count, 2048).to("cpu")
            generated_image = model(z)
            generated_image = (generated_image * 0.5) + 0.5
            # print(f"shape. {generated_image.shape}" )
            for img_tensor in generated_image:
                img_tensor = (
                    img_tensor.permute(1, 2, 0).clamp(0, 1).mul(255).byte().numpy()
                )
                pil_img = Image.fromarray(img_tensor)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)
                yield f"path: {img_name}\n"
                await asyncio.sleep(0.5)

        # yield "[DONE]"

    return EventSourceResponse(
        image_generator(),
        media_type="text/event-stream",
    )


@router.post("/cv/generate/stream")
async def cv_generate_stream(req: CvAugmentRequest):
    """Stream-generated images from the cv model"""
    from mltools.augmentation.aug_no_label import random_aug_stream
    from mltools.utils.json2mask.third_party import img_b64_to_arr

    if req.types is None or len(req.types) == 0:
        logger.info("[cv augmentation] no types provided, using default: [rotation]")
        req.types = [
            "rotation",
        ]

    async def image_generator():
        operator = get_operator(s3_properties.augment_bucket_name)
        img = img_b64_to_arr(req.b64)

        for aug_img in random_aug_stream(
            img,
            augNumber=req.count,
            augMethods=req.types,
        ):
            # print(f"img data: {aug_img is None}")
            if aug_img is not None:
                pil_img = Image.fromarray(aug_img)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)

                out_base64 = base64.b64encode(img_bytes).decode("utf-8")
                point = cnn_measure(req.b64, out_base64)

                resp: CvAugmentResponse = CvAugmentResponse(
                    img_url=img_name, point=point
                )

                yield f"path: {resp.model_dump_json()}\n"

    return EventSourceResponse(
        image_generator(),
        media_type="text/event-stream",
    )


meta_prompt = """
你是专业的视觉提示词工程师，擅长为Stable Diffusion、MidJourney等图像生成模型设计高质量提示词。

请根据我提供的简短中文描述，扩展成一条详细、丰富、英文的Stable Diffusion图像生成Prompt，用于生成高清、高质量图片。

要求如下：
	•	必须用英文输出
	•	补充丰富的画面细节（环境、光影、色彩、氛围）
	•	指定艺术风格（如：真实风格、动漫风、油画风、科幻风、未来感、复古风、3D渲染等，若描述未提及请合理补充）
	•	添加质量关键词（如：highly detailed、ultra realistic、8K、masterpiece、cinematic lighting、high quality）
	•	整体风格自然流畅，适合直接用于Stable Diffusion

示例：

输入：一只湖边的猫
输出：A cute cat sitting by the calm lakeside during golden hour, warm sunset glow reflecting on rippling water, lush green trees in the background, ultra detailed fur, cinematic lighting, photorealistic style, 8K resolution, masterpiece, high quality

请根据以上规则，扩展以下中文描述：

{{prompt}}
"""


@router.post("/sd/prompt/optimize")
def optimize_prompt(req: PromptOptimizeRequest, db: Session = Depends(get_db)):
    """
    优化prompt
    """
    tool_model = get_tool_model(db, req.model_id)
    model: OpenAI = get_model(tool_model)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": meta_prompt.replace("{{prompt}}", req.prompt),
        },
    ]
    # response = model.chat(, model_name=tool_model.model_name)
    completion = model.chat.completions.create(
        model=tool_model.model_name,
        max_tokens=1024,
        messages=messages,
        temperature=0.7,
    )
    res = completion.choices[0].message.content
    return create_response(
        status=200, message="OK", data=PromptOptimizeResponse(prompt=res)
    )


@router.post("/measure/stream")
async def measure_stream(req: MeasureRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, req.model_id)

    async def measure_generator():
        loop = asyncio.get_event_loop()
        # f = await loop.run_in_executor(
        #     None, functools.partial(cnn_measure, req.img1, req.img2)
        # )
        # yield f"score: {f}\n"
        await asyncio.sleep(0.5)
        s = await loop.run_in_executor(
            None, functools.partial(openai_measure, req.img1, req.img2, tool_model)
        )
        yield f"{s}\n"

    return EventSourceResponse(
        measure_generator(),
        media_type="text/event-stream",
    )


@router.get("/graph/embedded/{model_id}")
def get_graph(model_id: str):
    from pathlib import Path
    if model_id == "SimpleGan":
        graph = Path(__file__).parent / "resources/simple_gan.png"
        b64 = base64.b64encode(graph.read_bytes()).decode("utf-8")
        return {"data":f"data:image/png;base64,{b64}"}
    # TODO implement other models
    return {"data": ""}



@router.post("/train")
async def train(req: GANTrainRequest, db: Session = Depends(get_db)):
    pass


SD_CLIENT: Optional[StableDiffusionUnified] = None


@router.post("/sd/initialize")
async def initialize_sd(req: SDInitializeRequest):
    global SD_CLIENT
    try:
        enable_img2img = req.enable_img2img if req.enable_img2img is not None else False
        enable_inpaint = req.enable_inpaint if req.enable_inpaint is not None else False
        sd_path = req.model_path if req.model_path is not None else "/root/models/sd3m"
        SD_CLIENT = StableDiffusionUnified(sd_path, enable_img2img, enable_inpaint)
        return {"status": "ok"}
    except Exception as e:
        logger.error(e)
        return {"status": "error"}


@router.post("/sd/generate")
async def sd_augment(req: SdAugmentRequest, db: Session = Depends(get_db)):
    global SD_CLIENT
    if SD_CLIENT is None:
        logger.error("SD_CLIENT is not initialized")
        return {"status": "error", "message": "SD_CLIENT is not initialized"}
    operator = get_operator(s3_properties.augment_bucket_name)
    if req.job_type == "img2img":
        if req.img is None:
            return {"status": "error", "message": "img is required"}

        base64_img = req.img

        if req.prompt_optimize and req.model_id is not None:
            tool_model = get_tool_model(db, req.model_id)
            model: OpenAI = get_model(tool_model)
            logger.info(f"[tool model] {tool_model.id}.{tool_model.model_name} ")
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
                            "image_url": {"url": f"{base64_img}"},
                        },
                    ],
                },
            ]
            try:
                completion = model.chat.completions.create(
                    model=tool_model.model_name,
                    max_tokens=1024,
                    messages=messages,
                    temperature=0.7,
                )
                response = (
                    completion.choices[0]
                    .message.content.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                logger.info(f"merge user`s prompt with llm generated prompt")
                prompt = json.loads(response)
                req.prompt = prompt["prompt"] + "," + req.prompt
                req.negative_prompt = prompt["negative_prompt"]
            except Exception:
                logger.error(
                    "prompt optimize failed because of llm or json parse error. Details:\n"
                )
                traceback.print_exc()

        async def __img_to_img():
            if req.negative_prompt is None:
                req.negative_prompt = __RESERVED_NEGATIVE_PROMPT__

            logger.info(f"prompt: {req.prompt}")
            logger.info(f"negative_prompt: {req.negative_prompt}")

            ref_img = base64_to_pil_image(base64_img)
            for i in range(req.count):
                res = SD_CLIENT.img2img(
                    image=ref_img,
                    prompt=req.prompt,
                    negative_prompt=req.negative_prompt,
                    steps=req.steps,
                    strength=req.strength,
                    guidance_scale=req.guidance_scale,
                    seed=random.randint(1, req.seed + i * 10),
                    num_images_per_prompt=1,
                )
                if res is None or len(res) == 0:
                    continue
                pil_img = res[0]
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)
                # yield f"path: {img_name}\n"
                ref_img_base64 = pil_to_base64(ref_img)
                out_base64 = base64.b64encode(img_bytes).decode("utf-8")
                point = cnn_measure(ref_img_base64, out_base64)

                resp: CvAugmentResponse = CvAugmentResponse(
                    img_url=img_name, point=point
                )

                yield f"path: {resp.model_dump_json()}\n"

                await asyncio.sleep(0.5)

        return EventSourceResponse(__img_to_img(), media_type="text/event-stream")

    if req.job_type == "inpaint":
        if req.img is None or req.mask is None:
            # TODO unimplemented yet
            return {"status": "error", "message": "img and mask are required"}
        return {"status": "error", "message": "inpaint is not supported yet"}

    if req.job_type == "txt2img":
        if req.lora_name is not None:
            if req.lora_name not in reserved_lora_modules:
                return {"status": "error", "message": "lora_name is not supported"}
            if req.lora_name in reserved_lora_modules:
                SD_CLIENT.enable_lora(req.lora_name)
                req.prompt = (
                    req.prompt
                    if len(req.prompt) == 0
                    else reserved_lora_modules[req.lora_name]["prompt"]
                )

        async def __txt_to_img():
            for i in range(req.count):
                res = SD_CLIENT.text2img(
                    prompt=req.prompt,
                    negative_prompt=req.negative_prompt,
                    width=req.width,
                    height=req.height,
                    steps=req.steps,
                    guidance_scale=req.guidance_scale,
                    seed=random.randint(1, req.seed + i * 10),
                    num_images_per_prompt=1,
                )
                if res is None or len(res) == 0:
                    continue
                pil_img = res[0]
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)
                # yield f"path: {img_name}\n"

                resp: CvAugmentResponse = CvAugmentResponse(img_url=img_name, point=0)

                yield f"path: {resp.model_dump_json()}\n"
                await asyncio.sleep(0.5)
            SD_CLIENT.disable_lora()

        return EventSourceResponse(__txt_to_img(), media_type="text/event-stream")

    return {"status": "error", "message": "Invalid request"}


@router.get("/on")
async def is_client_on():
    global SD_CLIENT
    return {"status": "ok", "data": SD_CLIENT is not None}


@router.post("/sd/deep-optimize")
async def sd_deep_optimize(req: SdDeepOptimizeRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, req.model_id)
    model: OpenAI = get_model(tool_model)
    operator = get_operator(s3_properties.augment_bucket_name)
    first_image_path = req.img
    first_image_bytes = operator.read(first_image_path)
    first_image_base64 = base64.b64encode(first_image_bytes).decode("utf-8")
    global SD_CLIENT

    def __evaluate_image_with_mllm(base64_image: str, user_goal: str) -> dict:
        query = f"""
            你是一位图像评估专家，请根据以下用户目标对图像进行评估：

            目标：「{user_goal}」

            请：
            1. 判断图像是否符合该目标（如真实性、对比度等）
            2. 如果不符合，指出不足，并优化提示词用于 Stable Diffusion 生成
            3. 回答强制使用英语

            请严格输出以下 JSON 格式（注意字段名）：
            {{
                "score": 0~1之间的浮点数,
                "advice": "你对图像优化的简要建议",
                "prompt": "新的正向提示词，用于指导 SD 生成",
                "negative_prompt": "新的负向提示词，用于避免生成错误"
            }}
            如果图像已经很好，仍然需要输出 score 和建议。
        """

        if not base64_image.startswith("data:image/png;base64,"):
            base64_image = "data:image/png;base64," + base64_image

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"{base64_image}"},
                    },
                ],
            },
        ]

        completion = model.chat.completions.create(
            model=tool_model.model_name,
            max_tokens=1024,
            messages=messages,
            temperature=0.7,
        )
        response = (
            completion.choices[0]
            .message.content.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        logger.info(f"🧠 MLLM 响应：{response}")

        try:
            result = json.loads(response)

            if result.get("score", 0.0) >= 0.95:
                return {"status": "ok", **result}
            else:
                return {"status": "need_improve", **result}
        except Exception:
            logger.error(
                "prompt optimize failed because of llm or json parse error. Details:\n"
            )
            traceback.print_exc()
            return {
                "status": "error",
                "message": "Invalid response from Qwen-VL",
            }

    async def __loop_optimize(base64_image: str, user_goal: str, times: int):
        for i in range(times):
            res = __evaluate_image_with_mllm(base64_image, user_goal)
            if res["status"] == "ok":
                # save to s3
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = base64.b64decode(base64_image)
                operator.write(img_name, img_bytes)
                sdop: SdDeepOptimizeResponse = SdDeepOptimizeResponse(
                    img=img_name, tip=f"[Round {i+1}] done"
                )
                yield f"path: {sdop.model_dump_json()}\n"
                await asyncio.sleep(0.5)
                break
            elif res["status"] == "need_improve":
                prompt = res["prompt"]
                negative_prompt = res["negative_prompt"]
                image = base64_to_pil_image(base64_image)

                imgs = SD_CLIENT.img2img(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=image,
                    strength=0.3,
                )
                if imgs is None or len(imgs) == 0:
                    continue
                new_img = imgs[0]
                base64_image = pil_to_base64(new_img)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = base64.b64decode(base64_image)
                operator.write(img_name, img_bytes)
                sdop: SdDeepOptimizeResponse = SdDeepOptimizeResponse(
                    img=img_name, tip=f"[Round {i+1}] {res['advice']}"
                )
                yield f"path: {sdop.model_dump_json()}\n"
                await asyncio.sleep(0.5)
            else:
                yield f"loop error \n"

    return EventSourceResponse(
        __loop_optimize(first_image_base64, req.prompt, req.loop_times),
        media_type="text/event-stream",
    )
