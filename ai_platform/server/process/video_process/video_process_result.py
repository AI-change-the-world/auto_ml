from typing import List

from pydantic import BaseModel

from yolo.response import PredictResult


class KeyFrameInfo(BaseModel):
    filename: str
    timestamp: float
    detections: List[PredictResult] = []  # 初始可以为空，后面可以补充检测结果


class VideoKeyFrames(BaseModel):
    video_path: str
    duration: float
    keyframes: List[KeyFrameInfo]
    frame_width: int
    frame_height: int

    def save_json(self, path: str):
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def load_json(cls, path: str):
        with open(path, "r") as f:
            return cls.model_validate_json(f.read())
