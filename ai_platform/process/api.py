import os
import tempfile

import supervision as sv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from ultralytics import YOLO

from base.file_delegate import FileDelegate

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
        delegate = FileDelegate(file_type=1, storage_type=1, url="", file_name=file)

        try:

            b: bytes = delegate.get_file()
            temp = tempfile.NamedTemporaryFile(delete=True, dir="./runs/")

            temp.write(b)
            temp.flush()
            temp_path = temp.name

            vp = VideoProcess(session_id=session_id, video_path=temp_path)
            yield f"开始处理文件 {file}"

            vp.extract_keyframes()
            yield "关键帧提取 完成"

            rs: BaseModel = vp.detect_and_annotate(annotator=box_annotator, model=model)
            yield "检测完成"

            yield f"{rs.model_dump_json()}"

            # 结束标记
            yield "[DONE]"
        except Exception as e:
            yield f"[ERROR] {e}"
        finally:
            temp.close()  # 关闭文件（重要！）
            # 用完后删除文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Temporary file {temp_path} deleted.")

    return EventSourceResponse(
        event_generator(session_id=req.session_id, file=req.file),
        media_type="text/event-stream",
    )
