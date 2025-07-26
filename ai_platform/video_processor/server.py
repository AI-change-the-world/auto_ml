import asyncio
import base64
import json
import math
import numpy as np
from pydantic import BaseModel
import torch
import torchvision.transforms as T
from decord import VideoReader, cpu
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
from fastapi import FastAPI, UploadFile, Form
from sse_starlette import EventSourceResponse
from tempfile import NamedTemporaryFile
from typing import List
import shutil
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的前端地址列表
    allow_credentials=True,  # 是否允许携带 cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)



# model setting
model_path = '/root/models/iv'

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModel.from_pretrained(model_path, trust_remote_code=True).half().cuda().to(torch.bfloat16)

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([T.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img), T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC), T.ToTensor(), T.Normalize(mean=MEAN, std=STD)])
    return transform


def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float("inf")
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def dynamic_preprocess(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set((i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = ((i % (target_width // image_size)) * image_size, (i // (target_width // image_size)) * image_size, ((i % (target_width // image_size)) + 1) * image_size, ((i // (target_width // image_size)) + 1) * image_size)
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images


def load_image(image, input_size=448, max_num=6):
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values


def get_index(bound, fps, max_frame, first_idx=0, num_segments=32):
    if bound:
        start, end = bound[0], bound[1]
    else:
        start, end = -100000, 100000
    start_idx = max(first_idx, round(start * fps))
    end_idx = min(round(end * fps), max_frame)
    seg_size = float(end_idx - start_idx) / num_segments
    frame_indices = np.array([int(start_idx + (seg_size / 2) + np.round(seg_size * idx)) for idx in range(num_segments)])
    return frame_indices

def get_num_frames_by_duration(duration):
        local_num_frames = 4        
        num_segments = int(duration // local_num_frames)
        if num_segments == 0:
            num_frames = local_num_frames
        else:
            num_frames = local_num_frames * num_segments
        
        num_frames = min(512, num_frames)
        num_frames = max(128, num_frames)

        return num_frames

def load_video(video_path, bound=None, input_size=448, max_num=1, num_segments=32, get_frame_by_duration = False):
    vr = VideoReader(video_path, ctx=cpu(0), num_threads=1)
    max_frame = len(vr) - 1
    fps = float(vr.get_avg_fps())

    pixel_values_list, num_patches_list = [], []
    transform = build_transform(input_size=input_size)
    if get_frame_by_duration:
        duration = max_frame / fps
        num_segments = get_num_frames_by_duration(duration)
    frame_indices = get_index(bound, fps, max_frame, first_idx=0, num_segments=num_segments)
    for frame_index in frame_indices:
        img = Image.fromarray(vr[frame_index].asnumpy()).convert("RGB")
        img = dynamic_preprocess(img, image_size=input_size, use_thumbnail=True, max_num=max_num)
        pixel_values = [transform(tile) for tile in img]
        pixel_values = torch.stack(pixel_values)
        num_patches_list.append(pixel_values.shape[0])
        pixel_values_list.append(pixel_values)
    pixel_values = torch.cat(pixel_values_list)
    return pixel_values, num_patches_list

# evaluation setting
max_num_frames = 512
generation_config = dict(
    do_sample=True,
    temperature=0.1,
    max_new_tokens=1024,
    top_p=0.1,
    num_beams=1
)
num_segments=128

frame_interval = 24

SEGMENT_SECONDS = 10  # 每段时长，秒


class VideoAnalyzerRequest(BaseModel):
    video_path: str
    prompt: str

@app.post("/video/upload")
async def upload_video_file(video: UploadFile):
    try:
        with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            shutil.copyfileobj(video.file, tmp)
            tmp_path = tmp.name
        return {"video_path": tmp_path}
    except Exception as e:
        raise {"video_path": None}
    

def image_to_base64_webp(img_array, width=300, quality=80):
    # 1. 转换为 PIL Image
    img = Image.fromarray(img_array).convert("RGB")

    # 2. 缩放
    w_percent = (width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((width, h_size), Image.LANCZOS)

    # 3. 转为 WebP 并压缩
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality)
    buf.seek(0)

    # 4. Base64 编码
    b64_img = base64.b64encode(buf.read()).decode("utf-8")
    return b64_img

@app.post("/video/search-frame")
async def search_relevant_frame(req: VideoAnalyzerRequest):
    # 保存视频临时文件
    tmp_path = req.video_path

    vr = VideoReader(tmp_path, ctx=cpu(0), num_threads=1)
    fps = vr.get_avg_fps()
    total_frames = len(vr)
    duration_sec = total_frames / fps

    # 计算切分段数
    num_segments = math.ceil(duration_sec / SEGMENT_SECONDS)

    async def handle_request():
        for seg_idx in range(num_segments):
            start_time = seg_idx * SEGMENT_SECONDS
            end_time = min((seg_idx + 1) * SEGMENT_SECONDS, duration_sec)

            # 这里load_video 支持按时间区间切片，加个bound参数 start/end秒
            pixel_values, num_patches_list = load_video(
                tmp_path,
                bound=(start_time, end_time),
                num_segments=32,   # 或根据时长动态调整
                max_num=1,
                get_frame_by_duration=False,
            )
            pixel_values = pixel_values.to(torch.bfloat16).to(model.device)
            video_prefix = "".join([f"Frame{i+1}: <image>\n" for i in range(len(num_patches_list))])

            with torch.no_grad():
                question1 = "详细描述视频中每一个工人的工作状态，包括是否穿戴安全帽，是否穿着反光背心，是否在抽烟。"
                question = video_prefix + question1
                output1, chat_history = model.chat(tokenizer, pixel_values, question, generation_config, num_patches_list=num_patches_list, history=None, return_history=True)
                print(f"output1 {output1}")
                
                question2 = video_prefix + req.prompt+", 答案回答是或者否"
                output2, chat_history = model.chat(tokenizer, pixel_values, question2, generation_config, num_patches_list=num_patches_list, history=chat_history, return_history=True)

                print("output:", output2)

            # 简单判断输出，返回对应帧，或者所有帧也可以，示例只返回第一帧
            if "是" in output2 and "否" not in output2:
                for frame_index in range(0,len(num_patches_list), frame_interval):
                    frame = vr[frame_index].asnumpy()
                    img = image_to_base64_webp(frame)

                    result = {
                        "segment_index": seg_idx,
                        "frame_index": frame_index,
                        "frame": img,
                        "text": output1,
                    }
                    yield json.dumps(result, ensure_ascii=False)
                    await asyncio.sleep(0.5)

        yield json.dumps({"frame": None})

    return EventSourceResponse(handle_request(), media_type="text/event-stream")


# @app.post("/video/search-frame")
# async def search_relevant_frame(video: UploadFile, prompt: str = Form(...)):

#     # 保存视频到临时文件
#     with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
#         shutil.copyfileobj(video.file, tmp)
#         tmp_path = tmp.name

#     # 推理部分开始
#     with torch.no_grad():
#         pixel_values, num_patches_list = load_video(tmp_path, num_segments=128, max_num=1, get_frame_by_duration=False)
#         pixel_values = pixel_values.to(torch.bfloat16).to(model.device)
        
#         video_prefix = "".join([f"Frame{i+1}: <image>\n" for i in range(len(num_patches_list))])
#         question = video_prefix + prompt
#         # print("question:", question)
#         output, chat_history = model.chat(
#             tokenizer, pixel_values, question, generation_config,
#             num_patches_list=num_patches_list, history=None, return_history=True
#         )
#         print("output:", output)

#     async def handle_request():
#         # 简单启发式匹配：找出哪个 FrameX 出现在回答中最早
#         if "是" in output and "否" not in output:
#             vr = VideoReader(tmp_path, ctx=cpu(0), num_threads=1)
#             # 从num_patches_list中按frame_interval提取frame
#             for frame_index in range(0,len(num_patches_list), frame_interval):
#                 frame = vr[frame_index].asnumpy()
#                 img = Image.fromarray(frame).convert("RGB")
#                 buf = io.BytesIO()
#                 img.save(buf, format="JPEG")
#                 buf.seek(0)
#                 bytes = buf.getvalue()
#                 result = {"frame": base64.b64encode(bytes).decode("utf-8")}
#                 yield json.dumps(result)
#                 await asyncio.sleep(0.1)
#         yield json.dumps({"frame": None})
#     return EventSourceResponse(handle_request(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    import os

    debug = os.environ.get("IS_DEBUG", None)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=debug == "true" or debug is None,
    )