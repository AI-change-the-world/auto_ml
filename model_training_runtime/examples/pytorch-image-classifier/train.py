"""Runnable PyTorch cat-versus-dog training package.

In ``script_managed`` mode this package downloads CIFAR-10 through torchvision
and uses only its cat and dog samples. In ``platform_dataset`` mode it trains
from the runtime-materialized image and single-label annotation files.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Callable


SCRIPT_MANAGED_CLASSES = ["cat", "dog"]


def train(context: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader

    parameters = context.get("parameters") or {}
    input_mode = context.get("input_mode")
    class_names = [str(value) for value in context["dataset"]["class_names"]]
    if input_mode == "script_managed" and class_names != SCRIPT_MANAGED_CLASSES:
        raise ValueError("script_managed CIFAR-10 mode requires class_names in this exact order: cat,dog")
    if len(class_names) < 2:
        raise ValueError("classification training requires at least two class names")

    image_size = int(parameters.get("image_size", 32))
    batch_size = int(parameters.get("batch_size", 64))
    epochs = int(parameters.get("epochs", 5))
    max_samples = int(parameters.get("max_samples", 2000))
    num_workers = int(parameters.get("num_workers", 0))
    seed = int(parameters.get("seed", 42))
    torch.manual_seed(seed)

    report(event_type="phase", phase="prepare", message="preparing image classification dataset")
    if input_mode == "script_managed":
        dataset = _cifar_cat_dog_dataset(
            Path(context["workspace"]["input_dir"]) / "script-data",
            image_size=image_size,
            max_samples=max_samples,
            seed=seed,
        )
        report(event_type="log", level="info", message=f"downloaded and selected {len(dataset)} CIFAR-10 cat/dog samples")
    else:
        dataset = _platform_dataset(
            context["dataset"],
            Path(context["workspace"]["input_dir"]),
            image_size=image_size,
            max_samples=max_samples,
        )
        report(event_type="log", level="info", message=f"prepared {len(dataset)} materialized platform samples")
    if len(dataset) < 2:
        raise ValueError("at least two labeled samples are required for training")

    device = _resolve_device(context["resources"], torch)
    model = _tiny_image_classifier(len(class_names), nn).to(device)
    _load_bundled_initial_weights(model, device, torch)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(parameters.get("learning_rate", 0.001)))
    loss_function = nn.CrossEntropyLoss()
    loader = DataLoader(dataset, batch_size=min(batch_size, len(dataset)), shuffle=True, num_workers=num_workers)

    report(event_type="phase", phase="train", message=f"training on {device} for {epochs} epochs")
    last_loss = 0.0
    last_accuracy = 0.0
    for epoch in range(epochs):
        model.train()
        correct = 0
        total = 0
        total_loss = 0.0
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = loss_function(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach().item()) * len(labels)
            correct += int((logits.argmax(dim=1) == labels).sum().item())
            total += len(labels)
        last_loss = total_loss / max(total, 1)
        last_accuracy = correct / max(total, 1)
        report(event_type="metric", split="train", epoch=epoch, metrics={"loss": last_loss, "accuracy": last_accuracy})

    output_dir = Path(context["workspace"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "training-state.pt"
    torch.save({"model_state": model.state_dict(), "class_names": class_names, "image_size": image_size}, checkpoint_path)

    report(event_type="phase", phase="export", message="exporting deployable ONNX classifier")
    model.eval()
    inference_model = nn.Sequential(model, nn.Softmax(dim=1)).to(device).eval()
    onnx_path = output_dir / "model.onnx"
    example_input = torch.zeros(1, 3, image_size, image_size, device=device)
    with torch.no_grad():
        torch.onnx.export(
            inference_model,
            example_input,
            onnx_path,
            input_names=["images"],
            output_names=["probabilities"],
            dynamic_axes={"images": {0: "batch"}, "probabilities": {0: "batch"}},
            opset_version=17,
        )

    return {
        "summary": f"PyTorch cat/dog classifier completed with {len(dataset)} samples",
        "metrics": {"train_loss": last_loss, "train_accuracy": last_accuracy},
        "artifacts": [
            {"path": "model.onnx", "role": "model", "format": "onnx", "deployable": True},
            {"path": "training-state.pt", "role": "checkpoint", "format": "pt", "deployable": False},
        ],
        "model": {
            "task_kind": "classification",
            "class_names": class_names,
            "framework": {"id": "pytorch", "version": "2.5"},
            "resume_checkpoint_path": "training-state.pt",
            "preprocessing": {"resize": [image_size, image_size], "scale": "0_1", "layout": "NCHW"},
        },
    }


def _cifar_cat_dog_dataset(root: Path, *, image_size: int, max_samples: int, seed: int):
    from torch.utils.data import Dataset
    from torchvision import datasets, transforms

    transform = transforms.Compose([transforms.Resize((image_size, image_size)), transforms.ToTensor()])
    cifar = datasets.CIFAR10(root=str(root), train=True, download=True, transform=transform)
    selected = [index for index, label in enumerate(cifar.targets) if label in {3, 5}]
    random.Random(seed).shuffle(selected)
    selected = selected[:max_samples]
    if len(selected) < 2:
        raise ValueError("CIFAR-10 did not provide enough cat/dog samples")

    class CifarCatDogDataset(Dataset):
        def __len__(self) -> int:
            return len(selected)

        def __getitem__(self, index: int):
            image, label = cifar[selected[index]]
            return image, 0 if label == 3 else 1

    return CifarCatDogDataset()


def _platform_dataset(dataset_manifest: dict[str, Any], input_dir: Path, *, image_size: int, max_samples: int):
    from torch.utils.data import Dataset
    from torchvision import transforms

    class_names = [str(value) for value in dataset_manifest["class_names"]]
    samples: list[tuple[Path, int]] = []
    for item in dataset_manifest.get("items", []):
        media_path = _workspace_file(input_dir, item.get("media_path"), "media_path")
        annotation_path = _workspace_file(input_dir, item.get("annotation_path"), "annotation_path")
        samples.append((media_path, _single_class_id(annotation_path.read_text(encoding="utf-8"), class_names)))
        if len(samples) >= max_samples:
            break
    if not samples:
        raise ValueError("platform dataset contains no readable labeled image samples")
    transform = transforms.Compose([transforms.Resize((image_size, image_size)), transforms.ToTensor()])

    class PlatformDataset(Dataset):
        def __len__(self) -> int:
            return len(samples)

        def __getitem__(self, index: int):
            from PIL import Image

            image_path, class_id = samples[index]
            with Image.open(image_path) as image:
                return transform(image.convert("RGB")), class_id

    return PlatformDataset()


def _workspace_file(input_dir: Path, relative_path: Any, label: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError(f"platform classification item requires {label}")
    input_root = input_dir.resolve()
    path = (input_root / relative_path).resolve()
    try:
        path.relative_to(input_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the runtime input directory") from exc
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {relative_path}")
    return path


def _single_class_id(raw_label: str, class_names: list[str]) -> int:
    value = raw_label.strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed else None
    if isinstance(parsed, dict):
        class_ids = parsed.get("class_ids")
        parsed = class_ids[0] if isinstance(class_ids, list) and class_ids else None
    try:
        class_id = int(parsed)
    except (TypeError, ValueError) as exc:
        raise ValueError("platform classification annotation must contain one numeric class ID") from exc
    if class_id < 0 or class_id >= len(class_names):
        raise ValueError(f"classification class ID {class_id} is outside the declared class list")
    return class_id


def _resolve_device(resources: dict[str, Any], torch):
    requested = resources.get("device", "cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable in the selected runtime")
        return torch.device("cuda:0")
    if requested != "cpu":
        raise ValueError(f"unsupported execution device: {requested}")
    return torch.device("cpu")


def _load_bundled_initial_weights(model, device, torch) -> None:
    model_path = Path(__file__).resolve().parent / "weights" / "initial.pt"
    if not model_path.is_file():
        return
    payload = torch.load(model_path, map_location=device, weights_only=False)
    state = payload.get("model_state") if isinstance(payload, dict) else payload
    if not isinstance(state, dict):
        raise ValueError("bundled initial weight is not a compatible PyTorch state dictionary")
    model.load_state_dict(state)


def _tiny_image_classifier(class_count: int, nn):
    return nn.Sequential(
        nn.Conv2d(3, 16, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(16, 32, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
        nn.Linear(32, class_count),
    )
