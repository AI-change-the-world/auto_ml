import os
import random
import shutil
import tempfile
from typing import Dict

from base.logger import logger

__basic_path = "./runs/"


def prepare_temp_training_dir_split(
    all_images_dir: str,
    all_labels_dir: str,
    class_names: list[str],
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
    tmp_root: str = __basic_path,
) -> str:
    """
    构造临时训练目录，自动划分验证集；样本太少时，val 复制 train。
    """
    # temp_dir = tempfile.mkdtemp(prefix="yolo_train_", dir=tmp_root)
    temp_dir = os.path.abspath(tempfile.mkdtemp(prefix="yolo_train_", dir=tmp_root))

    all_image_files = [
        f
        for f in os.listdir(all_images_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and os.path.exists(
            os.path.join(all_labels_dir, os.path.splitext(f)[0] + ".txt")
        )
    ]

    total = len(all_image_files)
    if total == 0:
        raise ValueError("No valid image-label pairs found.")

    random.shuffle(all_image_files)

    if total >= min_total and val_split > 0:
        val_count = max(int(total * val_split), min_val)
        val_count = min(val_count, total - 1)  # 至少保留一张训练
        val_files = set(all_image_files[:val_count])
        train_files = set(all_image_files[val_count:])
    else:
        train_files = set(all_image_files)
        val_files = set(all_image_files)  # val = train 复制一份

    def copy_files(file_set, mode):
        img_dst = os.path.join(temp_dir, "images", mode)
        lbl_dst = os.path.join(temp_dir, "labels", mode)
        os.makedirs(img_dst, exist_ok=True)
        os.makedirs(lbl_dst, exist_ok=True)

        for fname in file_set:
            name = os.path.splitext(fname)[0]
            shutil.copy(
                os.path.join(all_images_dir, fname), os.path.join(img_dst, fname)
            )
            shutil.copy(
                os.path.join(all_labels_dir, name + ".txt"),
                os.path.join(lbl_dst, name + ".txt"),
            )

    copy_files(train_files, "train")
    copy_files(val_files, "val")

    with open(os.path.join(temp_dir, "data.yaml"), "w") as f:
        f.write(
            f"""
path: {temp_dir}
train: images/train
val: images/val
nc: {len(class_names)}
names: {class_names}
"""
        )

    return temp_dir


def prepare_dataset_for_cls(
    all_images_dir: str,
    class_info: Dict[str, str],
    tmp_root: str = __basic_path,
    val_split: float = 0.2,
    min_total: int = 10,
    min_val: int = 1,
) -> str:
    """
    构造分类任务所需的临时训练目录。
    - 自动划分 train/val
    - 格式为：temp_dir/train/class_x/*.jpg 和 temp_dir/val/class_x/*.jpg
    """
    temp_dir = os.path.abspath(tempfile.mkdtemp(prefix="yolo_cls_", dir=tmp_root))
    logger.info(f"class_info: {class_info}")
    logger.info(f"all_images_dir images: {all_images_dir}")

    all_image_files = [
        f
        for f in os.listdir(all_images_dir)
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
        val_files = set(all_image_files)  # 复制一份作为 val

    # 获取类别名列表并编码
    class_names = sorted(set(class_info.values()))
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}

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
