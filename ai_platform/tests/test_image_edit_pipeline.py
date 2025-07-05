import os
from http import HTTPStatus

# dashscope sdk >= 1.23.4
from dashscope import ImageSynthesis

# 从环境变量中获取 DashScope API Key（即阿里云百炼平台 API key）
api_key = os.getenv("OPENAI_API_KEY")

# ========== 图像输入方式（二选一）==========
# 【方式一】使用公网图片 URL
# mask_image_url = "http://wanx.alicdn.com/material/20250318/description_edit_with_mask_3_mask.png"
# base_image_url = "http://wanx.alicdn.com/material/20250318/description_edit_with_mask_3.jpeg"

# 【方式二】使用本地文件路径（file://+文件路径）
# 使用绝对路径
# mask_image_url = "file://" + "/path/to/your/mask_image.png"     # Linux/macOS
# base_image_url = "file://" + "D:/github_repo/auto_ml/ai_platform/tests/ref1.png"  # Windows
# mask_image_url = "file://" + "D:/github_repo/auto_ml/ai_platform/tests/ref1.png"  # Windows
# 或使用相对路径
mask_image_url = "file://" + "./mask.png"  # 以实际路径为准
base_image_url = "file://" + "./ref1.png"  # 以实际路径为准


def sample_sync_call_imageedit():
    print("please wait...")
    rsp = ImageSynthesis.call(
        api_key=api_key,
        model="wanx2.1-imageedit",
        function="description_edit_with_mask",  # description_edit
        prompt="这是一施工工地地面缺陷图，中间有一些裂纹缺陷。去除这张图像中裂纹缺陷，添加一污渍和水渍。",
        mask_image_url=mask_image_url,
        base_image_url=base_image_url,
        n=1,
    )
    assert rsp.status_code == HTTPStatus.OK

    print("response: %s" % rsp)
    if rsp.status_code == HTTPStatus.OK:
        for result in rsp.output.results:
            print("---------------------------")
            print(result.url)
    else:
        print(
            "sync_call Failed, status_code: %s, code: %s, message: %s"
            % (rsp.status_code, rsp.code, rsp.message)
        )


if __name__ == "__main__":
    sample_sync_call_imageedit()
