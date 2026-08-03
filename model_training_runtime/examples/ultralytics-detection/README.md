# Ultralytics Detection Example

This is the first real framework package for `model_training_runtime`. It is a
YOLO detection adapter for the existing `training-dataset-source-manifest/v1`
flow:

- media objects are read from the materialized dataset manifest;
- annotation objects are the existing plain-text YOLO records;
- `train`, `val`, and deterministic fallback splits are converted to the
  Ultralytics `images/*` and `labels/*` layout;
- the selected `.pt` model input is loaded from `context["model_input_path"]`;
- `best.pt` is retained as a custom-training initialization artifact and `last.pt` is the resumable checkpoint;
- `export_onnx=true` writes the deployable `best.onnx` artifact for the existing detection inference runtime.

The package intentionally contains no dependency file. The service image owns
the pinned Ultralytics/PyTorch dependencies and exposes the runtime id
`ultralytics-8.3.0-pytorch-2.5-cu124`.

Build the code package ZIP:

```bash
python build_package_zip.py ./dist/ultralytics-detection-1.0.0.zip
```

Package an approved base model or full training checkpoint for registration:

```bash
python build_model_package_zip.py ./weights/yolo11n.pt \
  ./dist/yolo11n-detection-model.zip \
  --classes person,car,dog
```

To make a resumable input, provide a distinct optimizer-bearing checkpoint:

```bash
python build_model_package_zip.py ./weights/best.pt \
  ./dist/yolo11n-resume-model.zip \
  --classes person,car,dog \
  --resume-checkpoint ./weights/last.pt
```

The builder only packages bytes supplied by the caller. It does not download
weights or put model files in the code package.
