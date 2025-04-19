import base64
import os

from openai import OpenAI

img_path = "/Users/guchengxi/Desktop/projects/auto_ml/backend/datasets/coco8/images/train/000000000030.jpg"


#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# 将xxxx/test.png替换为你本地图像的绝对路径
base64_image = encode_image(img_path)

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-max-latest",
    messages=[
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI model trained to annotate images for YOLO object detection. "
                    "Analyze the given image and identify objects belonging to the following categories: 'vase' and 'flower'. "
                    "For each detected object, provide the annotation in the following structured format:\n\n"
                    "<Object Class>: (x_min, y_min, width, height)\n\n"
                    "Example Output:\n"
                    "Vase: (120, 300, 80, 150)\n"
                    "Flower: (200, 100, 150, 200)\n\n"
                    "Do not include any additional text or explanation. Only return the structured annotations.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        },
    ],
)
print(completion.choices[0].message.content)
