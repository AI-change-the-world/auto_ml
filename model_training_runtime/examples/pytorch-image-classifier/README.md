# PyTorch Cat/Dog Classifier Example

This runnable package trains a small PyTorch image classifier and exports a
deployable ONNX model plus a resumable `.pt` checkpoint. Its platform runtime
is `pytorch-2.5-cu124`, which is provided by the training runtime image; the
ZIP does not install dependencies.

For `platform_dataset`, choose an image classification dataset and annotation
project in the UI. Each annotation must contain one class ID, and its class
order is used unchanged by the ONNX model.

For `script_managed`, set class names to `cat,dog`. The package downloads the
public CIFAR-10 archive with torchvision, selects its cat and dog samples, and
trains without a platform dataset or annotation project. This requires the
platform to enable both `allow_script_managed_data: true` and outbound access
to the CIFAR-10 download host. The downloaded data exists only in the current
task workspace and is removed after the run.

Build the uploadable ZIP:

```bash
python build_package_zip.py ./dist/pytorch-image-classifier-1.0.0.zip
```

Import that ZIP from **模型管理 → 自定义模型**, then choose **自定义脚本训练** when
creating a training task. For a fast smoke test, use:

```json
{"epochs": 1, "max_samples": 128, "batch_size": 32}
```

To start from a pre-trained `.pt` weight, include it in the same ZIP (for
example `weights/initial.pt`) and load it from `train.py` using a path relative
to `__file__`. The example checks that exact optional path automatically; do
not upload it as a separate model package or add a manifest field.
