# -*- coding: utf-8 -*-

import base64
import json
import os
import traceback

import cv2
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

try:
    # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
    # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性
    # 以下代码示例仅供参考，建议采用更安全的方式来使用密钥
    # 请参见：https://cloud.tencent.com/document/product/1278/85305
    # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
    cred = credential.Credential(os.getenv("TES_ID"), os.getenv("TES_KEY"))
    # 使用临时密钥示例
    # cred = credential.Credential("SecretId", "SecretKey", "Token")
    # 实例化一个http选项，可选的，没有特殊需求可以跳过
    httpProfile = HttpProfile()
    httpProfile.endpoint = "hunyuan.tencentcloudapi.com"

    # 实例化一个client选项，可选的，没有特殊需求可以跳过
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    # 实例化要请求产品的client对象,clientProfile是可选的
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", clientProfile)

    ref_image = cv2.imread("./ref.jpg")
    _, buffer = cv2.imencode(".jpg", ref_image)

    # 转为 base64 字符串
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    # 如果你需要加上头部，可加这一行：
    img_base64_with_header = f"data:image/jpeg;base64,{img_base64}"

    # 实例化一个请求对象,每个接口都会对应一个request对象
    req = models.SubmitHunyuanImageJobRequest()
    params = {
        # "Prompt": "正面90°平视视角拍摄的光伏电池组件特写，完整展示8×12块深蓝色硅片组成的矩形阵列。每块硅片表面布满不规则网状裂纹，玻璃封装层呈现清晰的蛛网式破裂纹理，裂纹边缘带有细微高光反射。背景为冷调金属质感的工业车间环境，左侧45°强侧光照射突出玻璃裂痕的立体深度，工业摄影风格，超高细节写实画质，比例3:4",
        "Prompt": "混凝土墙面表面可见一条细小竖向裂缝，宽度小于0.2毫米，裂缝浅而连续，无明显破损和掉边，整体墙面平整干净，结构完整。真实工地环境，写实风格，冷色调光照，图像比例为3:4。",
        # "NegativePrompt": None,
        # "Style": None,
        # "Resolution": None,
        # "Num": None,
        # "Clarity": None,
        "ContentImage": {"ImageUrl": None, "ImageBase64": img_base64_with_header},
        # "Revise": None,
        # "Seed": None,
        # "LogoAdd": None,
        # "LogoParam": {
        #     "LogoUrl": None,
        #     "LogoImage": None,
        #     "LogoRect": {"X": None, "Y": None, "Width": None, "Height": None},
        # },
    }
    req.from_json_string(json.dumps(params))

    # 返回的resp是一个SubmitHunyuanImageJobResponse的实例，与请求对象对应
    resp = client.SubmitHunyuanImageJob(req)
    # 输出json格式的字符串回包
    print(resp.to_json_string())

except TencentCloudSDKException as err:
    print(err)
    traceback.print_exc()
