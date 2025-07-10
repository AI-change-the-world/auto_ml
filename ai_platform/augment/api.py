import asyncio
import functools
import io
import time
import uuid
from http import HTTPStatus
from typing import Optional

import torch
from dashscope import ImageSynthesis
from fastapi import APIRouter, Depends
from openai import OpenAI
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sse_starlette import EventSourceResponse

from augment.simple_gan.model import Generator as Model
from base import create_response
from base.file_delegate import get_operator, s3_properties
from base.nacos_config import get_db
from db.tool_model.tool_model_crud import get_tool_model
from label.client import get_model

model_path = "generator.pth"

model = Model(z_dim=2048, img_channels=3).to("cpu")
model.load_state_dict(torch.load(model_path))


class GANRequest(BaseModel):
    count: int


class CvAugmentRequest(BaseModel):
    count: int
    b64: str


class SdAugmentRequest(BaseModel):
    count: int
    prompt: str


class PromptOptimizeRequest(BaseModel):
    model_id: int
    prompt: str
    ref: Optional[str] = None


class PromptOptimizeResponse(BaseModel):
    prompt: str


class SdAugmentResponse(BaseModel):
    img_url: str


class MeasureRequest(BaseModel):
    img1: str
    img2: str
    model_id: int


router = APIRouter(
    prefix="/augment",
    tags=["Augment"],
)


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
                time.sleep(0.5)

        # yield "[DONE]"

    return EventSourceResponse(
        image_generator(),
        media_type="text/event-stream",
    )


# TODO merge to augment, just for demo
@router.post("/cv/generate/stream")
async def cv_generate_stream(req: CvAugmentRequest):
    """Stream-generated images from the cv model"""
    from mltools.augmentation.aug_no_label import random_aug_stream
    from mltools.utils.json2mask.third_party import img_b64_to_arr

    async def image_generator():
        operator = get_operator(s3_properties.augment_bucket_name)
        img = img_b64_to_arr(req.b64)

        for aug_img in random_aug_stream(
            img,
            augNumber=req.count,
            augMethods=["noise", "rotation", "trans", "flip", "zoom"],
        ):
            print(f"img data: {aug_img is None}")
            if aug_img is not None:
                pil_img = Image.fromarray(aug_img)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4()) + ".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)
                yield f"path: {img_name}\n"

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


async def __block_call(model: str, prompt: str, ak: str, ref: Optional[str] = None):
    rsp = ImageSynthesis.call(model=model, prompt=prompt, api_key=ak)
    if rsp.status_code == HTTPStatus.OK:
        # save file to current directory
        for result in rsp.output.results:
            yield result.url
    else:
        yield None


@router.post("/sd/generate")
async def generate_image(req: SdAugmentRequest, db: Session = Depends(get_db)):
    tool_model = get_tool_model(db, 1)
    return EventSourceResponse(
        __block_call(model="flux-schnell", prompt=req.prompt, ak=tool_model.api_key),
        media_type="text/event-stream",
    )


@router.post("/measure/stream")
async def measure_stream(req: MeasureRequest, db: Session = Depends(get_db)):
    from augment.measure import cnn_measure, openai_measure

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
