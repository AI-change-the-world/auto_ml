import os
import random
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import download_from_s3, get_trainer_config
from utils.logger import logger


def download_dataset_from_s3(
    dataset_path: str, annotation_path: str, temp_root: str = "./runs"
) -> Optional[str]:
    """从 S3 下载数据集和标注文件"""
    cfg = get_trainer_config()

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
        op = get_s3_operator(cfg.s3.datasets_bucket_name)

        for item in op.list(dataset_path):
            if Path(item.path).suffix != "":
                file_name = Path(item.path).name
                download_from_s3(
                    item.path,
                    os.path.join(temp_dataset_path, file_name),
                    cfg.s3.datasets_bucket_name
                )

        # 下载标注文件
        for item in op.list(annotation_path):
            if Path(item.path).suffix != "":
                file_name = Path(item.path).name
                download_from_s3(
                    item.path,
                    os.path.join(temp_annotation_path, file_name),
                    cfg.s3.datasets_bucket_name
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
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
    tmp_root: str = "./runs",
) -> str:
    """
    准备目标检测训练数据集
    构造临时训练目录，自动划分验证集
    """
    temp_dir = os.path.abspath(tempfile.mkdtemp(
        prefix="yolo_det_", dir=tmp_root))

    all_image_files = [
        f for f in os.listdir(all_images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and os.path.exists(os.path.join(all_labels_dir, Path(f).stem + ".txt"))
    ]

    total = len(all_image_files)
    if total == 0:
        raise ValueError("No valid image-label pairs found.")

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
            name = Path(fname).stem
            shutil.copy(
                os.path.join(all_images_dir, fname),
                os.path.join(img_dst, fname)
            )
            shutil.copy(
                os.path.join(all_labels_dir, name + ".txt"),
                os.path.join(lbl_dst, name + ".txt")
            )

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

    return temp_dir


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
