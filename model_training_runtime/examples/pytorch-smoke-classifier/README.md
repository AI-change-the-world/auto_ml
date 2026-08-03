# PyTorch Smoke Classifier

This is the smallest offline custom-training test package. It uses generated
two-dimensional binary samples, so it needs neither a platform dataset nor
network access. It trains a tiny PyTorch model for five epochs by default.

Build the uploadable ZIP:

```bash
python build_package_zip.py ./dist/pytorch-smoke-classifier-1.0.1.zip
```

Upload `dist/pytorch-smoke-classifier-1.0.1.zip` from **模型管理 → 自定义模型**.
When creating the training task, select **自定义脚本训练** and set:

- Data input mode: `脚本自行准备数据`
- Class names: automatically loaded from the ZIP as `negative,positive`
- Device: `cpu`
- Script parameters: `{}`

The package writes `smoke-model.pt` as a non-deployable `model` artifact. The
runtime verifies it and persists it automatically in the configured S3 models
bucket. It does not create an inference model or require ONNX.
