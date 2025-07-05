from tencentcloud.common import credential
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
import base64
import os

# 1. 设置认证信息
cred = credential.Credential(os.environ["TES_ID"], os.environ["TES_KEY"])

# 2. 设置请求地址
http_profile = HttpProfile()
http_profile.endpoint = "hunyuan.tencentcloudapi.com"

client_profile = ClientProfile()
client_profile.httpProfile = http_profile

# 3. 创建混元客户端
client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", client_profile)

# 4. 构造请求参数
req = models.TextToImageLiteRequest()
req.Prompt = "正面90°平视视角拍摄的光伏电池组件特写，完整展示8×12块深蓝色硅片组成的矩形阵列。每块硅片表面布满不规则网状裂纹，玻璃封装层呈现清晰的蛛网式破裂纹理，裂纹边缘带有细微高光反射。背景为冷调金属质感的工业车间环境，左侧45°强侧光照射突出玻璃裂痕的立体深度，工业摄影风格，超高细节写实画质，比例3:4"
req.Resolution = "1024:1024"
req.LogoAdd = 0
req.Style = "401"
req.RspImgType = "base64"

# 5. 发起请求
resp = client.TextToImageLite(req)

# 6. 处理响应
image_base64 = resp.ResultImage
with open("output.png", "wb") as f:
    f.write(base64.b64decode(image_base64))

print("图片保存为 output.png")
