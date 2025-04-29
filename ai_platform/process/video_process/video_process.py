import io
import json
import os
import shutil
from glob import glob
from typing import List, Optional, Union

import cv2
import ffmpeg
import supervision as sv
from PIL import Image
from supervision.annotators.core import BaseAnnotator
from ultralytics import YOLO

from base.file_delegate import FileDelegate
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
        self,
        annotator: BaseAnnotator,
        model: Union[YOLO],
        delegate: Optional[FileDelegate] = None,
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
            if delegate is not None:
                # 转成 Image
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)

                # 写入到内存 buffer
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")  # 或 "JPEG" 之类
                buffer.seek(0)  # 重要，回到文件开头

                delegate.put_bytes_to_s3(
                    prefix=self.session_id,
                    file_content=buffer.read(),
                    file_name=frame_name,
                )
                l.append(
                    KeyFrameInfo(
                        detections=dls,
                        filename=self.session_id + "/" + frame_name,
                        timestamp=self.timestamps[frame_name],
                    )
                )
            else:
                # this logic is deprecated, will be removed
                save_path = os.path.join(self.dir.results_dir, frame_name)
                cv2.imwrite(save_path, annotated_frame)
                l.append(
                    KeyFrameInfo(
                        detections=dls,
                        filename=frame_name,
                        timestamp=self.timestamps[frame_name],
                    )
                )
        # delete all files
        parent_dir = os.path.dirname(self.dir.files_dir)
        shutil.rmtree(parent_dir)

        return VideoKeyFrames(
            frame_width=self.video_frame_width,
            frame_height=self.video_frame_height,
            duration=self.duration,
            keyframes=l,
            video_path=self.video_path + "(tempfile)",
        )
