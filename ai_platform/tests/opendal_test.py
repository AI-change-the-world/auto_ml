import os

import opendal

access_key = os.environ.get("AWS_ACCESS_KEY_ID") or "QBYnE95cE6hkYgXideUE"
secret_key = (
    os.environ.get("AWS_SECRET_ACCESS_KEY")
    or "4VWw8OyPjkPhlGwHOdvadQwjFCozuQoIGHed4DG7"
)
bucket_name = os.environ.get("AWS_BUCKET_NAME") or "predict-data-bucket"
endpoint = os.environ.get("AWS_ENDPOINT") or "http://127.0.0.1:9000"


op = opendal.Operator(
    "s3",
    endpoint=endpoint,
    access_key_id=access_key,
    secret_access_key=secret_key,
    region="us-east-1",
    bucket=bucket_name,
    root="/",
    enable_virtual_host_style="false",  # <=== 要加上！！！
)


print(len(op.read("image.png")))
