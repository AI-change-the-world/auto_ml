"""用于评估数据集质量，并推荐最合适的训练模型"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import cv2
from pydantic import BaseModel, Field
from tqdm import tqdm

from base.file_delegate import get_operator, s3_properties
from base.nacos_config import get_sync_db
from base.tools import download_from_s3
from db.annotation.annotation_crud import get_annotation
from db.dataset.dataset_crud import get_dataset
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate


class ObjectStatsSummary(BaseModel):
    total_objects: int
    small_objects: int
    medium_objects: int
    large_objects: int
    average_objects_per_image: float


class ImageStatsSummary(BaseModel):
    total_images: int
    annotated_images: int
    image_only: int
    label_only: int


class YoloModelRecommendation(BaseModel):
    suggested_model: str
    rationale: str
    tiling_recommended: bool
    tiling_strategy: Optional[str] = None


class DatasetAggregateAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_stats: ImageStatsSummary
    object_stats: ObjectStatsSummary
    yolo_recommendation: YoloModelRecommendation


class ObjectStat(BaseModel):
    class_id: int
    bbox_width: float
    bbox_height: float
    bbox_area: float
    bbox_area_ratio: float


class ImageAnnotationStats(BaseModel):
    image_path: str
    width: int
    height: int
    num_objects: int
    small_object_count: int
    medium_object_count: int
    large_object_count: int
    object_stats: List[ObjectStat]

    def summary(self):
        return {
            "image": self.image_path,
            "size": f"{self.width}x{self.height}",
            "total_objects": self.num_objects,
            "<1%": self.small_object_count,
            "1%-5%": self.medium_object_count,
            ">5%": self.large_object_count,
        }


# ---------------------------
# 主分析器类
# ---------------------------


class YoloDatasetAnalyzer:
    def __init__(self, dataset_id: int, annotation_id: int, task_id: int):
        self.op = get_operator(s3_properties.datasets_bucket_name)
        self.image_suffixes = [".jpg", ".jpeg", ".png"]
        self.session = get_sync_db()
        self.dataset_id = dataset_id
        self.annotation_id = annotation_id
        self.task_id = task_id

    def _prepare_dataset(self) -> str:
        tlc = TaskLogCreate(
            task_id=self.task_id, log_content="[pre-eval] preparing dataset ..."
        )
        create_log(self.session, tlc)
        # download files from s3
        dataset = get_dataset(self.session, self.dataset_id)
        if dataset is None:
            raise Exception("Dataset not found")
        annotation = get_annotation(self.session, self.annotation_id)
        if annotation is None:
            raise Exception("Annotation not found")

        # create temp dir
        folder_name = str(uuid.uuid4())
        os.mkdir(f"./runs/{folder_name}")
        temp_dataset_path = f"./runs/{folder_name}" + os.sep + "dataset"
        temp_annotation_path = f"./runs/{folder_name}" + os.sep + "annotations"
        os.mkdir(temp_dataset_path)
        os.mkdir(temp_annotation_path)

        tlc = TaskLogCreate(
            task_id=self.task_id,
            log_content="[pre-eval] downloading dataset from s3 ...",
        )
        create_log(self.session, tlc)

        for i in self.op.list(dataset.local_s3_storage_path):
            if Path(i.path).suffix != "":
                print(i.path)
                file_name = i.path.split("/")[-1]
                download_from_s3(
                    self.op, i.path, temp_dataset_path + os.sep + file_name
                )

        tlc = TaskLogCreate(
            task_id=self.task_id,
            log_content="[pre-eval] downloading annotation from s3 ...",
        )

        create_log(self.session, tlc)

        for i in self.op.list(annotation.annotation_save_path):
            if Path(i.path).suffix != "":
                file_name = i.path.split("/")[-1]
                download_from_s3(
                    self.op, i.path, temp_annotation_path + os.sep + file_name
                )

        tlc = TaskLogCreate(
            task_id=self.task_id,
            log_content="[pre-eval] dataset downloaded.",
        )

        create_log(self.session, tlc)

        self.img_dir = temp_dataset_path
        self.label_dir = temp_annotation_path

        return f"./runs/{folder_name}"

    def _collect_file_pairs(self):
        image_map = {
            p.stem: p
            for suffix in self.image_suffixes
            for p in Path(self.img_dir).glob(f"*{suffix}")
        }
        label_map = {p.stem: p for p in Path(self.label_dir).glob("*.txt")}

        common = set(image_map) & set(label_map)
        image_only = set(image_map) - common
        label_only = set(label_map) - common

        return image_map, label_map, common, image_only, label_only

    def _analyze_image_and_labels(
        self, image_path: str, label_path: str
    ) -> ImageAnnotationStats:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Cannot load image")
        h_img, w_img = img.shape[:2]

        object_stats = []
        small, medium, large = 0, 0, 0

        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                class_id, x, y, w_rel, h_rel = map(float, parts)
                w_abs = w_rel * w_img
                h_abs = h_rel * h_img
                area = w_abs * h_abs
                ratio = area / (w_img * h_img)

                if ratio < 0.01:
                    small += 1
                elif ratio < 0.05:
                    medium += 1
                else:
                    large += 1

                object_stats.append(
                    ObjectStat(
                        class_id=int(class_id),
                        bbox_width=w_abs,
                        bbox_height=h_abs,
                        bbox_area=area,
                        bbox_area_ratio=ratio,
                    )
                )

        return ImageAnnotationStats(
            image_path=image_path,
            width=w_img,
            height=h_img,
            num_objects=len(object_stats),
            small_object_count=small,
            medium_object_count=medium,
            large_object_count=large,
            object_stats=object_stats,
        )

    def aggregate_analysis_from_yolo_output(
        self,
        analysis_output: Dict[str, List],
    ) -> DatasetAggregateAnalysis:
        matched_raw = analysis_output.get("matched", [])
        image_only_raw = analysis_output.get("image_only", [])
        label_only_raw = analysis_output.get("label_only", [])

        # 1. 图像统计
        total_images = len(matched_raw) + len(image_only_raw)
        annotated_images = len(matched_raw)
        image_only = len(image_only_raw)
        label_only = len(label_only_raw)

        # 2. 目标统计
        total_objects = 0
        small = 0
        medium = 0
        large = 0

        for item in matched_raw:
            total_objects += item["num_objects"]
            small += item["small_object_count"]
            medium += item["medium_object_count"]
            large += item["large_object_count"]

        average_objects_per_image = (
            round(total_objects / annotated_images, 2) if annotated_images > 0 else 0.0
        )

        # 3. 模型推荐
        if total_objects == 0:
            model = "yolov8-n"
            rationale = "无目标数据，仅测试用途，选择最小模型。"
            tiling = False
            strategy = None
        else:
            small_ratio = small / total_objects
            large_ratio = large / total_objects

            if small_ratio > 0.4:
                model = "yolov8-l"
                rationale = "小目标占比较高，推荐使用更深层网络以提高小目标召回率。"
                tiling = True
                strategy = "建议图像滑窗或切分为 2x2 区块，重叠 25–30%"
            elif large_ratio > 0.5:
                model = "yolov8-s"
                rationale = "大目标为主，推荐轻量模型提高速度，训练时间短。"
                tiling = False
                strategy = None
            else:
                model = "yolov8-m"
                rationale = "目标大小分布均匀，推荐中型模型以平衡性能与速度。"
                tiling = True
                strategy = "可选图像切分 2x2，滑窗增强小目标覆盖"

        return DatasetAggregateAnalysis(
            image_stats=ImageStatsSummary(
                total_images=total_images,
                annotated_images=annotated_images,
                image_only=image_only,
                label_only=label_only,
            ),
            object_stats=ObjectStatsSummary(
                total_objects=total_objects,
                small_objects=small,
                medium_objects=medium,
                large_objects=large,
                average_objects_per_image=average_objects_per_image,
            ),
            yolo_recommendation=YoloModelRecommendation(
                suggested_model=model,
                rationale=rationale,
                tiling_recommended=tiling,
                tiling_strategy=strategy,
            ),
        )

    def analyze(self) -> Dict[str, List]:
        tmp_path = self._prepare_dataset()

        tlc = TaskLogCreate(task_id=self.task_id, log_content="[eval] collection pairs")

        create_log(self.session, tlc)

        (
            image_map,
            label_map,
            common,
            image_only,
            label_only,
        ) = self._collect_file_pairs()

        matched_stats = []
        image_only_stats = []
        label_only_stats = []

        for stem in tqdm(common, desc="Analyzing matched pairs"):
            try:
                stat = self._analyze_image_and_labels(
                    str(image_map[stem]), str(label_map[stem])
                )
                matched_stats.append(stat)
            except Exception as e:
                print(f"[ERROR] Failed to analyze {stem}: {e}")

        for stem in tqdm(image_only, desc="Handling image-only"):
            img = cv2.imread(str(image_map[stem]))
            if img is None:
                continue
            h, w = img.shape[:2]
            stat = ImageAnnotationStats(
                image_path=str(image_map[stem]),
                width=w,
                height=h,
                num_objects=0,
                small_object_count=0,
                medium_object_count=0,
                large_object_count=0,
                object_stats=[],
            )
            image_only_stats.append(stat)

        for stem in label_only:
            label_only_stats.append(
                {"label_path": str(label_map[stem]), "reason": "missing image"}
            )

        tlc = TaskLogCreate(task_id=self.task_id, log_content="[eval] done")

        create_log(self.session, tlc)

        tlc = TaskLogCreate(
            task_id=self.task_id, log_content="[post-eval] remove temp dir ..."
        )

        create_log(self.session, tlc)

        shutil.rmtree(tmp_path)

        res = self.aggregate_analysis_from_yolo_output(
            {
                "matched": [s.dict() for s in matched_stats],
                "image_only": [s.dict() for s in image_only_stats],
                "label_only": label_only_stats,
            }
        )

        return res
