# 1.aiohttp  2.xoscar  3.xinference --no-deps

from xinference.client import Client

client = Client("http://localhost:9997")


model_uid = client.launch_model(
    model_name="my-sd",  # 自定义名称
    model_type="stable-diffusion",
    model_path="/root/models/sd35",
)

print("Model UID:", model_uid)
