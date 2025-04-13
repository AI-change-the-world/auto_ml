import os
from openai import OpenAI

vl_client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
