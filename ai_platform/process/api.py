import os
import tempfile

import supervision as sv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from ultralytics import YOLO

from base.file_delegate import FileDelegate, GetFileRequest

router = APIRouter(
    prefix="/process",
    tags=["process"],
)

model = YOLO("yolo11x.pt")
box_annotator = sv.BoxAnnotator()


class Request(BaseModel):
    file: str
    session_id: str


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

            vp.extract_keyframes()
            yield "关键帧提取完成"

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
