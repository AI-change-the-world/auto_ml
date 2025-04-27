import json
import os
from glob import glob

import cv2
import ffmpeg
import supervision as sv
from ultralytics import YOLO

# 配置
video_path = "test.mp4"
frames_dir = "keyframes"
annotated_dir = "annotated_keyframes"
timestamp_json_path = "keyframes_timestamps.json"
os.makedirs(frames_dir, exist_ok=True)
os.makedirs(annotated_dir, exist_ok=True)

model = YOLO("yolo11x.pt")
box_annotator = sv.BoxAnnotator()


# Step 1. 抽取无损关键帧
def extract_keyframes(video_path, frames_dir, timestamp_json_path, interval_sec=2.0):
    # 用 ffprobe 拉所有帧信息
    probe = ffmpeg.probe(video_path, select_streams="v")
    duration = float(probe["streams"][0]["duration"])

    cap = cv2.VideoCapture(video_path)

    current_time = 0.0
    timestamps = {}
    frame_idx = 0

    while current_time < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
        ret, frame = cap.read()
        if not ret:
            break

        save_name = f"frame_{frame_idx:04d}.png"
        save_path = os.path.join(frames_dir, save_name)
        cv2.imwrite(save_path, frame)
        timestamps[save_name] = current_time

        frame_idx += 1
        current_time += interval_sec  # 每隔 interval 秒取一帧

    cap.release()

    with open(timestamp_json_path, "w") as f:
        json.dump(timestamps, f, indent=4)


# Step 2. 关键帧检测 + 标注保存
def detect_and_annotate(frames_dir, annotated_dir):
    frame_paths = sorted(glob(os.path.join(frames_dir, "*.png")))
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        result = model(frame)[0]
        print(result.to_json())
        detections = sv.Detections.from_ultralytics(result)

        annotated_frame = box_annotator.annotate(
            scene=frame.copy(), detections=detections
        )

        # 保存
        frame_name = os.path.basename(frame_path)
        save_path = os.path.join(annotated_dir, frame_name)
        cv2.imwrite(save_path, annotated_frame)


# === RUN ===
extract_keyframes(video_path, frames_dir, timestamp_json_path)

detect_and_annotate(frames_dir, annotated_dir)

print(f"完成！关键帧保存在 {frames_dir}，标注后关键帧保存在 {annotated_dir}")
