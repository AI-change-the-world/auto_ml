# requirements: fastapi, uvicorn, opencv-python, numpy, supervision, ultralytics

import os
import base64
import io
import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

video_path = "your_video.mp4"  # 你的原视频路径
model = YOLO('yolov8n.pt')      # 用小一点的模型加速
trace_annotator = sv.TraceAnnotator()
tracker = sv.ByteTrack()

# --- Helper function: 比较两次检测结果是否变化大 ---
def detections_changed(prev_detections: sv.Detections, curr_detections: sv.Detections, iou_threshold=0.5):
    if prev_detections is None:
        return True
    if len(prev_detections) != len(curr_detections):
        return True
    # 简单比较，每个框的iou
    for prev_bbox, curr_bbox in zip(prev_detections.xyxy, curr_detections.xyxy):
        iou = compute_iou(prev_bbox, curr_bbox)
        if iou < iou_threshold:
            return True
    return False

# --- Helper function: 计算两个bbox的IoU ---
def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou

@app.get("/stream")
async def stream_keyframes():
    def event_generator():
        frames_generator = sv.get_video_frames_generator(source_path=video_path)
        prev_detections = None
        frame_idx = 0

        for frame in frames_generator:
            frame_idx += 1
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)

            if detections_changed(prev_detections, detections):
                # 关键帧，处理并推送
                annotated_frame = trace_annotator.annotate(scene=frame.copy(), detections=detections)
                
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                yield f"data:{frame_base64}\n\n"

                prev_detections = detections

    return StreamingResponse(event_generator(), media_type='text/event-stream')


if __name__ == "__main__":
    import uvicorn

    debug = os.environ.get("IS_DEBUG", None)
    uvicorn.run(
        "video_test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=debug == "true" or debug is None,
    )