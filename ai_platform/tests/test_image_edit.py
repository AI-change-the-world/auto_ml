import base64
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os
import cv2

model = "stable-diffusion-3.5-large-turbo"
prompt = "帮我去除右下角的水印"

ref_image = cv2.imread("./ref.jpg")
_, buffer = cv2.imencode(".jpg", ref_image)

# 转为 base64 字符串
img_base64 = base64.b64encode(buffer).decode("utf-8")

# 如果你需要加上头部，可加这一行：
img_base64_with_header = f"data:image/jpeg;base64,{img_base64}"


# 同步调用
def sample_block_call():
    rsp = ImageSynthesis.call(
        model=model,
        images=[img_base64_with_header],
        api_key=os.getenv("OPENAI_API_KEY"),
        prompt=prompt,
        n=1,
    )
    if rsp.status_code == HTTPStatus.OK:
        print(rsp)
        # 保存图片到当前文件夹
        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            with open("./%s" % file_name, "wb+") as f:
                f.write(requests.get(result.url).content)
    else:
        print(
            "Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message)
        )


# 异步调用
def sample_async_call():
    rsp = ImageSynthesis.async_call(
        model=model,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        prompt=prompt,
        negative_prompt="garfield",
        n=1,
        size="512*512",
    )
    if rsp.status_code == HTTPStatus.OK:
        print(rsp)
    else:
        print(
            "Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message)
        )
    status = ImageSynthesis.fetch(rsp)
    if status.status_code == HTTPStatus.OK:
        print(status.output.task_status)
    else:
        print(
            "Failed, status_code: %s, code: %s, message: %s"
            % (status.status_code, status.code, status.message)
        )

    rsp = ImageSynthesis.wait(rsp)
    if rsp.status_code == HTTPStatus.OK:
        print(rsp)
    else:
        print(
            "Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message)
        )


if __name__ == "__main__":
    sample_block_call()
    # sample_async_call()
