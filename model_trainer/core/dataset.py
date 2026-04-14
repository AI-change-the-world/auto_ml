import os
import random
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import download_from_s3, get_s3_config
from utils.logger import logger


@dataclass
class DetectionDatasetStats:
    images: int = 0
    bbox_labels: int = 0
    obb_labels: int = 0
    converted_to_bbox: int = 0
    converted_to_obb: int = 0


@dataclass
class PreparedDetectionDataset:
    root_dir: str
    label_format: str
    stats: DetectionDatasetStats


def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _infer_detection_label_format(
    label_format: str = "auto",
    model_name: Optional[str] = None,
) -> str:
    normalized = (label_format or "auto").strip().lower()
    if normalized in {"bbox", "detect", "detection"}:
        return "bbox"
    if normalized == "obb":
        return "obb"
    if normalized != "auto":
        raise ValueError(
            f"Unsupported detection label_format '{label_format}'. Expected one of: auto, bbox, obb."
        )

    model_stem = Path(model_name or "").stem.lower()
    return "obb" if "obb" in model_stem else "bbox"


def _bbox_to_obb(values: List[float]) -> List[float]:
    x_center, y_center, width, height = values
    half_w = width / 2
    half_h = height / 2
    x1 = _clamp01(x_center - half_w)
    y1 = _clamp01(y_center - half_h)
    x2 = _clamp01(x_center + half_w)
    y2 = _clamp01(y_center - half_h)
    x3 = _clamp01(x_center + half_w)
    y3 = _clamp01(y_center + half_h)
    x4 = _clamp01(x_center - half_w)
    y4 = _clamp01(y_center + half_h)
    return [x1, y1, x2, y2, x3, y3, x4, y4]


def _obb_to_bbox(values: List[float]) -> List[float]:
    xs = values[0::2]
    ys = values[1::2]
    min_x = _clamp01(min(xs))
    max_x = _clamp01(max(xs))
    min_y = _clamp01(min(ys))
    max_y = _clamp01(max(ys))
    width = max(max_x - min_x, 0.0)
    height = max(max_y - min_y, 0.0)
    x_center = min_x + width / 2
    y_center = min_y + height / 2
    return [
        _clamp01(x_center),
        _clamp01(y_center),
        _clamp01(width),
        _clamp01(height),
    ]


def _normalize_detection_label_file(
    source_path: str,
    target_path: str,
    output_format: str,
    stats: DetectionDatasetStats,
    count_stats: bool = True,
):
    normalized_lines: List[str] = []

    with open(source_path, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 5:
                raise ValueError(
                    f"Invalid label line in {source_path}:{line_no}. Expected 5 or 9 columns, got {len(parts)}."
                )

            class_id = int(float(parts[0]))
            values = [float(v) for v in parts[1:]]

            if len(values) == 4:
                if count_stats:
                    stats.bbox_labels += 1
                output_values = values if output_format == "bbox" else _bbox_to_obb(values)
                if count_stats and output_format == "obb":
                    stats.converted_to_obb += 1
            elif len(values) == 8:
                if count_stats:
                    stats.obb_labels += 1
                output_values = values if output_format == "obb" else _obb_to_bbox(values)
                if count_stats and output_format == "bbox":
                    stats.converted_to_bbox += 1
            else:
                raise ValueError(
                    f"Unsupported detection label format in {source_path}:{line_no}. "
                    f"Only BBox(5 cols) and OBB(9 cols) are supported."
                )

            normalized_lines.append(
                " ".join([str(class_id), *[f"{_clamp01(v):.6f}" for v in output_values]])
            )

    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(normalized_lines))


def download_dataset_from_s3(
    dataset_path: str, annotation_path: str, temp_root: str = "./runs"
) -> Optional[str]:
    """从 S3 下载数据集和标注文件"""
    cfg = get_s3_config()

    if not dataset_path or not annotation_path:
        return None

    import uuid
    folder_name = str(uuid.uuid4())
    temp_folder = os.path.join(temp_root, folder_name)
    os.makedirs(temp_folder, exist_ok=True)

    temp_dataset_path = os.path.join(temp_folder, "dataset")
    temp_annotation_path = os.path.join(temp_folder, "annotations")
    os.makedirs(temp_dataset_path, exist_ok=True)
    os.makedirs(temp_annotation_path, exist_ok=True)

    try:
        # 下载数据集
        from utils.config import get_s3_operator
        op = get_s3_operator(cfg.datasets_bucket_name)

        for item in op.list(dataset_path):
            if Path(item.path).suffix != "":
                file_name = Path(item.path).name
                download_from_s3(
                    item.path,
                    os.path.join(temp_dataset_path, file_name),
                    cfg.datasets_bucket_name
                )

        # 下载标注文件
        for item in op.list(annotation_path):
            if Path(item.path).suffix != "":
                file_name = Path(item.path).name
                download_from_s3(
                    item.path,
                    os.path.join(temp_annotation_path, file_name),
                    cfg.datasets_bucket_name
                )

        return temp_folder
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        # 清理临时目录
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        raise


