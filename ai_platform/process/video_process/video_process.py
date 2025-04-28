import json
import os
from glob import glob
from typing import List, Union

import cv2
import ffmpeg
import supervision as sv
from supervision.annotators.core import BaseAnnotator
from ultralytics import YOLO

from process import BaseProcess, DirectoryModel
from process.video_process import create_folder
from process.video_process.video_process_result import KeyFrameInfo, VideoKeyFrames
from yolo.response import PredictResult

basic_path = "./runs/"
frames_dir = "keyframes"
annotated_dir = "annotated_keyframes"


def get_annotated_files(session_id: str) -> List[str]:
    return sorted(glob(os.path.join(basic_path, session_id, annotated_dir), "*.png"))


class VideoProcess(BaseProcess):

    def __init__(self, video_path: str, session_id: str):
        super().__init__()
        self.video_path = video_path
        self.session_id = session_id
        self.dir = self.create_temp_dir()
        self.timestamps = {}
        self.duration = 0.0
        self.video_frame_width = 0
        self.video_frame_height = 0

    def create_temp_dir(self) -> DirectoryModel:
        global basic_path, frames_dir, annotated_dir

        __frames_dir = create_folder(basic_path, self.session_id, frames_dir)
        __annotated_dir = create_folder(basic_path, self.session_id, annotated_dir)
        return DirectoryModel(
            files_dir=__frames_dir,
            results_dir=__annotated_dir,
        )

    def extract_keyframes(self, interval_sec=2.0):
        probe = ffmpeg.probe(self.video_path, select_streams="v")
        self.duration = float(probe["streams"][0]["duration"])
        cap = cv2.VideoCapture(self.video_path)
        current_time = 0.0
        # timestamps = {}
        frame_idx = 0

        while current_time < self.duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
            ret, frame = cap.read()
            if not ret:
                break

            if self.video_frame_height == 0 and self.video_frame_width == 0:
                self.video_frame_width = frame.shape[1]
                self.video_frame_height = frame.shape[0]

            save_name = f"frame_{frame_idx:04d}.png"
            save_path = os.path.join(self.dir.files_dir, save_name)
            cv2.imwrite(save_path, frame)
            self.timestamps[save_name] = current_time

            frame_idx += 1
            current_time += interval_sec  # 每隔 interval 秒取一帧

        cap.release()

    def detect_and_annotate(
        self, annotator: BaseAnnotator, model: Union[YOLO]
    ) -> VideoKeyFrames:
        frame_paths = sorted(glob(os.path.join(self.dir.files_dir, "*.png")))
        l: List[KeyFrameInfo] = []
        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)

            annotated_frame = annotator.annotate(
                scene=frame.copy(), detections=detections
            )
            dls: List[PredictResult] = []

            for r in json.loads(result.to_json()):
                """
                {
                    "name": "person",
                    "class": 0,
                    "confidence": 0.84967,
                    "box": {
                    "x1": 28.39458,
                    "y1": 456.74014,
                    "x2": 143.09355,
                    "y2": 696.08197
                    }
                }
                """

                dl = PredictResult.from_dict(r)
                dls.append(dl)

            # 保存
            frame_name = os.path.basename(frame_path)
            save_path = os.path.join(self.dir.results_dir, frame_name)
            cv2.imwrite(save_path, annotated_frame)
            l.append(
                KeyFrameInfo(
                    detections=dls,
                    filename=frame_name,
                    timestamp=self.timestamps[frame_name],
                )
            )
        return VideoKeyFrames(
            frame_width=self.video_frame_width,
            frame_height=self.video_frame_height,
            duration=self.duration,
            keyframes=l,
            video_path=self.video_path + "(tempfile)",
        )
