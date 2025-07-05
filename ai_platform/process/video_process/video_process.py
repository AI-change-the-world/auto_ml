import io
import json
import os
import shutil
from glob import glob
from typing import Any, List, Optional, Union, overload

import cv2
import ffmpeg
import numpy as np
import supervision as sv
from PIL import Image
from supervision.annotators.core import BaseAnnotator
from ultralytics import YOLO

from base.file_delegate import FileDelegate
from process import BaseProcess, DirectoryModel
from process.video_process import create_folder
from process.video_process.video_process_result import KeyFrameInfo, VideoKeyFrames
from yolo.response import PredictResult, predict_result_from_detections

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

    @overload
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

    def detect_and_annotate(
        self,
        annotator: BaseAnnotator,
        model_list: List[YOLO],
        delegate: Optional[FileDelegate] = None,
        iou_threshold: float = 0.5,
    ) -> VideoKeyFrames:
        assert model_list, "At least one model must be provided."

        frame_paths = sorted(glob(os.path.join(self.dir.files_dir, "*.png")))
        keyframes: List[KeyFrameInfo] = []

        def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
            """
            box1, box2: [x1, y1, x2, y2]
            """
            xA = max(box1[0], box2[0])
            yA = max(box1[1], box2[1])
            xB = min(box1[2], box2[2])
            yB = min(box1[3], box2[3])

            interArea = max(0, xB - xA) * max(0, yB - yA)

            box1Area = (box1[2] - box1[0]) * (box1[3] - box1[1])
            box2Area = (box2[2] - box2[0]) * (box2[3] - box2[1])

            unionArea = box1Area + box2Area - interArea

            if unionArea == 0:
                return 0.0

            return interArea / unionArea

        def merge_detections(
            detections_list: List[sv.Detections],
        ) -> sv.Detections:
            """
            合并多个模型输出的 Detections（按类名和 IOU）。
            """
            if not detections_list:
                return sv.Detections.empty()

            # 把所有 detections 合并成一个大的
            all_boxes = []
            all_scores = []
            all_class_names = []

            for detections in detections_list:
                # print(detections.class_id)
                all_boxes.extend(list(detections.xyxy))
                all_scores.extend(list(detections.confidence))
                all_class_names.extend(list(detections.data["class_name"]))

            all_class_names = [str(i).lower() for i in all_class_names]

            # print(all_boxes)

            merged_indices = []
            used = set()

            for i in range(len(all_boxes)):
                if i in used:
                    continue

                box_i = all_boxes[i]
                cls_i = all_class_names[i]

                is_insert = False
                for j in range(i + 1, len(all_boxes)):
                    if j in used or all_class_names[j] != cls_i:
                        continue
                    box_j = all_boxes[j]
                    iou_val = compute_iou(box1=box_i, box2=box_j)
                    if iou_val > iou_threshold:
                        # 同一个对象，可以只保留一个
                        used.add(j)
                        is_insert = True
                        merged_indices.append((box_i, all_scores[i], cls_i))
                if not is_insert:
                    merged_indices.append((box_i, all_scores[i], cls_i))
                is_insert = False

            merged_boxes = np.array([b for b, _, _ in merged_indices])
            merged_scores = np.array([s for _, s, _ in merged_indices])
            merged_class_names = np.array([c for _, _, c in merged_indices])

            # print(merged_class_ids)

            def encode_labels(arr):
                label_map = {}
                result = []
                current_index = 0
                for label in arr:
                    if label not in label_map:
                        label_map[label] = current_index
                        current_index += 1
                    result.append(label_map[label])
                return result, label_map

            # print(merged_boxes)

            merged_class_ids, _ = encode_labels(merged_class_names)

            return sv.Detections(
                xyxy=merged_boxes,
                confidence=merged_scores,
                class_id=np.array(merged_class_ids),
                data={"class_name": np.array(merged_class_names)},
            )

        for frame_path in frame_paths:
            frame = cv2.imread(frame_path)
            all_predictions = []

            # 多模型预测并收集结果
            for model in model_list:
                result = model(frame)[0]
                predictions = sv.Detections.from_ultralytics(result)
                all_predictions.append(predictions)

            # 合并预测结果
            merged_preds = merge_detections(all_predictions)
            print(merged_preds)
            # detections = sv.Detections.from_ultralytics(merged_preds)

            annotated_frame = annotator.annotate(
                scene=frame.copy(), detections=merged_preds
            )

            predict_results = predict_result_from_detections(merged_preds)

            frame_name = os.path.basename(frame_path)
            if delegate is not None:
                # 转为 PIL Image 再存入 buffer
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb_frame)
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)

                delegate.put_bytes_to_s3(
                    prefix=self.session_id,
                    file_content=buffer.read(),
                    file_name=frame_name,
                )

                keyframes.append(
                    KeyFrameInfo(
                        detections=predict_results,
                        filename=self.session_id + "/" + frame_name,
                        timestamp=self.timestamps[frame_name],
                    )
                )
            else:
                # 旧逻辑，保存到本地
                save_path = os.path.join(self.dir.results_dir, frame_name)
                cv2.imwrite(save_path, annotated_frame)
                keyframes.append(
                    KeyFrameInfo(
                        detections=predict_results,
                        filename=frame_name,
                        timestamp=self.timestamps[frame_name],
                    )
                )

        shutil.rmtree(os.path.dirname(self.dir.files_dir))  # 删除临时文件

        return VideoKeyFrames(
            frame_width=self.video_frame_width,
            frame_height=self.video_frame_height,
            duration=self.duration,
            keyframes=keyframes,
            video_path=self.video_path + "(tempfile)",
        )
