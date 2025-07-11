import opendal


def download_from_s3(op: opendal.Operator, s3_path: str, local_path: str):
    data = op.read(s3_path)
    with open(local_path, "wb") as f:
        f.write(data)

def upload_to_s3(op: opendal.Operator, local_path: str, s3_path: str):
    with open(local_path, "rb") as f:
        op.write(s3_path, f.read())
