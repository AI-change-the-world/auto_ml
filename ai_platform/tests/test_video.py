import sys

from ultralytics import YOLO

sys.path.append(".")
import supervision as sv
from pydantic import BaseModel

from process.video_process.video_process import VideoProcess

model = YOLO("yolo11x.pt")
model2 = YOLO("/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/best.pt")
box_annotator = sv.BoxAnnotator()


vp = VideoProcess(
    session_id="1-2-3-4",
    video_path="/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/test.mp4",
)

vp.extract_keyframes()

rs: BaseModel = vp.detect_and_annotate(
    annotator=box_annotator, model_list=[model, model2]
)

print(rs.model_dump_json())
