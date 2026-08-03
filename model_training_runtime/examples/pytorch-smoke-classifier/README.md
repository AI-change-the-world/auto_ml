# PyTorch Smoke Classifier

This is the smallest offline custom-training test package. It uses generated
two-dimensional binary samples, so it needs neither a platform dataset nor
network access. It trains a tiny PyTorch model for five epochs by default.

Build the uploadable ZIP:

```bash
python build_package_zip.py ./dist/pytorch-smoke-classifier-1.1.0.zip
```

Upload `dist/pytorch-smoke-classifier-1.1.0.zip` from **模型管理 → 自定义模型**.
When creating the training task, select **自定义脚本训练** and set:

- Data input mode: `脚本自行准备数据`
- Class names: automatically loaded from the ZIP as `negative,positive`
- Device: `cpu`
- Script parameters: `{}`

The package writes a deployable `smoke-model.onnx` plus a resumable
`smoke-model.pt` checkpoint. The Runtime stores both in the configured S3
models bucket and registers the ONNX output in **部署** after training succeeds.
The deployment uses the `onnx_classification` inference template, so any RGB
image can be used to test the generated `negative` / `positive` classifier.
