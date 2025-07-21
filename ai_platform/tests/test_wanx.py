import os
from http import HTTPStatus
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import requests
from dashscope import ImageSynthesis

prompt = "混凝土墙面表面可见一条细小竖向裂缝，宽度小于0.2毫米，裂缝浅而连续，无明显破损和掉边，整体墙面平整干净，结构完整。真实工地环境，写实风格，冷色调光照，图像比例为3:4。"

prompt2 = "一张拍摄于建筑工地的特写照片，展示一段混凝土墙面存在轻微蜂窝麻面，表面有小范围孔洞和不均匀纹理，缺陷程度为轻微，背景为真实施工环境，冷色调自然光，工程巡检视角，高清写实风格，图像比例为3:4。"

# wanx2.1-t2i-turbo   wanx2.1-t2i-plus  stable-diffusion-3.5-large  flux-schnell


def sample_block_call(model: str):
    rsp = ImageSynthesis.call(
        model=model, prompt=prompt2, api_key=os.getenv("OPENAI_API_KEY"), size="768*512"
    )
    if rsp.status_code == HTTPStatus.OK:
        print(rsp.output)
        print(rsp.usage)
        # save file to current directory
        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            with open("./%s" % file_name, "wb+") as f:
                f.write(requests.get(result.url).content)
    else:
        print(
            "Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message)
        )


def sample_async_call(model: str):
    rsp = ImageSynthesis.async_call(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        prompt=prompt,
        # negative_prompt="garfield",
        n=1,
        size="256*256",
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
    sample_block_call("flux-schnell")
