import sys

import opendal

sys.path.append(".")
import os
import uuid
from pathlib import Path
from typing import Optional

from base.file_delegate import s3_properties


def __download_from_s3(op: opendal.Operator, s3_path: str, local_path: str):
    data = op.read(s3_path)
    with open(local_path, "wb") as f:
        f.write(data)


def download_dataset_from_s3(dataset_path: str, annotation_path: str) -> Optional[str]:
    from base.file_delegate import get_operator

    print(s3_properties.datasets_bucket_name)
    op = get_operator(s3_properties.datasets_bucket_name)
    if op is None:
        return None
    if dataset_path == "" or annotation_path == "":
        return None
    # 创建临时的工作空间
    folder_name = str(uuid.uuid4())
    os.mkdir(f"./runs/{folder_name}")
    temp_dataset_path = f"./runs/{folder_name}" + os.sep + "dataset"
    temp_annotation_path = f"./runs/{folder_name}" + os.sep + "annotations"
    os.mkdir(temp_dataset_path)
    os.mkdir(temp_annotation_path)

    for i in op.list(dataset_path):
        if Path(i.path).suffix != "":
            print(i.path)
            file_name = i.path.split("/")[-1]
            __download_from_s3(op, i.path, temp_dataset_path + os.sep + file_name)

    for i in op.list(annotation_path):
        if Path(i.path).suffix != "":
            file_name = i.path.split("/")[-1]
            __download_from_s3(op, i.path, temp_annotation_path + os.sep + file_name)

    return f"./runs/{folder_name}"


print(
    download_dataset_from_s3(
        "dataset/f7f57835-5a4e-4f56-890b-b30f461cd93a/",
        "annotation/67c4d4eb-92d5-474d-a3e7-f1e62757a61c/",
    )
)
