import torch
import torch.onnx
from model import Generator


def export_to_onnx(pth_path, onnx_path, input_shape=(3, 256, 256)):
    # 1. 加载模型
    model = Generator()
    model.load_state_dict(torch.load(pth_path, map_location="cpu"))
    model.eval()

    # 2. 创建 dummy input
    dummy_input = torch.randn(1, *input_shape)  # e.g., (1, 3, 224, 224)

    # 3. 导出为 ONNX
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )

    print(f"✅ 转换成功: {onnx_path}")


# 使用示例
if __name__ == "__main__":
    export_to_onnx(
        r"D:\github_repo\auto_ml\ai_platform\augment\simple_cycle_gan\generator_A.pth",
        "model.onnx",
    )
