import hashlib
import json
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


@dataclass
class PreparedSegmentationDataset:
    root_dir: str
    images: int = 0


@dataclass
class MaterializedTrainingDataset:
    root_dir: str
    class_info: Dict[str, str]
    samples: int = 0


_MATERIALIZED_METADATA_FILE = "_manifest_meta.json"


@dataclass
class TrainingDatasetCache:
    cache_key: str
    cache_dir: str
    hit: bool
    created: bool = False


def _ensure_temp_root(temp_root: str) -> str:
    resolved = os.path.abspath(temp_root)
    os.makedirs(resolved, exist_ok=True)
    return resolved


def _copytree_replace(src: str, dst: str):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _write_materialized_metadata(root_dir: str, class_info: Dict[str, str], samples: int):
    metadata_path = os.path.join(root_dir, _MATERIALIZED_METADATA_FILE)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "class_info": class_info,
                "samples": samples,
            },
            f,
            ensure_ascii=False,
        )


def load_materialized_training_dataset(root_dir: str) -> MaterializedTrainingDataset:
    metadata_path = os.path.join(root_dir, _MATERIALIZED_METADATA_FILE)
    class_info: Dict[str, str] = {}
    samples = 0
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            raw_class_info = payload.get("class_info")
            if isinstance(raw_class_info, dict):
                class_info = {
                    str(key): str(value)
                    for key, value in raw_class_info.items()
                }
            try:
                samples = int(payload.get("samples") or 0)
            except (TypeError, ValueError):
                samples = 0
    return MaterializedTrainingDataset(
        root_dir=root_dir,
        class_info=class_info,
        samples=samples,
    )


