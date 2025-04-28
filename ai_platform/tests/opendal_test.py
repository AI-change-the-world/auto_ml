import sys
sys.path.append(".")
import opendal

from base.nacos_config import load_nacos_config


def get_op(data_id="LOCAL_S3_CONFIG", group="AUTO_ML") -> opendal.Operator:
    nacos_config = load_nacos_config(data_id, group)
    cfg = nacos_config.get("local-s3-config")
    return opendal.Operator(
        "s3",
        endpoint=cfg.get("endpoint"),
        access_key_id=cfg.get("access_key"),
        secret_access_key=cfg.get("secret_key"),
        region="us-east-1",
        bucket=cfg.get("bucket_name"),
        root="/",
        enable_virtual_host_style="false",  # <=== 要加上！！！
    )

op = get_op()


print(len(op.read("image.png")))
