import os
import shutil
import tempfile
import random

def prepare_temp_training_dir_split(
    all_images_dir: str,
    all_labels_dir: str,
    class_names: list[str],
    val_split: float = 0.2,
    tmp_root: str = "/tmp"
) -> str:
    """
    构造临时训练目录，并自动将训练集按 val_split 分成 train/val。

    Returns:
        temp_dir: 临时训练目录，包含 data.yaml
    """
    temp_dir = tempfile.mkdtemp(prefix="yolo_train_", dir=tmp_root)

    # 收集所有图像（只要有对应标签的才保留）
    all_image_files = [
        f for f in os.listdir(all_images_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png')) and
           os.path.exists(os.path.join(all_labels_dir, os.path.splitext(f)[0] + ".txt"))
    ]

    # 随机划分
    random.shuffle(all_image_files)
    val_count = int(len(all_image_files) * val_split)
    val_files = set(all_image_files[:val_count])
    train_files = set(all_image_files[val_count:])

    def copy_files(file_set, mode):
        img_dst = os.path.join(temp_dir, "images", mode)
        lbl_dst = os.path.join(temp_dir, "labels", mode)
        os.makedirs(img_dst, exist_ok=True)
        os.makedirs(lbl_dst, exist_ok=True)

        for fname in file_set:
            name = os.path.splitext(fname)[0]
            shutil.copy(os.path.join(all_images_dir, fname), os.path.join(img_dst, fname))
            shutil.copy(os.path.join(all_labels_dir, name + ".txt"), os.path.join(lbl_dst, name + ".txt"))

    copy_files(train_files, "train")
    copy_files(val_files, "val")

    # 写入 data.yaml
    data_yaml = f"""
path: {temp_dir}
train: images/train
val: images/val
nc: {len(class_names)}
names: {class_names}
"""
    with open(os.path.join(temp_dir, "data.yaml"), "w") as f:
        f.write(data_yaml)

    return temp_dir