def build_training_cache_key(
    *,
    task_type: str,
    sources: List[Dict[str, object]],
    class_names: Optional[List[str]] = None,
    label_format: Optional[str] = None,
) -> str:
    normalized_sources: list[dict[str, object]] = []
    for source in sources:
        samples = source.get("samples") or []
        sample_ids = []
        if isinstance(samples, list):
            for sample in samples:
                if isinstance(sample, dict):
                    sample_ids.append(int(sample.get("sample_item_id") or 0))
        normalized_sources.append({
            "dataset_id": int(source.get("dataset_id") or 0),
            "annotation_id": int(source.get("annotation_id") or 0),
            "source_order": int(source.get("source_order") or 0),
            "sample_ids": sorted(sample_ids),
        })

    normalized_sources.sort(
        key=lambda item: (
            int(item["source_order"]),
            int(item["dataset_id"]),
            int(item["annotation_id"]),
        )
    )
    payload = {
        "task_type": task_type,
        "label_format": (label_format or "").strip().lower(),
        "class_names": class_names or [],
        "sources": normalized_sources,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def prepare_training_cache_dir(
    cache_key: str,
    cache_root: str = "./runs/cache/datasets",
) -> TrainingDatasetCache:
    resolved_root = _ensure_temp_root(cache_root)
    cache_dir = os.path.join(resolved_root, cache_key)
    hit = os.path.isdir(cache_dir)
    return TrainingDatasetCache(
        cache_key=cache_key,
        cache_dir=cache_dir,
        hit=hit,
        created=False,
    )


def finalize_training_cache(
    *,
    cache: TrainingDatasetCache,
    source_dir: str,
):
    os.makedirs(os.path.dirname(cache.cache_dir), exist_ok=True)
    _copytree_replace(source_dir, cache.cache_dir)
    cache.hit = True
    cache.created = True


def clone_cached_dataset(
    cache_dir: str,
    *,
    prefix: str,
    tmp_root: str = "./runs",
) -> str:
    tmp_root = _ensure_temp_root(tmp_root)
    temp_dir = os.path.abspath(tempfile.mkdtemp(prefix=prefix, dir=tmp_root))
    _copytree_replace(cache_dir, temp_dir)
    return temp_dir


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


def materialize_training_manifest(
    sources: List[Dict[str, object]],
    task_type: str,
    class_names: Optional[List[str]] = None,
    temp_root: str = "./runs",
) -> MaterializedTrainingDataset:
    """Create the trainer-local dataset layout from sample/record manifest payloads."""
    if not sources:
        raise ValueError("training sources manifest is empty")

    temp_root = _ensure_temp_root(temp_root)
    root_dir = os.path.abspath(tempfile.mkdtemp(prefix=f"manifest_{task_type}_", dir=temp_root))
    images_dir = os.path.join(root_dir, "dataset")
    labels_dir = os.path.join(root_dir, "annotations")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    cfg = get_s3_config()
    class_info: Dict[str, str] = {}
    materialized_count = 0

    try:
        for source_index, source in enumerate(sources):
            source_order = int(source.get("source_order") or source_index)
            dataset_id = int(source.get("dataset_id") or 0)
            annotation_id = int(source.get("annotation_id") or 0)
            samples = source.get("samples") or []
            if not isinstance(samples, list):
                continue

            for sample in samples:
                if not isinstance(sample, dict):
                    continue
                asset = sample.get("asset") if isinstance(sample.get("asset"), dict) else {}
                annotation = sample.get("annotation") if isinstance(sample.get("annotation"), dict) else {}
                content = annotation.get("content") if isinstance(annotation, dict) else {}
                save_path = str(asset.get("save_path") or "").strip()
                if not save_path:
                    continue

                sample_id = int(sample.get("sample_item_id") or 0)
                original_name = str(asset.get("file_name") or sample.get("item_key") or f"sample_{sample_id}.jpg")
                image_name = _build_manifest_image_name(
                    source_order=source_order,
                    dataset_id=dataset_id,
                    annotation_id=annotation_id,
                    sample_id=sample_id,
                    original_name=original_name,
                )
                image_path = os.path.join(images_dir, image_name)

                if task_type == "classification":
                    class_name = _extract_class_name(content, class_names or [])
                    if class_name is None:
                        continue
                    download_from_s3(save_path, image_path, cfg.datasets_bucket_name)
                    class_info[image_name] = class_name
                else:
                    label_text = _extract_label_text(content)
                    download_from_s3(save_path, image_path, cfg.datasets_bucket_name)
                    label_path = os.path.join(labels_dir, Path(image_name).stem + ".txt")
                    with open(label_path, "w", encoding="utf-8") as f:
                        f.write(label_text)

                materialized_count += 1

        if materialized_count == 0:
            raise ValueError("No valid samples found in training manifest")
        if task_type == "classification" and not class_info:
            raise ValueError("No valid classified samples found in training manifest")

        logger.info(
            f"Materialized training manifest: task_type={task_type}, sources={len(sources)}, "
            f"samples={materialized_count}, root={root_dir}"
        )
        _write_materialized_metadata(root_dir, class_info, materialized_count)
        return MaterializedTrainingDataset(
            root_dir=root_dir,
            class_info=class_info,
            samples=materialized_count,
        )
    except Exception:
        cleanup_temp_dir(root_dir)
        raise


def _build_manifest_image_name(
    source_order: int,
    dataset_id: int,
    annotation_id: int,
    sample_id: int,
    original_name: str,
) -> str:
    path = Path(original_name)
    suffix = path.suffix or ".jpg"
    stem = _safe_file_stem(path.stem or f"sample_{sample_id}")
    return f"s{source_order}_d{dataset_id}_a{annotation_id}_i{sample_id}_{stem}{suffix}"


def _safe_file_stem(value: str) -> str:
    chars = [ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value.strip()]
    return "".join(chars).strip("._") or "sample"


def _extract_label_text(content: object) -> str:
    if isinstance(content, dict):
        value = content.get("label_text") or content.get("yolo") or content.get("content") or ""
        return str(value).strip() if value is not None else ""
    if isinstance(content, str):
        return content.strip()
    return ""


def _extract_class_name(content: object, class_names: List[str]) -> Optional[str]:
    if isinstance(content, dict):
        direct_name = content.get("class_name") or content.get("label")
        if isinstance(direct_name, str) and direct_name.strip():
            return direct_name.strip()

        class_id_value = content.get("class_id")
        class_ids_value = content.get("class_ids")
        if isinstance(class_ids_value, list) and class_ids_value:
            class_id_value = class_ids_value[0]
        if class_id_value is not None:
            return _class_name_from_id(class_id_value, class_names)

        label_text = _extract_label_text(content)
        if label_text:
            return _class_name_from_id(label_text.split()[0], class_names)

    if isinstance(content, (str, int, float)):
        return _class_name_from_id(content, class_names)
    return None


def _class_name_from_id(value: object, class_names: List[str]) -> Optional[str]:
    try:
        class_id = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None
    if class_id < 0 or class_id >= len(class_names):
        return None
    return class_names[class_id]


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
    tmp_root = _ensure_temp_root(tmp_root)
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
        image_candidates = sorted(
            f for f in os.listdir(all_images_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )
        label_candidates = sorted(
            f for f in os.listdir(all_labels_dir)
            if f.lower().endswith(".txt")
        )
        sample_images = image_candidates[:5]
        sample_labels = label_candidates[:5]
        raise ValueError(
            "No valid image-label pairs found. "
            f"images={len(image_candidates)}, labels={len(label_candidates)}, "
            f"sample_images={sample_images}, sample_labels={sample_labels}. "
            "Expected each image to have a same-stem .txt label file."
        )
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
    tmp_root = _ensure_temp_root(tmp_root)
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


def prepare_segmentation_dataset(
    all_images_dir: str,
    all_labels_dir: str,
    class_names: List[str],
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
    tmp_root: str = "./runs",
) -> PreparedSegmentationDataset:
    tmp_root = _ensure_temp_root(tmp_root)
    temp_dir = os.path.abspath(tempfile.mkdtemp(prefix="yolo_seg_", dir=tmp_root))
    all_image_files = [
        f for f in os.listdir(all_images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and os.path.exists(os.path.join(all_labels_dir, Path(f).stem + ".txt"))
    ]
    total = len(all_image_files)
    if total == 0:
        raise ValueError("No valid image-label pairs found for segmentation training")

    random.shuffle(all_image_files)
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
            stem = Path(fname).stem
            shutil.copy(
                os.path.join(all_images_dir, fname),
                os.path.join(img_dst, fname),
            )
            shutil.copy(
                os.path.join(all_labels_dir, stem + ".txt"),
                os.path.join(lbl_dst, stem + ".txt"),
            )

    copy_files(train_files, "train")
    copy_files(val_files, "val")

    with open(os.path.join(temp_dir, "data.yaml"), "w", encoding="utf-8") as f:
        f.write(f"""path: {temp_dir}
train: images/train
val: images/val
nc: {len(class_names)}
names: {class_names}
""")

    return PreparedSegmentationDataset(root_dir=temp_dir, images=total)


def cleanup_temp_dir(temp_dir: str):
    """清理临时目录"""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temp directory: {temp_dir}")
