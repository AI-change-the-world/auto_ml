import opendal


def download_from_s3(op: opendal.Operator, s3_path: str, local_path: str):
    data = op.read(s3_path)
    with open(local_path, "wb") as f:
        f.write(data)
