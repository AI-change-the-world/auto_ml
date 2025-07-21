import torch
import torch.onnx
from model import Generator


def export_generator_to_onnx(pth_path, onnx_path, z_dim=2048, img_channels=3):
    # 1. 创建模型并加载参数
    model = Generator(z_dim, img_channels)
    model.load_state_dict(torch.load(pth_path, map_location="cpu"))
    model.eval()

    # 2. 准备输入
    z = torch.randn(1, z_dim)  # 这里注意一定要是 (B, z_dim)

    # 3. 导出为 ONNX
    torch.onnx.export(
        model,
        z,  # 输入
        onnx_path,  # 输出路径
        export_params=True,
        opset_version=11,  # 可改成 12/13 看需求
        do_constant_folding=True,
        input_names=["z"],
        output_names=["generated_image"],
        dynamic_axes={"z": {0: "batch_size"}, "generated_image": {0: "batch_size"}},
    )

    print(f"✅ 成功导出 ONNX: {onnx_path}")


# 使用示例
if __name__ == "__main__":
    export_generator_to_onnx(
        r"D:\github_repo\auto_ml\ai_platform\gan\output\generator_1000.pth",
        "model.onnx",
    )
