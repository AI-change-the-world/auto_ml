import os
import tempfile
from typing import List, Optional

import supervision as sv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from requests import Session
from sse_starlette.sse import EventSourceResponse
from ultralytics import YOLO

from base.deprecated import deprecated
from base.file_delegate import FileDelegate, GetFileRequest
from base.nacos_config import get_db
from db.tool_model.tool_model_crud import get_tool_model

router = APIRouter(
    prefix="/process",
    tags=["process"],
)

model = YOLO("yolo11x.pt")
box_annotator = sv.BoxAnnotator()


class Request(BaseModel):
    file: str
    session_id: str


class ImageAnalyzeRequest(BaseModel):
    model_id: int
    frame_path: str
    x1: float
    y1: float
    x2: float
    y2: float
    prompt: Optional[str]


class ImageDescribeRequest(BaseModel):
    model_id: int
    frame_path: str
    prompt: Optional[str]

class ImageListDescribeRequest(BaseModel):
    model_id: int
    frames: List[str]
    prompt: Optional[str]


interval_sec = 10


@deprecated(reason="请使用 /describe 接口")
@router.post("/analyze")
async def predict(req: ImageAnalyzeRequest, db: Session = Depends(get_db)):
    from process.video_process.key_frame_analysis import key_frame_analysis

    tool_model = get_tool_model(db, req.model_id)

    return EventSourceResponse(
        key_frame_analysis(
            frame_path=req.frame_path,
            tool_model=tool_model,
            x1=req.x1,
            y1=req.y1,
            x2=req.x2,
            y2=req.y2,
            prompt=req.prompt,
        ),
        media_type="text/event-stream",
    )


@router.post("/describe")
async def predict(req: ImageDescribeRequest, db: Session = Depends(get_db)):
    from process.video_process.key_frame_analysis import describe_frame

    tool_model = get_tool_model(db, req.model_id)

    return EventSourceResponse(
        describe_frame(
            frame_path=req.frame_path,
            tool_model=tool_model,
            prompt=req.prompt,
        ),
        media_type="text/event-stream",
    )


@router.post("/describe/list")
async def predict(req: ImageListDescribeRequest, db: Session = Depends(get_db)):
    from process.video_process.key_frame_analysis import describe_frames

    tool_model = get_tool_model(db, req.model_id)

    return EventSourceResponse(
        describe_frames(
            frame_paths=req.frames,
            tool_model=tool_model,
            prompt=req.prompt,
        ),
        media_type="text/event-stream",
    )


@router.post("/video")
async def predict(req: Request):
    from process.video_process.video_process import VideoProcess

    async def event_generator(session_id: str, file: str):
        delegate = FileDelegate()
        temp_path = None
        temp_file = None
        try:
            req = GetFileRequest(
                file_name=file,
                file_type=1,
                storage_type=1,
                url="",
            )
            b: bytes = delegate.get_file(req)

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, dir="./runs/")
            temp_file.write(b)
            temp_file.flush()
            temp_path = temp_file.name
            temp_file.close()

            vp = VideoProcess(session_id=session_id, video_path=temp_path)
            yield f"开始处理文件 {file}"

            vp.extract_keyframes(interval_sec=interval_sec)
            yield "关键帧提取完成"

            yield "正在识别关键帧，请稍后..."

            rs: BaseModel = vp.detect_and_annotate(
                annotator=box_annotator, model=model, delegate=delegate
            )
            yield "检测完成"

            yield rs.model_dump_json()
        except Exception as e:
            # 如果捕获到了异常，发一个 [ERROR]
            yield f"[ERROR] {str(e)}"
        finally:
            # 最后一定要清理
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    return EventSourceResponse(
        event_generator(session_id=req.session_id, file=req.file),
        media_type="text/event-stream",
    )
