"""
docker run --rm -it \
-e MTX_RTSPTRANSPORTS=tcp \
-e MTX_WEBRTCADDITIONALHOSTS=192.168.x.x \
-p 8554:8554 \
-p 1935:1935 \
-p 8888:8888 \
-p 8889:8889 \
-p 8890:8890/udp \
-p 8189:8189/udp \
bluenviron/mediamtx

ffmpeg -re -stream_loop -1 -i test.mp4  -c copy -f rtsp rtsp://localhost:8554/mystream
"""


import os
from ultralytics import YOLO
import supervision as sv
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import cv2

model = YOLO("yolov8n.pt")
app = FastAPI()

# 打开 RTSP 视频流（替换为你的实际地址）
video = cv2.VideoCapture("rtsp://localhost:8554/mystream")

box_annotator = sv.BoxAnnotator()

def gen_frames():
    while True:
        success, frame = video.read()
        if not success:
            break

        # 1. 将 numpy 图像直接送入模型（不是 buffer）
        results = model(frame)[0]

        # 2. 生成检测框对象
        detections = sv.Detections.from_ultralytics(results)

        # 3. 在原始图像上绘制检测框
        annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)

        # 4. 编码为 JPEG
        success, encoded_image = cv2.imencode('.jpg', annotated_frame)
        if not success:
            continue

        # 5. 输出 MJPEG 帧
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n')

@app.get("/video")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=15234)