def prepare_detection_dataset(
    all_images_dir: str,
    all_labels_dir: str,
    class_names: List[str],
    label_format: str = "auto",
    model_name: Optional[str] = None,
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
    tmp_root: str = "./runs",
) -> PreparedDetectionDataset:
    """
    准备目标检测训练数据集
    构造临时训练目录，自动划分验证集
    """
    temp_dir = os.path.abspath(tempfile.mkdtemp(prefix="yolo_det_", dir=tmp_root))
    resolved_label_format = _infer_detection_label_format(label_format, model_name)
    stats = DetectionDatasetStats()

    all_image_files = [
        f for f in os.listdir(all_images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and os.path.exists(os.path.join(all_labels_dir, Path(f).stem + ".txt"))
    ]

    total = len(all_image_files)
    if total == 0:
        raise ValueError("No valid image-label pairs found.")
    stats.images = total

    random.shuffle(all_image_files)
    counted_label_sources = set()

    if total >= min_total and val_split > 0:
        val_count = max(int(total * val_split), min_val)
        val_count = min(val_count, total - 1)
        val_files = set(all_image_files[:val_count])
        train_files = set(all_image_files[val_count:])
    else:
        train_files = set(all_image_files)
        val_files = set(all_image_files)

    def copy_files(file_set, mode):
        img_dst = os.path.join(temp_dir, "images", mode)
        lbl_dst = os.path.join(temp_dir, "labels", mode)
        os.makedirs(img_dst, exist_ok=True)
        os.makedirs(lbl_dst, exist_ok=True)

        for fname in file_set:
            name = Path(fname).stem
            source_label_path = os.path.join(all_labels_dir, name + ".txt")
            shutil.copy(
                os.path.join(all_images_dir, fname),
                os.path.join(img_dst, fname)
            )
            _normalize_detection_label_file(
                source_path=source_label_path,
                target_path=os.path.join(lbl_dst, name + ".txt"),
                output_format=resolved_label_format,
                stats=stats,
                count_stats=source_label_path not in counted_label_sources,
            )
            counted_label_sources.add(source_label_path)

    copy_files(train_files, "train")
    copy_files(val_files, "val")

    # 创建 data.yaml
    with open(os.path.join(temp_dir, "data.yaml"), "w") as f:
        f.write(f"""path: {temp_dir}
train: images/train
val: images/val
nc: {len(class_names)}
names: {class_names}
""")

    return PreparedDetectionDataset(
        root_dir=temp_dir,
        label_format=resolved_label_format,
        stats=stats,
    )


def prepare_classification_dataset(
    all_images_dir: str,
    class_info: Dict[str, str],
    tmp_root: str = "./runs",
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
) -> str:
    """
    准备分类训练数据集
    格式: temp_dir/train/class_x/*.jpg 和 temp_dir/val/class_x/*.jpg
    """
    temp_dir = os.path.abspath(tempfile.mkdtemp(
        prefix="yolo_cls_", dir=tmp_root))

    all_image_files = [
        f for f in os.listdir(all_images_dir)
        if f in class_info and f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not all_image_files:
        raise ValueError("No valid image files found matching class_info.")

    random.shuffle(all_image_files)
    total = len(all_image_files)

    if total >= min_total and val_split > 0:
        val_count = max(int(total * val_split), min_val)
        val_count = min(val_count, total - 1)
        val_files = set(all_image_files[:val_count])
        train_files = set(all_image_files[val_count:])
    else:
        train_files = set(all_image_files)
        val_files = set(all_image_files)

    def copy_cls_images(file_set, mode):
        for fname in file_set:
            class_name = class_info[fname]
            src_path = os.path.join(all_images_dir, fname)
            dst_dir = os.path.join(temp_dir, mode, class_name)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy(src_path, os.path.join(dst_dir, fname))

    copy_cls_images(train_files, "train")
    copy_cls_images(val_files, "val")

    return temp_dir


def cleanup_temp_dir(temp_dir: str):
    """清理临时目录"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temp directory: {temp_dir}")
