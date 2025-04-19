from typing import List

from label.models import ImageModel
from label.tools import encode_image


def label_img(img_path: str, classes: List[str]) -> ImageModel:
    """
    对图像进行标注
    :param img_path: 图像路径
    :param classes: 类别名称列表
    :return: ImageModel 对象
    """
    from label.client import vl_client
    from label.tools import get_prompt, result_to_label

    prompt = get_prompt(classes)
    base64_img = encode_image(img_path)

    completion = vl_client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful assistant."}],
            },
            {
                "role": "user",
                "content": [
                    prompt,
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_img}"},
                    },
                ],
            },
        ],
    )
    return result_to_label(completion.choices[0].message.content, img_path)
