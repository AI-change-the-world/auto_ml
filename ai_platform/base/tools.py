import opendal

from base.logger import logger


def download_from_s3(op: opendal.Operator, s3_path: str, local_path: str):
    try:
        data = op.read(s3_path)
        with open(local_path, "wb") as f:
            f.write(data)
    except Exception as e:
        logger.error(f"Error downloading from S3: {e}")
        pass

def upload_to_s3(op: opendal.Operator, local_path: str, s3_path: str):
    try:
        with open(local_path, "rb") as f:
            op.write(s3_path, f.read())
    except Exception as e:
        logger.error(f"Error uploading from S3: {e}")
        pass
